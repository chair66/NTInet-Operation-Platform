from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    owning_organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    assigned_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email_profile_id: Mapped[int | None] = mapped_column(ForeignKey("communication_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    sms_profile_id: Mapped[int | None] = mapped_column(ForeignKey("communication_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(240), index=True)
    description: Mapped[str] = mapped_column(Text)
    ticket_type: Mapped[str] = mapped_column(String(40), default="support", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    source: Mapped[str] = mapped_column(String(30), default="portal", index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_target_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, index=True
    )

    customer = relationship("Customer", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    location = relationship("CustomerLocation", lazy="joined")
    service = relationship("CustomerService", lazy="joined")
    owning_organization = relationship("Organization", lazy="joined")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined")
    email_profile = relationship("CommunicationProfile", foreign_keys=[email_profile_id], lazy="joined")
    sms_profile = relationship("CommunicationProfile", foreign_keys=[sms_profile_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")
    entries: Mapped[list["TicketEntry"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="selectin",
        order_by="TicketEntry.created_at",
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="selectin"
    )
    outbound_messages: Mapped[list["TicketOutboundMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="selectin",
        order_by="TicketOutboundMessage.created_at",
    )
    jobs = relationship("Job", back_populates="ticket", lazy="selectin")


class TicketEntry(Base):
    __tablename__ = "ticket_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    entry_type: Mapped[str] = mapped_column(String(30), default="public_reply", index=True)
    visibility: Mapped[str] = mapped_column(String(20), default="customer", index=True)
    body: Mapped[str] = mapped_column(Text)
    author_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    ticket: Mapped[Ticket] = relationship(back_populates="entries")
    author = relationship("User", lazy="joined")
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="entry", lazy="selectin"
    )


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("ticket_entries.id", ondelete="SET NULL"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    ticket: Mapped[Ticket] = relationship(back_populates="attachments")
    entry: Mapped[TicketEntry | None] = relationship(back_populates="attachments")
    uploaded_by = relationship("User", lazy="joined")


class TicketOutboundMessage(Base):
    __tablename__ = "ticket_outbound_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    entry_id: Mapped[int | None] = mapped_column(ForeignKey("ticket_entries.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    communication_profile_id: Mapped[int | None] = mapped_column(ForeignKey("communication_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    profile_name: Mapped[str] = mapped_column(String(120), default="")
    sender_identity: Mapped[str] = mapped_column(String(255), default="")
    channel: Mapped[str] = mapped_column(String(20), index=True)
    destination: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    provider: Mapped[str] = mapped_column(String(40), default="")
    provider_message_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    deduplication_key: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    attempt_count: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    ticket = relationship("Ticket", back_populates="outbound_messages", lazy="joined")
    entry = relationship("TicketEntry", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    communication_profile = relationship("CommunicationProfile", lazy="joined")
    created_by = relationship("User", lazy="joined")
