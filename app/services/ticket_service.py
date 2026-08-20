from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.database.customer_models import Customer
from app.database.models import User
from app.database.ticket_models import Ticket, TicketEntry
from app.security.context import SecurityContext
from app.services.customer_service import CustomerService


TICKET_STATUSES = {"new", "open", "pending_customer", "scheduled", "resolved", "closed"}
TICKET_PRIORITIES = {"low", "normal", "high", "urgent"}
TICKET_TYPES = {
    "no_internet_all_devices", "no_internet_single_device", "internet_slow",
    "internet_intermittent", "internet_wifi", "internet_other",
    "phone_no_dial_tone", "phone_inbound", "phone_outbound", "phone_quality",
    "phone_voicemail", "phone_other", "email_send_receive", "email_login",
    "email_spam", "email_setup", "email_other", "billing_question",
    "billing_payment", "billing_charge", "billing_other", "service_request", "other",
    # Retained so existing tickets created before v1.25.2 remain editable.
    "support", "outage", "installation", "billing", "phone",
}
SLA_HOURS = {"urgent": 2, "high": 4, "normal": 24, "low": 72}


@dataclass(slots=True)
class TicketService:
    db: Session
    context: SecurityContext

    def scope(self, statement: Select) -> Select:
        statement = statement.join(Customer, Ticket.customer_id == Customer.id)
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
        priority: str = "",
        ticket_type: str = "",
        assigned_user_id: int | None = None,
        customer_id: int | None = None,
        limit: int = 500,
    ) -> list[Ticket]:
        statement = self.scope(select(Ticket))
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Ticket.ticket_number).like(term),
                    func.lower(Ticket.subject).like(term),
                    func.lower(Ticket.description).like(term),
                    func.lower(Customer.name).like(term),
                )
            )
        if status in TICKET_STATUSES:
            statement = statement.where(Ticket.status == status)
        if priority in TICKET_PRIORITIES:
            statement = statement.where(Ticket.priority == priority)
        if ticket_type in TICKET_TYPES:
            statement = statement.where(Ticket.ticket_type == ticket_type)
        if assigned_user_id:
            statement = statement.where(Ticket.assigned_user_id == assigned_user_id)
        if customer_id:
            statement = statement.where(Ticket.customer_id == customer_id)
        return list(
            self.db.scalars(
                statement.order_by(Ticket.updated_at.desc()).limit(max(1, min(limit, 2000)))
            ).unique()
        )

    def get(self, ticket_id: int) -> Ticket | None:
        return self.db.scalar(self.scope(select(Ticket).where(Ticket.id == ticket_id)))

    def visible_customers(self) -> list[Customer]:
        return CustomerService(self.db, self.context).list(status="active", limit=2000)

    def assignable_users(self) -> list[User]:
        statement = select(User).where(User.active.is_(True), User.deleted_at.is_(None))
        if not self.context.is_staff:
            statement = statement.where(User.organization_id == self.context.organization_id)
        return list(self.db.scalars(statement.order_by(User.full_name)).unique())

    def create(
        self,
        *,
        customer_id: int,
        subject: str,
        description: str,
        contact_id: int | None,
        location_id: int | None,
        service_id: int | None,
        ticket_type: str,
        priority: str,
        assigned_user_id: int | None,
        due_at: datetime | None,
        callback_number: str = "",
    ) -> Ticket:
        customer = CustomerService(self.db, self.context).get(customer_id)
        if customer is None:
            raise ValueError("Customer not found or is not available to your organization.")
        subject = subject.strip()
        description = description.strip()
        if not subject or not description:
            raise ValueError("Subject and problem description are required.")
        if ticket_type not in TICKET_TYPES or priority not in TICKET_PRIORITIES:
            raise ValueError("Invalid ticket type or priority.")
        contact_ids = {item.id for item in customer.contacts}
        location_ids = {item.id for item in customer.locations}
        service_ids = {item.id for item in customer.services}
        if contact_id and contact_id not in contact_ids:
            raise ValueError("The selected contact does not belong to this customer.")
        if location_id and location_id not in location_ids:
            raise ValueError("The selected location does not belong to this customer.")
        if service_id and service_id not in service_ids:
            raise ValueError("The selected service does not belong to this customer.")
        valid_user_ids = {user.id for user in self.assignable_users()}
        if assigned_user_id and assigned_user_id not in valid_user_ids:
            raise ValueError("Invalid ticket assignment.")
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            ticket_number=f"PENDING-{self.context.user_id}-{int(now.timestamp())}",
            customer_id=customer.id,
            contact_id=contact_id,
            location_id=location_id,
            service_id=service_id,
            owning_organization_id=(
                customer.servicing_organization_id or customer.owner_organization_id
            ),
            assigned_user_id=assigned_user_id,
            subject=subject,
            description=description,
            ticket_type=ticket_type,
            priority=priority,
            status="new",
            source="portal",
            due_at=due_at,
            sla_target_at=now + timedelta(hours=SLA_HOURS[priority]),
            created_by_user_id=self.context.user_id,
            updated_by_user_id=self.context.user_id,
        )
        self.db.add(ticket)
        self.db.flush()
        ticket.ticket_number = f"TKT-{ticket.id:06d}"
        self.db.add(
            TicketEntry(
                ticket_id=ticket.id,
                entry_type="system",
                visibility="customer",
                body=f"Ticket created with {priority.title()} priority.",
                author_user_id=self.context.user_id,
            )
        )
        if callback_number:
            self.db.add(
                TicketEntry(
                    ticket_id=ticket.id,
                    entry_type="callback_number",
                    visibility="internal",
                    body=callback_number,
                    author_user_id=self.context.user_id,
                )
            )
        return ticket
