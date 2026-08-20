from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    customer_type: Mapped[str] = mapped_column(String(40), default="direct", index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", index=True)
    owner_organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    servicing_organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    bill_to_customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"), nullable=True, index=True
    )
    billing_method: Mapped[str] = mapped_column(String(30), default="direct")
    billing_email: Mapped[str] = mapped_column(String(255), default="")
    billing_phone: Mapped[str] = mapped_column(String(40), default="")
    tax_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_exemption_reference: Mapped[str] = mapped_column(String(100), default="")
    purchase_order_required: Mapped[bool] = mapped_column(Boolean, default=False)
    default_purchase_order: Mapped[str] = mapped_column(String(80), default="")
    payment_terms: Mapped[str] = mapped_column(String(40), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, index=True
    )

    owner_organization = relationship(
        "Organization", foreign_keys=[owner_organization_id], lazy="joined"
    )
    servicing_organization = relationship(
        "Organization", foreign_keys=[servicing_organization_id], lazy="joined"
    )
    bill_to_customer: Mapped["Customer | None"] = relationship(
        remote_side=[id], foreign_keys=[bill_to_customer_id], lazy="joined"
    )
    contacts: Mapped[list["CustomerContact"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    locations: Mapped[list["CustomerLocation"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    services: Mapped[list["CustomerService"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    plume_network: Mapped["PlumeCustomerNetwork | None"] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin",
        uselist=False,
    )
    external_links: Mapped[list["ExternalRecordLink"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    outgoing_relationships: Mapped[list["CustomerRelationship"]] = relationship(
        back_populates="source_customer",
        foreign_keys="CustomerRelationship.source_customer_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incoming_relationships: Mapped[list["CustomerRelationship"]] = relationship(
        back_populates="target_customer",
        foreign_keys="CustomerRelationship.target_customer_id",
        lazy="selectin",
    )

    @property
    def primary_contact(self) -> "CustomerContact | None":
        return next((contact for contact in self.contacts if contact.is_primary), None)

    @property
    def primary_location(self) -> "CustomerLocation | None":
        return next((location for location in self.locations if location.is_primary), None)

    @property
    def platypus_link(self) -> "ExternalRecordLink | None":
        return next(
            (
                link
                for link in self.external_links
                if link.system_name.lower() == "platypus"
                and link.record_type.lower() == "customer"
            ),
            None,
        )


class CustomerContact(Base):
    __tablename__ = "customer_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80), default="")
    job_title: Mapped[str] = mapped_column(String(120), default="")
    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    office_phone: Mapped[str] = mapped_column(String(40), default="")
    mobile_phone: Mapped[str] = mapped_column(String(40), default="")
    preferred_channel: Mapped[str] = mapped_column(String(20), default="email")
    sms_consent_status: Mapped[str] = mapped_column(String(20), default="unknown")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    authorized_for_support: Mapped[bool] = mapped_column(Boolean, default=True)
    authorized_for_estimates: Mapped[bool] = mapped_column(Boolean, default=False)
    receives_invoices: Mapped[bool] = mapped_column(Boolean, default=False)
    portal_access_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[Customer] = relationship(back_populates="contacts")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class CustomerLocation(Base):
    __tablename__ = "customer_locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(140), default="Primary Location")
    address_line_1: Mapped[str] = mapped_column(String(180))
    address_line_2: Mapped[str] = mapped_column(String(180), default="")
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(40), default="SC", index=True)
    postal_code: Mapped[str] = mapped_column(String(20), index=True)
    country: Mapped[str] = mapped_column(String(2), default="US")
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    primary_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True
    )
    service_territory: Mapped[str] = mapped_column(String(100), default="")
    tax_jurisdiction: Mapped[str] = mapped_column(String(100), default="")
    access_instructions: Mapped[str] = mapped_column(Text, default="")
    dispatch_notes: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[Customer] = relationship(back_populates="locations")
    primary_contact: Mapped[CustomerContact | None] = relationship(lazy="joined")

    @property
    def one_line_address(self) -> str:
        street = " ".join(part for part in (self.address_line_1, self.address_line_2) if part)
        return f"{street}, {self.city}, {self.state} {self.postal_code}".strip()


class CustomerRelationship(Base):
    __tablename__ = "customer_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_customer_id",
            "target_customer_id",
            "relationship_type",
            name="uq_customer_relationship",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    target_customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(40), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source_customer: Mapped[Customer] = relationship(
        back_populates="outgoing_relationships", foreign_keys=[source_customer_id]
    )
    target_customer: Mapped[Customer] = relationship(
        back_populates="incoming_relationships", foreign_keys=[target_customer_id], lazy="joined"
    )


class ExternalRecordLink(Base):
    __tablename__ = "external_record_links"
    __table_args__ = (
        UniqueConstraint(
            "system_name",
            "record_type",
            "external_id",
            name="uq_external_system_record",
        ),
        UniqueConstraint(
            "customer_id",
            "system_name",
            "record_type",
            name="uq_customer_external_record_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    system_name: Mapped[str] = mapped_column(String(60), index=True)
    record_type: Mapped[str] = mapped_column(String(60), default="customer", index=True)
    external_id: Mapped[str] = mapped_column(String(160), index=True)
    external_account_number: Mapped[str] = mapped_column(String(100), default="", index=True)
    link_status: Mapped[str] = mapped_column(String(30), default="simulated", index=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_hash: Mapped[str] = mapped_column(String(128), default="")
    source_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    notes: Mapped[str] = mapped_column(Text, default="")

    customer: Mapped[Customer] = relationship(back_populates="external_links")


class CustomerService(Base):
    __tablename__ = "customer_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_type: Mapped[str] = mapped_column(String(60), index=True)
    service_name: Mapped[str] = mapped_column(String(160))
    service_identifier: Mapped[str] = mapped_column(String(160), default="", index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    quantity: Mapped[int] = mapped_column(default=1)
    activation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cancellation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurring_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    billing_responsibility: Mapped[str] = mapped_column(String(30), default="customer")
    source_system: Mapped[str] = mapped_column(String(40), default="manual", index=True)
    source_rate_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_rate_code: Mapped[str] = mapped_column(String(120), default="", index=True)
    managed_by_source: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[Customer] = relationship(back_populates="services")
    location: Mapped[CustomerLocation | None] = relationship(lazy="joined")


class ServiceRateMapping(Base):
    """Maps a stable Platypus rate ID to an operational NOP service."""

    __tablename__ = "service_rate_mappings"
    __table_args__ = (
        UniqueConstraint("source_system", "source_rate_id", name="uq_service_rate_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_system: Mapped[str] = mapped_column(String(40), default="platypus", index=True)
    source_rate_id: Mapped[str] = mapped_column(String(120), index=True)
    source_rate_code: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_rate_name: Mapped[str] = mapped_column(String(180), default="")
    service_type: Mapped[str] = mapped_column(String(60), index=True)
    service_name: Mapped[str] = mapped_column(String(160))
    module_slug: Mapped[str] = mapped_column(String(80), default="")
    quantity_mode: Mapped[str] = mapped_column(String(30), default="rate_quantity")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class PlumeCustomerNetwork(Base):
    __tablename__ = "plume_customer_networks"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), unique=True, index=True
    )
    customer_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plume_customer_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    plume_location_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    network_name: Mapped[str] = mapped_column(String(160), default="")
    service_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    sync_status: Mapped[str] = mapped_column(String(30), default="not_synced", index=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_error: Mapped[str] = mapped_column(Text, default="")
    source_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[Customer] = relationship(back_populates="plume_network")
    location: Mapped[CustomerLocation | None] = relationship(lazy="joined")
    pods: Mapped[list["PlumePod"]] = relationship(
        back_populates="network", cascade="all, delete-orphan", lazy="selectin"
    )
    devices: Mapped[list["PlumeClientDevice"]] = relationship(
        back_populates="network", cascade="all, delete-orphan", lazy="selectin"
    )


class PlumePod(Base):
    __tablename__ = "plume_pods"
    __table_args__ = (
        UniqueConstraint("network_id", "plume_pod_id", name="uq_plume_network_pod"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    network_id: Mapped[int] = mapped_column(
        ForeignKey("plume_customer_networks.id", ondelete="CASCADE"), index=True
    )
    plume_pod_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    serial_number: Mapped[str] = mapped_column(String(120), default="", index=True)
    mac_address: Mapped[str] = mapped_column(String(32), default="", index=True)
    model: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(30), default="extender")
    connection_type: Mapped[str] = mapped_column(String(30), default="wireless")
    status: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    firmware_version: Mapped[str] = mapped_column(String(80), default="")
    health_status: Mapped[str] = mapped_column(String(40), default="")
    signal_strength: Mapped[int | None] = mapped_column(nullable=True)
    connected_device_count: Mapped[int] = mapped_column(default=0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")

    network: Mapped[PlumeCustomerNetwork] = relationship(back_populates="pods")


class PlumeClientDevice(Base):
    __tablename__ = "plume_client_devices"
    __table_args__ = (
        UniqueConstraint("network_id", "plume_device_id", name="uq_plume_network_device"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    network_id: Mapped[int] = mapped_column(
        ForeignKey("plume_customer_networks.id", ondelete="CASCADE"), index=True
    )
    pod_id: Mapped[int | None] = mapped_column(
        ForeignKey("plume_pods.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plume_device_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    mac_address: Mapped[str] = mapped_column(String(32), default="", index=True)
    manufacturer: Mapped[str] = mapped_column(String(160), default="")
    device_type: Mapped[str] = mapped_column(String(80), default="")
    ipv4_address: Mapped[str] = mapped_column(String(64), default="")
    ipv6_address: Mapped[str] = mapped_column(String(128), default="")
    connection_type: Mapped[str] = mapped_column(String(30), default="wireless")
    wifi_band: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    signal_strength: Mapped[int | None] = mapped_column(nullable=True)
    link_speed_mbps: Mapped[int | None] = mapped_column(nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")

    network: Mapped[PlumeCustomerNetwork] = relationship(back_populates="devices")
    pod: Mapped[PlumePod | None] = relationship(lazy="joined")
