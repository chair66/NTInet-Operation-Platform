from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database.core import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Organization(Base):
    __tablename__ = "organizations"

    STAFF_TYPE = "staff"
    RESELLER_TYPE = "reseller"
    ALLOWED_TYPES = frozenset({STAFF_TYPE, RESELLER_TYPE})

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    organization_type: Mapped[str] = mapped_column(String(30), default=RESELLER_TYPE)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    bandwidth_account_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bandwidth_site_ids: Mapped[str] = mapped_column(Text, default="[]")
    mfa_policy: Mapped[str] = mapped_column(String(20), default="optional")
    password_expiration_days: Mapped[int] = mapped_column(default=0)
    session_timeout_minutes: Mapped[int] = mapped_column(default=480)
    allow_api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    date_format: Mapped[str] = mapped_column(String(20), default="MM/DD/YYYY")
    default_role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="organization", foreign_keys="User.organization_id")
    modules: Mapped[list["OrganizationModule"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @validates("organization_type")
    def validate_organization_type(self, _key: str, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in self.ALLOWED_TYPES:
            allowed = ", ".join(sorted(self.ALLOWED_TYPES))
            raise ValueError(
                f"Invalid organization type '{value}'. Allowed values: {allowed}"
            )
        return normalized

    @property
    def is_staff(self) -> bool:
        return self.organization_type == self.STAFF_TYPE

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None or self.status == "deleted"

    @property
    def effective_name(self) -> str:
        return (self.display_name or self.name).strip()

    @property
    def is_reseller(self) -> bool:
        return self.organization_type == self.RESELLER_TYPE

    @property
    def allowed_bandwidth_site_ids(self) -> frozenset[int]:
        import json

        try:
            values = json.loads(self.bandwidth_site_ids or "[]")
        except (TypeError, ValueError):
            return frozenset()

        result: set[int] = set()
        for value in values if isinstance(values, list) else []:
            try:
                result.add(int(value))
            except (TypeError, ValueError):
                continue
        return frozenset(result)

    def set_bandwidth_site_ids(self, values: list[int] | set[int] | tuple[int, ...]) -> None:
        import json

        normalized = sorted({int(value) for value in values})
        self.bandwidth_site_ids = json.dumps(normalized)

    def has_module(self, module_slug: str) -> bool:
        if not self.active:
            return False
        return any(
            assignment.module_slug == module_slug and assignment.enabled
            for assignment in self.modules
        )


class OrganizationModule(Base):
    __tablename__ = "organization_modules"
    __table_args__ = (
        UniqueConstraint("organization_id", "module_slug", name="uq_organization_module_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
    )
    module_slug: Mapped[str] = mapped_column(String(80), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped["Organization"] = relationship(back_populates="modules")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_role_org_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(255), default="")
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions, lazy="selectin")
    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfa_recovery_hashes: Mapped[str] = mapped_column(Text, default="[]")
    mfa_enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    invitation_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    invitation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="users", lazy="joined", foreign_keys=[organization_id])
    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    @property
    def permissions(self) -> set[str]:
        if self.is_superuser:
            return {"*"}
        return {permission.key for role in self.roles for permission in role.permissions}

    def can(self, permission: str) -> bool:
        permissions = self.permissions
        return "*" in permissions or permission in permissions

    @property
    def allowed_bandwidth_site_ids(self) -> frozenset[int]:
        import json

        try:
            values = json.loads(self.bandwidth_site_ids or "[]")
        except (TypeError, ValueError):
            return frozenset()

        result: set[int] = set()
        for value in values if isinstance(values, list) else []:
            try:
                result.add(int(value))
            except (TypeError, ValueError):
                continue
        return frozenset(result)

    def set_bandwidth_site_ids(self, values: list[int] | set[int] | tuple[int, ...]) -> None:
        import json

        normalized = sorted({int(value) for value in values})
        self.bandwidth_site_ids = json.dumps(normalized)

    def has_module(self, module_slug: str) -> bool:
        if not self.active or not self.organization.active:
            return False
        if self.is_superuser:
            return True
        return self.organization.has_module(module_slug)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(160), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    module: Mapped[str] = mapped_column(String(80), default="", index=True)
    event_data: Mapped[str] = mapped_column(Text, default="{}")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user: Mapped[User | None] = relationship(lazy="joined")


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    recipient_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(30), default="internal")
    subject: Mapped[str] = mapped_column(String(255), default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(160), default="Trusted browser")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(String(255), default="")
    user: Mapped[User] = relationship(lazy="joined")


class PortDraft(Base):
    __tablename__ = "port_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nti_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    customer_name: Mapped[str] = mapped_column(String(120), default="", index=True)
    billing_telephone_number: Mapped[str] = mapped_column(String(32), default="", index=True)
    losing_carrier_name: Mapped[str] = mapped_column(String(120), default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    bandwidth_order_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    bandwidth_status: Mapped[str] = mapped_column(String(40), default="")
    last_error_code: Mapped[str] = mapped_column(String(40), default="")
    last_error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), index=True)

    organization: Mapped[Organization] = relationship(lazy="joined")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id], lazy="joined")
    assigned_to: Mapped[User | None] = relationship(foreign_keys=[assigned_to_user_id], lazy="joined")
    attempts: Mapped[list["PortSubmissionAttempt"]] = relationship(back_populates="draft", cascade="all, delete-orphan", order_by="PortSubmissionAttempt.attempt_number")
    revisions: Mapped[list["PortDraftRevision"]] = relationship(back_populates="draft", cascade="all, delete-orphan", order_by="PortDraftRevision.revision_number")
    timeline_events: Mapped[list["PortTimelineEvent"]] = relationship(back_populates="draft", cascade="all, delete-orphan", order_by="PortTimelineEvent.created_at")
    portability_snapshots: Mapped[list["PortabilitySnapshot"]] = relationship(back_populates="draft", cascade="all, delete-orphan", order_by="PortabilitySnapshot.created_at")


class PortSubmissionAttempt(Base):
    __tablename__ = "port_submission_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("port_drafts.id", ondelete="CASCADE"), index=True)
    attempt_number: Mapped[int] = mapped_column(default=1)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    request_json: Mapped[str] = mapped_column(Text, default="{}")
    response_json: Mapped[str] = mapped_column(Text, default="{}")
    error_code: Mapped[str] = mapped_column(String(40), default="")
    error_message: Mapped[str] = mapped_column(Text, default="")

    draft: Mapped[PortDraft] = relationship(back_populates="attempts")


class PortDraftRevision(Base):
    __tablename__ = "port_draft_revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("port_drafts.id", ondelete="CASCADE"), index=True)
    revision_number: Mapped[int] = mapped_column(default=1)
    event_type: Mapped[str] = mapped_column(String(50), default="saved", index=True)
    summary: Mapped[str] = mapped_column(String(255), default="Draft saved")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    draft: Mapped[PortDraft] = relationship(back_populates="revisions")
    created_by: Mapped[User | None] = relationship(lazy="joined")


class PortTimelineEvent(Base):
    __tablename__ = "port_timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("port_drafts.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(160))
    detail: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(20), default="info")
    event_data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    draft: Mapped[PortDraft] = relationship(back_populates="timeline_events")
    created_by: Mapped[User | None] = relationship(lazy="joined")


class PortabilitySnapshot(Base):
    __tablename__ = "portability_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("port_drafts.id", ondelete="CASCADE"), index=True)
    raw_response_json: Mapped[str] = mapped_column(Text, default="{}")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    changed: Mapped[bool] = mapped_column(Boolean, default=False)
    change_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    draft: Mapped[PortDraft] = relationship(back_populates="portability_snapshots")
