"""TKT-1 customer foundation.

Revision ID: 20260806_02
Revises: 20260806_01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260806_02"
down_revision: Union[str, None] = "20260806_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_number", sa.String(32), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("customer_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("owner_organization_id", sa.Integer(), nullable=False),
        sa.Column("servicing_organization_id", sa.Integer(), nullable=True),
        sa.Column("bill_to_customer_id", sa.Integer(), nullable=True),
        sa.Column("billing_method", sa.String(30), nullable=False),
        sa.Column("billing_email", sa.String(255), nullable=False),
        sa.Column("billing_phone", sa.String(40), nullable=False),
        sa.Column("tax_exempt", sa.Boolean(), nullable=False),
        sa.Column("tax_exemption_reference", sa.String(100), nullable=False),
        sa.Column("purchase_order_required", sa.Boolean(), nullable=False),
        sa.Column("default_purchase_order", sa.String(80), nullable=False),
        sa.Column("payment_terms", sa.String(40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["servicing_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["bill_to_customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_customers_customer_number", "customers", ["customer_number"], unique=True)
    for column in (
        "name", "customer_type", "status", "source_type",
        "owner_organization_id", "servicing_organization_id",
        "bill_to_customer_id", "created_at", "updated_at",
    ):
        op.create_index(f"ix_customers_{column}", "customers", [column])

    op.create_table(
        "customer_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("job_title", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("office_phone", sa.String(40), nullable=False),
        sa.Column("mobile_phone", sa.String(40), nullable=False),
        sa.Column("preferred_channel", sa.String(20), nullable=False),
        sa.Column("sms_consent_status", sa.String(20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("authorized_for_support", sa.Boolean(), nullable=False),
        sa.Column("authorized_for_estimates", sa.Boolean(), nullable=False),
        sa.Column("receives_invoices", sa.Boolean(), nullable=False),
        sa.Column("portal_access_enabled", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
    )
    for column in ("customer_id", "email", "is_primary", "active"):
        op.create_index(f"ix_customer_contacts_{column}", "customer_contacts", [column])

    op.create_table(
        "customer_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("address_line_1", sa.String(180), nullable=False),
        sa.Column("address_line_2", sa.String(180), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(40), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("primary_contact_id", sa.Integer(), nullable=True),
        sa.Column("service_territory", sa.String(100), nullable=False),
        sa.Column("tax_jurisdiction", sa.String(100), nullable=False),
        sa.Column("access_instructions", sa.Text(), nullable=False),
        sa.Column("dispatch_notes", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
    )
    for column in ("customer_id", "city", "state", "postal_code", "is_primary", "active"):
        op.create_index(f"ix_customer_locations_{column}", "customer_locations", [column])

    op.create_table(
        "customer_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_customer_id", sa.Integer(), nullable=False),
        sa.Column("target_customer_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(40), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "source_customer_id", "target_customer_id", "relationship_type",
            name="uq_customer_relationship",
        ),
    )
    for column in ("source_customer_id", "target_customer_id", "relationship_type"):
        op.create_index(f"ix_customer_relationships_{column}", "customer_relationships", [column])

    op.create_table(
        "external_record_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(60), nullable=False),
        sa.Column("record_type", sa.String(60), nullable=False),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("external_account_number", sa.String(100), nullable=False),
        sa.Column("link_status", sa.String(30), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_hash", sa.String(128), nullable=False),
        sa.Column("source_snapshot_json", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("system_name", "record_type", "external_id", name="uq_external_system_record"),
        sa.UniqueConstraint("customer_id", "system_name", "record_type", name="uq_customer_external_record_type"),
    )
    for column in (
        "customer_id", "system_name", "record_type", "external_id",
        "external_account_number", "link_status",
    ):
        op.create_index(f"ix_external_record_links_{column}", "external_record_links", [column])

    op.create_table(
        "customer_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("service_type", sa.String(60), nullable=False),
        sa.Column("service_name", sa.String(160), nullable=False),
        sa.Column("service_identifier", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("activation_date", sa.Date(), nullable=True),
        sa.Column("cancellation_date", sa.Date(), nullable=True),
        sa.Column("recurring_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("billing_responsibility", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["customer_locations.id"], ondelete="SET NULL"),
    )
    for column in (
        "customer_id", "location_id", "service_type", "service_identifier", "status",
    ):
        op.create_index(f"ix_customer_services_{column}", "customer_services", [column])


def downgrade() -> None:
    op.drop_table("customer_services")
    op.drop_table("external_record_links")
    op.drop_table("customer_relationships")
    op.drop_table("customer_locations")
    op.drop_table("customer_contacts")
    op.drop_table("customers")
