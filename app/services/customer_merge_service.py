from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.database.catalog_models import Estimate
from app.database.customer_communication_models import (
    CommunicationConversation,
    CustomerCommunication,
)
from app.database.customer_models import (
    Customer,
    CustomerContact,
    CustomerLocation,
    CustomerRelationship,
    CustomerService as CustomerServiceRecord,
    ExternalRecordLink,
    PlumeCustomerNetwork,
)
from app.database.job_models import Job
from app.database.ticket_models import Ticket
from app.security.context import SecurityContext


@dataclass(frozen=True, slots=True)
class CustomerMergePreview:
    source: Customer
    target: Customer | None
    counts: dict[str, int]
    conflicts: tuple[str, ...]

    @property
    def total_dependencies(self) -> int:
        return sum(self.counts.values())

    @property
    def can_delete(self) -> bool:
        # Contacts, locations, and locally-owned services are part of the customer
        # record and are safely removed by the existing ON DELETE CASCADE rules.
        # External links and operational/account history must be preserved.
        blocking_labels = {
            "External links",
            "Plume networks",
            "Tickets",
            "Jobs",
            "Estimates",
            "Communications",
            "Conversations",
            "Customer relationships",
            "Bill-to references",
        }
        return not any(self.counts.get(label, 0) for label in blocking_labels)

    @property
    def delete_blockers(self) -> dict[str, int]:
        allowed_owned_records = {"Contacts", "Locations", "Services"}
        return {
            label: count
            for label, count in self.counts.items()
            if label not in allowed_owned_records and count
        }

    @property
    def can_merge(self) -> bool:
        return self.target is not None and not self.conflicts


@dataclass(slots=True)
class CustomerMergeService:
    db: Session
    context: SecurityContext

    def _require_staff(self) -> None:
        if not self.context.is_staff:
            raise PermissionError("Customer merge and deletion are restricted to NTInet staff.")

    def _customer(self, customer_id: int) -> Customer:
        customer = self.db.get(Customer, int(customer_id))
        if customer is None:
            raise ValueError("NOP customer not found.")
        return customer

    def candidates(self, source_id: int, *, limit: int = 2000) -> list[Customer]:
        self._require_staff()
        return list(self.db.scalars(
            select(Customer)
            .where(Customer.id != int(source_id))
            .order_by(Customer.name.asc(), Customer.customer_number.asc())
            .limit(limit)
        ))

    def preview(self, source_id: int, target_id: int | None = None) -> CustomerMergePreview:
        self._require_staff()
        source = self._customer(source_id)
        target = self._customer(target_id) if target_id is not None else None
        if target is not None and target.id == source.id:
            raise ValueError("Choose a different customer to keep.")

        counts = {
            "Contacts": self._count(CustomerContact, CustomerContact.customer_id, source.id),
            "Locations": self._count(CustomerLocation, CustomerLocation.customer_id, source.id),
            "Services": self._count(CustomerServiceRecord, CustomerServiceRecord.customer_id, source.id),
            "External links": self._count(ExternalRecordLink, ExternalRecordLink.customer_id, source.id),
            "Plume networks": self._count(PlumeCustomerNetwork, PlumeCustomerNetwork.customer_id, source.id),
            "Tickets": self._count(Ticket, Ticket.customer_id, source.id),
            "Jobs": self._count(Job, Job.customer_id, source.id),
            "Estimates": self._count(Estimate, Estimate.customer_id, source.id),
            "Communications": self._count(CustomerCommunication, CustomerCommunication.customer_id, source.id),
            "Conversations": self._count(CommunicationConversation, CommunicationConversation.customer_id, source.id),
            "Customer relationships": self._relationship_count(source.id),
            "Bill-to references": self._count(Customer, Customer.bill_to_customer_id, source.id),
        }
        conflicts: list[str] = []
        if target is not None:
            source_links = {
                (link.system_name.lower(), link.record_type.lower()): link
                for link in source.external_links
            }
            target_links = {
                (link.system_name.lower(), link.record_type.lower()): link
                for link in target.external_links
            }
            for key in sorted(source_links.keys() & target_links.keys()):
                left, right = source_links[key], target_links[key]
                conflicts.append(
                    f"Both customers have a {left.system_name} {left.record_type} link "
                    f"({left.external_id} and {right.external_id})."
                )
            if source.plume_network is not None and target.plume_network is not None:
                conflicts.append("Both customers have a Plume network.")
        return CustomerMergePreview(source, target, counts, tuple(conflicts))

    def merge(self, source_id: int, target_id: int) -> dict[str, int]:
        preview = self.preview(source_id, target_id)
        if not preview.can_merge:
            raise ValueError("Resolve the listed conflicts before merging these customers.")
        source, target = preview.source, preview.target
        assert target is not None

        # Preserve only one primary marker while retaining every contact/location.
        if target.primary_contact is not None:
            self.db.execute(update(CustomerContact).where(
                CustomerContact.customer_id == source.id,
                CustomerContact.is_primary.is_(True),
            ).values(is_primary=False))
        if target.primary_location is not None:
            self.db.execute(update(CustomerLocation).where(
                CustomerLocation.customer_id == source.id,
                CustomerLocation.is_primary.is_(True),
            ).values(is_primary=False))

        for model, column in (
            (CustomerContact, CustomerContact.customer_id),
            (CustomerLocation, CustomerLocation.customer_id),
            (CustomerServiceRecord, CustomerServiceRecord.customer_id),
            (ExternalRecordLink, ExternalRecordLink.customer_id),
            (PlumeCustomerNetwork, PlumeCustomerNetwork.customer_id),
            (Ticket, Ticket.customer_id),
            (Job, Job.customer_id),
            (Estimate, Estimate.customer_id),
            (CustomerCommunication, CustomerCommunication.customer_id),
            (CommunicationConversation, CommunicationConversation.customer_id),
        ):
            self.db.execute(update(model).where(column == source.id).values({column.key: target.id}))

        inherited_bill_to_id = source.bill_to_customer_id
        self.db.execute(update(Customer).where(Customer.bill_to_customer_id == source.id).values(
            bill_to_customer_id=target.id
        ))
        # A destination that billed to the duplicate must not become self-billing via
        # a circular FK. Otherwise inherit a useful bill-to assignment from source.
        if target.bill_to_customer_id == target.id:
            target.bill_to_customer_id = None
        if target.bill_to_customer_id is None and inherited_bill_to_id not in (None, source.id, target.id):
            target.bill_to_customer_id = inherited_bill_to_id
        self._merge_relationships(source.id, target.id)

        target.updated_by_user_id = self.context.user_id
        # Use a direct row delete after re-parenting. ORM delete-orphan cascades can
        # otherwise act on relationship collections loaded before the bulk updates
        # and try to delete records that have just been moved to the destination.
        self.db.execute(delete(Customer).where(Customer.id == source.id))
        self.db.flush()
        return preview.counts

    def delete_unused(self, customer_id: int) -> Customer:
        preview = self.preview(customer_id)
        if not preview.can_delete:
            blockers = ", ".join(
                f"{label}: {count}" for label, count in preview.delete_blockers.items()
            )
            raise ValueError(
                "This customer has records that must be preserved before deletion"
                + (f" ({blockers})." if blockers else ".")
                + " Merge it into another customer instead."
            )
        source = preview.source
        # These are customer-owned records and are intentionally removed with an
        # unused NOP-only customer. Delete explicitly so this also works on SQLite
        # development databases where FK cascade enforcement may be disabled.
        self.db.execute(delete(CustomerServiceRecord).where(CustomerServiceRecord.customer_id == source.id))
        self.db.execute(delete(CustomerLocation).where(CustomerLocation.customer_id == source.id))
        self.db.execute(delete(CustomerContact).where(CustomerContact.customer_id == source.id))
        self.db.execute(delete(Customer).where(Customer.id == source.id))
        self.db.flush()
        return source

    def _count(self, model, column, customer_id: int) -> int:
        return int(self.db.scalar(select(func.count()).select_from(model).where(column == customer_id)) or 0)

    def _relationship_count(self, customer_id: int) -> int:
        return int(self.db.scalar(
            select(func.count()).select_from(CustomerRelationship).where(
                (CustomerRelationship.source_customer_id == customer_id)
                | (CustomerRelationship.target_customer_id == customer_id)
            )
        ) or 0)

    def _merge_relationships(self, source_id: int, target_id: int) -> None:
        relationships = list(self.db.scalars(select(CustomerRelationship).where(
            (CustomerRelationship.source_customer_id == source_id)
            | (CustomerRelationship.target_customer_id == source_id)
        )))
        for relationship in relationships:
            new_source = target_id if relationship.source_customer_id == source_id else relationship.source_customer_id
            new_target = target_id if relationship.target_customer_id == source_id else relationship.target_customer_id
            if new_source == new_target:
                self.db.delete(relationship)
                continue
            existing = self.db.scalar(select(CustomerRelationship.id).where(
                CustomerRelationship.id != relationship.id,
                CustomerRelationship.source_customer_id == new_source,
                CustomerRelationship.target_customer_id == new_target,
                CustomerRelationship.relationship_type == relationship.relationship_type,
            ))
            if existing is not None:
                self.db.delete(relationship)
            else:
                relationship.source_customer_id = new_source
                relationship.target_customer_id = new_target
