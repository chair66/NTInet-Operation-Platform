from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, lazyload, selectinload

from app.database.customer_models import (
    Customer,
    CustomerContact,
    CustomerLocation,
    CustomerService,
    ExternalRecordLink,
)
from app.database.models import NotificationEvent, Organization, User
from app.database.ticket_models import Ticket, TicketEntry
from app.security.context import SecurityContext
from app.services.ticket_service import SLA_HOURS, TICKET_PRIORITIES, TICKET_TYPES


@dataclass(slots=True)
class PartnerPortalService:
    db: Session
    context: SecurityContext

    def _require_partner(self) -> None:
        if not (self.context.is_support_partner and self.context.can("partner_portal.access")):
            raise PermissionError("Third-party support portal access is required.")

    def _ticket_scope(self):
        self._require_partner()
        return (
            select(Ticket)
            .join(User, Ticket.created_by_user_id == User.id)
            .join(Customer, Ticket.customer_id == Customer.id)
            .where(
                User.organization_id == self.context.organization_id,
                Ticket.source == "third_party_portal",
            )
        )

    def list_tickets(self, *, status: str = "", query: str = "", limit: int = 250) -> list[Ticket]:
        statement = self._ticket_scope().options(
            lazyload("*"), joinedload(Ticket.customer), joinedload(Ticket.contact),
            joinedload(Ticket.location), joinedload(Ticket.assigned_user),
        )
        if status:
            statement = statement.where(Ticket.status == status)
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.where(or_(
                func.lower(Ticket.ticket_number).like(term),
                func.lower(Ticket.subject).like(term),
                func.lower(Customer.name).like(term),
            ))
        return list(self.db.scalars(statement.order_by(Ticket.updated_at.desc()).limit(limit)).unique())

    def current_tickets(self, limit: int = 100) -> list[Ticket]:
        statement = self._ticket_scope().options(
            lazyload("*"), joinedload(Ticket.customer), joinedload(Ticket.contact),
            joinedload(Ticket.location), joinedload(Ticket.assigned_user),
        ).where(Ticket.status.not_in({"resolved", "closed"}))
        return list(self.db.scalars(
            statement.order_by(Ticket.updated_at.desc()).limit(limit)
        ).unique())

    def recent_tickets(self, limit: int = 12) -> list[Ticket]:
        statement = self._ticket_scope().options(
            lazyload("*"), joinedload(Ticket.customer), joinedload(Ticket.contact),
            joinedload(Ticket.location), joinedload(Ticket.assigned_user),
        ).where(Ticket.status.in_({"resolved", "closed"}))
        return list(self.db.scalars(
            statement.order_by(Ticket.updated_at.desc()).limit(limit)
        ).unique())

    def customer_tickets(self, customer_id: int, *, closed: bool = False,
                         limit: int = 12) -> list[Ticket]:
        statement = self._ticket_scope().options(
            lazyload("*"), joinedload(Ticket.customer), joinedload(Ticket.contact),
            joinedload(Ticket.location), joinedload(Ticket.assigned_user),
        ).where(Ticket.customer_id == customer_id)
        if closed:
            statement = statement.where(Ticket.status.in_({"resolved", "closed"}))
        else:
            statement = statement.where(Ticket.status.not_in({"resolved", "closed"}))
        return list(self.db.scalars(
            statement.order_by(Ticket.updated_at.desc()).limit(limit)
        ).unique())

    def customer_profile(self, customer_id: int) -> dict[str, object] | None:
        self._require_partner()
        customer = self.db.scalar(
            select(Customer).where(
                Customer.id == customer_id, Customer.status == "active",
            ).options(
                lazyload("*"), selectinload(Customer.contacts),
                selectinload(Customer.locations), selectinload(Customer.external_links),
            )
        )
        if customer is None:
            return None
        platypus = customer.platypus_link
        primary_contact = customer.primary_contact or next(
            (item for item in customer.contacts if item.active), None
        )
        primary_location = customer.primary_location or next(
            (item for item in customer.locations if item.active), None
        )
        return {
            "id": customer.id, "number": customer.customer_number, "name": customer.name,
            "platypus_account": (
                platypus.external_account_number or platypus.external_id if platypus else ""
            ),
            "email": primary_contact.email if primary_contact else customer.billing_email,
            "phone": ((primary_contact.mobile_phone or primary_contact.office_phone)
                      if primary_contact else customer.billing_phone),
            "address": ", ".join(filter(None, (
                primary_location.address_line_1 if primary_location else "",
                primary_location.city if primary_location else "",
                primary_location.state if primary_location else "",
                primary_location.postal_code if primary_location else "",
            ))),
        }

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        statement = self._ticket_scope().options(
            lazyload("*"), joinedload(Ticket.customer), joinedload(Ticket.contact),
            joinedload(Ticket.location), joinedload(Ticket.service), joinedload(Ticket.assigned_user),
            selectinload(Ticket.entries).joinedload(TicketEntry.author),
            selectinload(Ticket.attachments),
        ).where(Ticket.id == ticket_id)
        return self.db.scalar(statement)

    def search_customers(self, query: str, limit: int = 15) -> list[dict[str, object]]:
        self._require_partner()
        query = query.strip()
        if len(query) < 2:
            return []
        term = f"%{query.lower()}%"
        digits = "".join(character for character in query if character.isdigit())

        def phone_digits(column):
            value = column
            for character in ("(", ")", "-", " ", "+", "."):
                value = func.replace(value, character, "")
            return value

        matches = [
            func.lower(Customer.name).like(term),
            func.lower(Customer.customer_number).like(term),
            func.lower(Customer.billing_email).like(term),
            func.lower(Customer.billing_phone).like(term),
            func.lower(CustomerContact.email).like(term),
            func.lower(CustomerContact.office_phone).like(term),
            func.lower(CustomerContact.mobile_phone).like(term),
            func.lower(CustomerLocation.address_line_1).like(term),
            func.lower(CustomerLocation.address_line_2).like(term),
            func.lower(CustomerLocation.city).like(term),
            func.lower(CustomerLocation.state).like(term),
            func.lower(CustomerLocation.postal_code).like(term),
            func.lower(ExternalRecordLink.external_account_number).like(term),
            func.lower(ExternalRecordLink.external_id).like(term),
        ]
        if len(digits) >= 4:
            digit_term = f"%{digits}%"
            matches.extend((
                phone_digits(Customer.billing_phone).like(digit_term),
                phone_digits(CustomerContact.office_phone).like(digit_term),
                phone_digits(CustomerContact.mobile_phone).like(digit_term),
            ))
        statement = (
            select(Customer)
            .outerjoin(CustomerContact, CustomerContact.customer_id == Customer.id)
            .outerjoin(CustomerLocation, CustomerLocation.customer_id == Customer.id)
            .outerjoin(
                ExternalRecordLink,
                (ExternalRecordLink.customer_id == Customer.id)
                & (func.lower(ExternalRecordLink.system_name) == "platypus")
                & (func.lower(ExternalRecordLink.record_type) == "customer"),
            )
            .where(
                Customer.status == "active",
                or_(*matches),
            )
            .options(
                lazyload("*"), selectinload(Customer.contacts),
                selectinload(Customer.locations), selectinload(Customer.external_links),
            )
            .order_by(Customer.name)
            .limit(max(1, min(limit, 25)))
        )
        customers = list(self.db.scalars(statement).unique())
        results = []
        for customer in customers:
            platypus = customer.platypus_link
            primary_contact = customer.primary_contact or next(
                (item for item in customer.contacts if item.active), None
            )
            primary_location = customer.primary_location or next(
                (item for item in customer.locations if item.active), None
            )
            results.append({
                "id": customer.id, "number": customer.customer_number,
                "name": customer.name,
                "platypus_account": (
                    platypus.external_account_number or platypus.external_id
                    if platypus else ""
                ),
                "email": primary_contact.email if primary_contact else customer.billing_email,
                "phone": ((primary_contact.mobile_phone or primary_contact.office_phone)
                          if primary_contact else customer.billing_phone),
                "address": ", ".join(filter(None, (
                    primary_location.address_line_1 if primary_location else "",
                    primary_location.city if primary_location else "",
                    primary_location.state if primary_location else "",
                    primary_location.postal_code if primary_location else "",
                ))),
                "locations": [{"city": location.city, "state": location.state}
                              for location in customer.locations[:2]],
            })
        return results

    def customer_options(self, customer_id: int) -> dict[str, object] | None:
        self._require_partner()
        customer = self.db.scalar(
            select(Customer).where(Customer.id == customer_id, Customer.status == "active").options(
                lazyload("*"), selectinload(Customer.contacts),
                selectinload(Customer.locations), selectinload(Customer.services),
                selectinload(Customer.external_links),
            )
        )
        if customer is None:
            return None
        primary_contact = customer.primary_contact or next(
            (item for item in customer.contacts if item.active), None
        )
        primary_location = customer.primary_location or next(
            (item for item in customer.locations if item.active), None
        )
        platypus_snapshot = {}
        if customer.platypus_link:
            try:
                platypus_snapshot = json.loads(customer.platypus_link.source_snapshot_json or "{}")
            except (TypeError, json.JSONDecodeError):
                platypus_snapshot = {}
        billing = platypus_snapshot.get("billing", {})
        if not isinstance(billing, dict):
            billing = {}
        billing_address = ", ".join(filter(None, (
            billing.get("address_line_1", ""), billing.get("address_line_2", ""),
            billing.get("city", ""), billing.get("state", ""), billing.get("postal_code", ""),
        )))
        primary_service_address = primary_location.one_line_address if primary_location else ""
        normalize_address = lambda value: "".join(
            character.lower() for character in value if character.isalnum()
        )
        return {
            "id": customer.id, "number": customer.customer_number, "name": customer.name,
            "contacts": [{"id": item.id, "name": item.full_name, "email": item.email,
                          "office": item.office_phone, "mobile": item.mobile_phone,
                          "primary": item.is_primary}
                         for item in customer.contacts if item.active],
            "locations": [{"id": item.id, "name": item.name,
                           "address": item.one_line_address, "primary": item.is_primary}
                          for item in customer.locations if item.active],
            "services": [{"id": item.id, "name": item.service_name, "location_id": item.location_id} for item in customer.services if item.status == "active"],
            "billing_contact": {
                "name": billing.get("contact_name") or (primary_contact.full_name if primary_contact else ""),
                "email": billing.get("email") or customer.billing_email or (primary_contact.email if primary_contact else ""),
                "phone": billing.get("phone") or customer.billing_phone or (
                    (primary_contact.office_phone or primary_contact.mobile_phone) if primary_contact else ""
                ),
                "address": billing_address,
                "address_differs": bool(
                    billing_address and primary_service_address
                    and normalize_address(billing_address) != normalize_address(primary_service_address)
                ),
            },
            "primary_service_location": {
                "id": primary_location.id if primary_location else None,
                "name": primary_location.name if primary_location else "",
                "address": primary_service_address,
            },
        }

    def create_ticket(self, *, customer_id: int, contact_id: int | None, location_id: int | None,
                      service_id: int | None, subject: str, description: str,
                      ticket_type: str, priority: str) -> Ticket:
        self._require_partner()
        options = self.customer_options(customer_id)
        if options is None:
            raise ValueError("Customer not found.")
        if contact_id and contact_id not in {item["id"] for item in options["contacts"]}:
            raise ValueError("The selected contact does not belong to this customer.")
        if location_id and location_id not in {item["id"] for item in options["locations"]}:
            raise ValueError("The selected location does not belong to this customer.")
        if service_id and service_id not in {item["id"] for item in options["services"]}:
            raise ValueError("The selected service does not belong to this customer.")
        subject, description = subject.strip(), description.strip()
        if not subject or not description:
            raise ValueError("Subject and problem description are required.")
        if ticket_type not in TICKET_TYPES or priority not in TICKET_PRIORITIES:
            raise ValueError("Invalid ticket type or priority.")
        customer = self.db.get(Customer, customer_id)
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            ticket_number=f"PENDING-{self.context.user_id}-{int(now.timestamp())}",
            customer_id=customer_id, contact_id=contact_id, location_id=location_id,
            service_id=service_id,
            owning_organization_id=customer.servicing_organization_id or customer.owner_organization_id,
            subject=subject, description=description, ticket_type=ticket_type, priority=priority,
            status="new", source="third_party_portal", sla_target_at=now + timedelta(hours=SLA_HOURS[priority]),
            created_by_user_id=self.context.user_id, updated_by_user_id=self.context.user_id,
        )
        self.db.add(ticket); self.db.flush(); ticket.ticket_number = f"TKT-{ticket.id:06d}"
        detail = f"Submitted by {self.context.organization.effective_name} — {self.context.user.full_name}."
        self.db.add(TicketEntry(ticket_id=ticket.id, entry_type="system", visibility="customer", body=detail, author_user_id=self.context.user_id))
        self._notify_staff(ticket)
        return ticket

    def add_reply(self, ticket: Ticket, body: str) -> TicketEntry:
        body = body.strip()
        if not body:
            raise ValueError("A reply is required.")
        entry = TicketEntry(ticket_id=ticket.id, entry_type="public_reply", visibility="customer", body=body, author_user_id=self.context.user_id)
        self.db.add(entry)
        ticket.updated_by_user_id = self.context.user_id
        if ticket.status in {"new", "pending_customer", "resolved", "closed"}:
            ticket.status = "open"
        self._notify_staff(ticket, reply=True)
        return entry

    def _notify_staff(self, ticket: Ticket, reply: bool = False) -> None:
        users = list(self.db.scalars(
            select(User).join(Organization, User.organization_id == Organization.id).where(
                User.active.is_(True), User.deleted_at.is_(None), Organization.organization_type == Organization.STAFF_TYPE,
            )
        ))
        for user in users:
            self.db.add(NotificationEvent(
                event_type="partner.ticket_reply" if reply else "partner.ticket_created",
                subject=(f"Third-party reply: {ticket.ticket_number}" if reply else f"Third-party ticket: {ticket.ticket_number}"),
                payload="{}", recipient_user_id=user.id, organization_id=ticket.owning_organization_id,
                channel="internal", status="pending", target_url=f"/tickets/{ticket.id}",
            ))
