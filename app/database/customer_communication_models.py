from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CustomerCommunication(Base):
    __tablename__ = "customer_communications"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("communication_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    estimate_id: Mapped[int | None] = mapped_column(ForeignKey("estimates.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    communication_profile_id: Mapped[int | None] = mapped_column(ForeignKey("communication_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(20), default="outbound", index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text)
    source_address: Mapped[str] = mapped_column(String(255), default="", index=True)
    destination_address: Mapped[str] = mapped_column(String(255), default="", index=True)
    profile_name: Mapped[str] = mapped_column(String(120), default="")
    provider: Mapped[str] = mapped_column(String(40), default="")
    provider_message_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    consent_override: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_override_reason: Mapped[str] = mapped_column(Text, default="")
    thread_key: Mapped[str] = mapped_column(String(180), default="", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_error_code: Mapped[str] = mapped_column(String(40), default="")
    delivery_description: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_message_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    email_in_reply_to: Mapped[str] = mapped_column(String(255), default="", index=True)
    email_references: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    ticket = relationship("Ticket", lazy="joined")
    estimate = relationship("Estimate", lazy="joined")
    organization = relationship("Organization", lazy="joined")
    communication_profile = relationship("CommunicationProfile", lazy="joined")
    created_by = relationship("User", lazy="joined")
    conversation = relationship("CommunicationConversation", back_populates="messages")


class CommunicationConversation(Base):
    __tablename__ = "communication_conversations"
    __table_args__ = (UniqueConstraint("thread_key", name="uq_communication_conversation_thread_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    estimate_id: Mapped[int | None] = mapped_column(ForeignKey("estimates.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    communication_profile_id: Mapped[int | None] = mapped_column(ForeignKey("communication_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    thread_key: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    last_message_preview: Mapped[str] = mapped_column(String(255), default="")
    last_direction: Mapped[str] = mapped_column(String(20), default="", index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    ticket = relationship("Ticket", lazy="select")
    estimate = relationship("Estimate", lazy="select")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined")
    communication_profile = relationship("CommunicationProfile", lazy="joined")
    messages: Mapped[list["CustomerCommunication"]] = relationship(
        back_populates="conversation", lazy="selectin", order_by="CustomerCommunication.created_at"
    )


class BandwidthMessagingWebhookEvent(Base):
    __tablename__ = "bandwidth_messaging_webhook_events"
    __table_args__ = (UniqueConstraint("deduplication_key", name="uq_bandwidth_webhook_deduplication_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    deduplication_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    provider_message_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    application_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_address: Mapped[str] = mapped_column(String(40), default="", index=True)
    destination_address: Mapped[str] = mapped_column(String(40), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    error_code: Mapped[str] = mapped_column(String(40), default="")
    processing_status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    customer_communication_id: Mapped[int | None] = mapped_column(ForeignKey("customer_communications.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_outbound_message_id: Mapped[int | None] = mapped_column(ForeignKey("ticket_outbound_messages.id", ondelete="SET NULL"), nullable=True, index=True)
    event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    customer_communication = relationship("CustomerCommunication", lazy="select")
    ticket_outbound_message = relationship("TicketOutboundMessage", lazy="select")


class InboundEmailImport(Base):
    __tablename__ = "inbound_email_imports"
    __table_args__ = (
        UniqueConstraint("communication_profile_id", "uidvalidity", "imap_uid", name="uq_inbound_email_profile_uid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    communication_profile_id: Mapped[int] = mapped_column(ForeignKey("communication_profiles.id", ondelete="CASCADE"), index=True)
    uidvalidity: Mapped[str] = mapped_column(String(80), default="")
    imap_uid: Mapped[int] = mapped_column(Integer)
    email_message_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    sender_address: Mapped[str] = mapped_column(String(255), default="", index=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    processing_status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    customer_communication_id: Mapped[int | None] = mapped_column(ForeignKey("customer_communications.id", ondelete="SET NULL"), nullable=True, index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    communication_profile = relationship("CommunicationProfile", lazy="joined")
    customer_communication = relationship("CustomerCommunication", lazy="select")
