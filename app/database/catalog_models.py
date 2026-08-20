from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CatalogCategory(Base):
    __tablename__ = "catalog_categories"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_catalog_category_org_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("catalog_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    organization = relationship("Organization", lazy="joined")
    parent = relationship("CatalogCategory", remote_side="CatalogCategory.id", back_populates="children", lazy="joined")
    children = relationship("CatalogCategory", back_populates="parent", lazy="selectin", order_by="CatalogCategory.name")
    items = relationship("CatalogItem", back_populates="category_record", lazy="selectin")


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (UniqueConstraint("organization_id", "sku", name="uq_catalog_org_sku"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(60), index=True)
    item_type: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(100), default="", index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("catalog_categories.id", ondelete="RESTRICT"), index=True)
    brand: Mapped[str] = mapped_column(String(120), default="", index=True)
    model_number: Mapped[str] = mapped_column(String(120), default="", index=True)
    ordering_note: Mapped[str] = mapped_column(Text, default="")
    ordering_url: Mapped[str] = mapped_column(String(1000), default="")
    name: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(30), default="each")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    taxable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    organization = relationship("Organization", lazy="joined")
    category_record = relationship("CatalogCategory", back_populates="items", lazy="joined")


class Estimate(Base):
    __tablename__ = "estimates"
    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("customer_locations.id", ondelete="RESTRICT"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    title: Mapped[str] = mapped_column(String(200))
    internal_notes: Mapped[str] = mapped_column(Text, default="")
    customer_notes: Mapped[str] = mapped_column(Text, default="")
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    taxable_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    margin_percent: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    won_option_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    accepted_by_name: Mapped[str] = mapped_column(String(160), default="")
    accepted_by_email: Mapped[str] = mapped_column(String(255), default="")
    accepted_signature_data: Mapped[str] = mapped_column(Text, default="")
    accepted_ip_address: Mapped[str] = mapped_column(String(64), default="")
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    organization = relationship("Organization", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    location = relationship("CustomerLocation", lazy="joined")
    job = relationship("Job", back_populates="estimates", lazy="joined")
    lines = relationship("EstimateLineItem", back_populates="estimate", lazy="selectin",
                         order_by="EstimateLineItem.sort_order", overlaps="lines,option")
    options = relationship("EstimateOption", back_populates="estimate", cascade="all, delete-orphan",
                           lazy="selectin", order_by="EstimateOption.sort_order")
    documents = relationship("EstimateDocument", back_populates="estimate", cascade="all, delete-orphan", lazy="selectin")
    deliveries = relationship("EstimateDelivery", back_populates="estimate", cascade="all, delete-orphan", lazy="selectin", order_by="EstimateDelivery.created_at")


class EstimateOption(Base):
    __tablename__ = "estimate_options"
    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    customer_notes: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    taxable_subtotal: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(14,2), default=Decimal("0"))
    margin_percent: Mapped[Decimal] = mapped_column(Numeric(8,2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    estimate = relationship("Estimate", back_populates="options")
    lines = relationship("EstimateLineItem", back_populates="option", cascade="all, delete-orphan", lazy="selectin", order_by="EstimateLineItem.sort_order", overlaps="estimate,lines")


class EstimateLineItem(Base):
    __tablename__ = "estimate_line_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("estimate_options.id", ondelete="CASCADE"), index=True)
    catalog_item_id: Mapped[int | None] = mapped_column(ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    item_type: Mapped[str] = mapped_column(String(20))
    sku: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(30), default="each")
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("1"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))
    taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    line_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    line_discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    estimate = relationship("Estimate", back_populates="lines", overlaps="lines,option")
    option = relationship("EstimateOption", back_populates="lines", overlaps="estimate,lines")
    catalog_item = relationship("CatalogItem", lazy="joined")


class EstimateEmailTemplate(Base):
    __tablename__ = "estimate_email_templates"
    __table_args__ = (UniqueConstraint("organization_id","name",name="uq_est_email_template_org_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id",ondelete="CASCADE"),index=True)
    name: Mapped[str] = mapped_column(String(160))
    subject_template: Mapped[str] = mapped_column(String(300))
    body_template: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean,default=True,index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now,onupdate=utc_now)


class StoredDocument(Base):
    __tablename__ = "stored_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id",ondelete="CASCADE"),index=True)
    name: Mapped[str] = mapped_column(String(200),index=True)
    description: Mapped[str] = mapped_column(Text,default="")
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255),unique=True)
    content_type: Mapped[str] = mapped_column(String(120),default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer,default=0)
    active: Mapped[bool] = mapped_column(Boolean,default=True,index=True)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now,index=True)


class EstimateDocument(Base):
    __tablename__ = "estimate_documents"
    __table_args__ = (UniqueConstraint("estimate_id","document_id",name="uq_estimate_document"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id",ondelete="CASCADE"),index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("stored_documents.id",ondelete="CASCADE"),index=True)
    attached_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now)
    estimate = relationship("Estimate",back_populates="documents")
    document = relationship("StoredDocument",lazy="joined")


class EstimateDelivery(Base):
    __tablename__ = "estimate_deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id",ondelete="CASCADE"),index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id",ondelete="SET NULL"),nullable=True,index=True)
    recipient_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(300))
    message_body: Mapped[str] = mapped_column(Text)
    option_ids_json: Mapped[str] = mapped_column(Text,default="[]")
    document_ids_json: Mapped[str] = mapped_column(Text,default="[]")
    pdf_attached: Mapped[bool] = mapped_column(Boolean,default=True)
    acceptance_token: Mapped[str] = mapped_column(String(1000),default="")
    status: Mapped[str] = mapped_column(String(20),index=True)
    error_message: Mapped[str] = mapped_column(Text,default="")
    sent_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=utc_now,index=True)
    estimate = relationship("Estimate",back_populates="deliveries")
    contact = relationship("CustomerContact",lazy="joined")


class JobLineItem(Base):
    __tablename__ = "job_line_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    catalog_item_id: Mapped[int | None] = mapped_column(ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True, index=True)
    estimate_line_item_id: Mapped[int | None] = mapped_column(ForeignKey("estimate_line_items.id", ondelete="SET NULL"), nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    item_type: Mapped[str] = mapped_column(String(20))
    sku: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(30), default="each")
    estimated_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0"))
    estimated_unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    actual_unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))
    taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    job = relationship("Job", back_populates="line_items")
    catalog_item = relationship("CatalogItem", lazy="joined")
    estimate_line_item = relationship("EstimateLineItem", lazy="joined")
