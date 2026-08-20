from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database.customer_models import (
    Customer,
    CustomerContact,
    CustomerLocation,
)
from app.database.models import Organization
from app.security.context import SecurityContext


CUSTOMER_TYPES = {
    "direct",
    "reseller_managed",
    "third_party_supported",
    "internal",
    "prospect",
}
CUSTOMER_STATUSES = {"active", "inactive", "prospect", "on_hold", "suspended"}
SOURCE_TYPES = {"manual", "platypus", "imported"}
BILLING_METHODS = {"direct", "reseller", "guarantor", "non_billable", "review"}


@dataclass(slots=True)
class CustomerService:
    db: Session
    context: SecurityContext

    def scope(self, statement: Select) -> Select:
        if self.context.is_staff:
            return statement
        return statement.where(
            or_(
                Customer.owner_organization_id == self.context.organization_id,
                Customer.servicing_organization_id == self.context.organization_id,
            )
        )

    def list(
        self,
        *,
        query: str = "",
        status: str = "",
        customer_type: str = "",
        source_type: str = "",
        organization_id: int | None = None,
        limit: int = 500,
    ) -> list[Customer]:
        statement = self.scope(select(Customer))
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Customer.customer_number).like(term),
                    func.lower(Customer.name).like(term),
                    func.lower(Customer.billing_email).like(term),
                    func.lower(Customer.billing_phone).like(term),
                )
            )
        if status in CUSTOMER_STATUSES:
            statement = statement.where(Customer.status == status)
        if customer_type in CUSTOMER_TYPES:
            statement = statement.where(Customer.customer_type == customer_type)
        if source_type in SOURCE_TYPES:
            statement = statement.where(Customer.source_type == source_type)
        if organization_id is not None and self.context.is_staff:
            statement = statement.where(Customer.owner_organization_id == organization_id)
        return list(
            self.db.scalars(
                statement.order_by(Customer.name.asc()).limit(max(1, min(limit, 2000)))
            ).unique()
        )

    def get(self, customer_id: int) -> Customer | None:
        statement = self.scope(select(Customer).options(
            joinedload(Customer.owner_organization),
            joinedload(Customer.servicing_organization),
            joinedload(Customer.bill_to_customer),
            selectinload(Customer.contacts),
            selectinload(Customer.locations),
            selectinload(Customer.services),
            selectinload(Customer.external_links),
            selectinload(Customer.outgoing_relationships),
        ).where(Customer.id == customer_id))
        return self.db.scalar(statement)

    def visible_organizations(self) -> list[Organization]:
        if not self.context.is_staff:
            return [self.context.organization]
        return list(
            self.db.scalars(
                select(Organization)
                .where(Organization.active.is_(True))
                .order_by(Organization.name.asc())
            )
        )

    def available_related_customers(self, customer: Customer) -> list[Customer]:
        statement = self.scope(select(Customer).where(Customer.id != customer.id))
        return list(self.db.scalars(statement.order_by(Customer.name.asc())).unique())

    def next_customer_number(self, customer: Customer) -> str:
        return f"CUST-{customer.id:06d}"

    def create_customer(
        self,
        *,
        name: str,
        customer_type: str,
        status: str,
        owner_organization_id: int | None,
        servicing_organization_id: int | None,
        billing_method: str,
        billing_email: str,
        billing_phone: str,
        notes: str,
    ) -> Customer:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Customer name is required.")
        if customer_type not in CUSTOMER_TYPES:
            raise ValueError("Invalid customer type.")
        if status not in CUSTOMER_STATUSES:
            raise ValueError("Invalid customer status.")
        if billing_method not in BILLING_METHODS:
            raise ValueError("Invalid billing method.")

        if self.context.is_staff:
            resolved_owner = int(owner_organization_id or self.context.organization_id)
            allowed_ids = {organization.id for organization in self.visible_organizations()}
            if resolved_owner not in allowed_ids:
                raise ValueError("Invalid owning organization.")
            if servicing_organization_id and int(servicing_organization_id) not in allowed_ids:
                raise ValueError("Invalid servicing organization.")
        else:
            resolved_owner = self.context.organization_id
            servicing_organization_id = self.context.organization_id

        customer = Customer(
            customer_number=f"PENDING-{self.context.user_id}-{id(self)}",
            name=normalized_name,
            customer_type=customer_type,
            status=status,
            source_type="manual",
            owner_organization_id=resolved_owner,
            servicing_organization_id=(
                int(servicing_organization_id) if servicing_organization_id else None
            ),
            billing_method=billing_method,
            billing_email=billing_email.strip().lower(),
            billing_phone=billing_phone.strip(),
            notes=notes.strip(),
            created_by_user_id=self.context.user_id,
            updated_by_user_id=self.context.user_id,
        )
        self.db.add(customer)
        self.db.flush()
        customer.customer_number = self.next_customer_number(customer)
        return customer

    def set_primary_contact(self, customer: Customer, contact: CustomerContact) -> None:
        for existing in customer.contacts:
            existing.is_primary = existing.id == contact.id

    def set_primary_location(self, customer: Customer, location: CustomerLocation) -> None:
        for existing in customer.locations:
            existing.is_primary = existing.id == location.id
