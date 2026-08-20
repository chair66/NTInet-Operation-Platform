from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MobileCustomer(Base):
    __tablename__ = "mobile_customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        index=True,
    )
    customer_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
    )
    customer_type: Mapped[str] = mapped_column(
        String(20),
        default="consumer",
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(80), default="")
    business_name: Mapped[str] = mapped_column(String(160), default="")
    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    phone: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        index=True,
    )
    provider_customer_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )

    @property
    def display_name(self) -> str:
        if self.business_name.strip():
            return self.business_name.strip()
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.customer_number


class MobilePlan(Base):
    __tablename__ = "mobile_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_code: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    data_gb: Mapped[int] = mapped_column(Integer, default=0)
    monthly_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
    )
    top_up_price_per_gb: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
    )
    unlimited_talk_text: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    provider_plan_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )


class MobileSIM(Base):
    __tablename__ = "mobile_sims"

    id: Mapped[int] = mapped_column(primary_key=True)
    iccid: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
    )
    sim_type: Mapped[str] = mapped_column(
        String(20),
        default="physical",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="available",
        index=True,
    )
    eid: Mapped[str] = mapped_column(String(40), default="", index=True)
    provider: Mapped[str] = mapped_column(String(60), default="")
    provider_sim_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    activation_code: Mapped[str] = mapped_column(Text, default="")
    assigned_customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("mobile_customers.id"),
        nullable=True,
        index=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )


class MobileSyncState(Base):
    __tablename__ = "mobile_sync_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_received: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class MobileLine(Base):
    __tablename__ = "mobile_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("mobile_customers.id"),
        index=True,
    )
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("mobile_plans.id"),
        nullable=True,
        index=True,
    )
    sim_id: Mapped[int | None] = mapped_column(
        ForeignKey("mobile_sims.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    mobile_number: Mapped[str] = mapped_column(
        String(32),
        default="",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        index=True,
    )
    activation_type: Mapped[str] = mapped_column(
        String(30),
        default="new_number",
    )
    provider_line_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    disconnected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )


class MobileOrder(Base):
    __tablename__ = "mobile_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("mobile_customers.id"),
        nullable=True,
        index=True,
    )
    order_type: Mapped[str] = mapped_column(
        String(40),
        default="activation",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        index=True,
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    provider_order_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )


class MobilePortRequest(Base):
    __tablename__ = "mobile_port_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    port_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("mobile_customers.id"),
        index=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("mobile_orders.id"),
        nullable=True,
        index=True,
    )
    telephone_number: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )
    losing_carrier: Mapped[str] = mapped_column(String(120), default="")
    account_number: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        index=True,
    )
    requested_foc_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_foc_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    provider_port_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )


class MobileException(Base):
    __tablename__ = "mobile_exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    exception_type: Mapped[str] = mapped_column(
        String(50),
        default="workflow",
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default="warning",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text, default="")
    resource_type: Mapped[str] = mapped_column(String(50), default="")
    resource_id: Mapped[str] = mapped_column(String(80), default="")
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )
