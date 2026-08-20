"""Platypus service mapping and Plume customer network foundation.

Revision ID: 20260807_18
Revises: 20260807_17
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260807_18"
down_revision: Union[str, None] = "20260807_17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customer_services",
        sa.Column("source_system", sa.String(length=40), nullable=False,
                  server_default="manual"),
    )
    op.add_column(
        "customer_services",
        sa.Column("source_rate_id", sa.String(length=120), nullable=False,
                  server_default=""),
    )
    op.add_column(
        "customer_services",
        sa.Column("source_rate_code", sa.String(length=120), nullable=False,
                  server_default=""),
    )
    op.add_column(
        "customer_services",
        sa.Column("managed_by_source", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.add_column(
        "customer_services",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "customer_services",
        sa.Column("source_snapshot_json", sa.Text(), nullable=False,
                  server_default="{}"),
    )
    op.create_index(
        "ix_customer_services_source_system", "customer_services", ["source_system"]
    )
    op.create_index(
        "ix_customer_services_source_rate_id", "customer_services", ["source_rate_id"]
    )
    op.create_index(
        "ix_customer_services_source_rate_code", "customer_services", ["source_rate_code"]
    )

    op.create_table(
        "service_rate_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_system", sa.String(length=40), nullable=False,
                  server_default="platypus"),
        sa.Column("source_rate_id", sa.String(length=120), nullable=False),
        sa.Column("source_rate_code", sa.String(length=120), nullable=False,
                  server_default=""),
        sa.Column("source_rate_name", sa.String(length=180), nullable=False,
                  server_default=""),
        sa.Column("service_type", sa.String(length=60), nullable=False),
        sa.Column("service_name", sa.String(length=160), nullable=False),
        sa.Column("module_slug", sa.String(length=80), nullable=False,
                  server_default=""),
        sa.Column("quantity_mode", sa.String(length=30), nullable=False,
                  server_default="rate_quantity"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system", "source_rate_id", name="uq_service_rate_source"
        ),
    )
    op.create_index(
        "ix_service_rate_mappings_source_system", "service_rate_mappings", ["source_system"]
    )
    op.create_index(
        "ix_service_rate_mappings_source_rate_id", "service_rate_mappings", ["source_rate_id"]
    )
    op.create_index(
        "ix_service_rate_mappings_source_rate_code", "service_rate_mappings", ["source_rate_code"]
    )
    op.create_index(
        "ix_service_rate_mappings_service_type", "service_rate_mappings", ["service_type"]
    )
    op.create_index(
        "ix_service_rate_mappings_active", "service_rate_mappings", ["active"]
    )

    op.create_table(
        "plume_customer_networks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("customer_location_id", sa.Integer(), nullable=True),
        sa.Column("plume_customer_id", sa.String(length=160), nullable=False,
                  server_default=""),
        sa.Column("plume_location_id", sa.String(length=160), nullable=False,
                  server_default=""),
        sa.Column("network_name", sa.String(length=160), nullable=False,
                  server_default=""),
        sa.Column("service_status", sa.String(length=30), nullable=False,
                  server_default="pending"),
        sa.Column("sync_status", sa.String(length=30), nullable=False,
                  server_default="not_synced"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_snapshot_json", sa.Text(), nullable=False,
                  server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["customer_location_id"], ["customer_locations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plume_customer_networks_customer_id",
        "plume_customer_networks", ["customer_id"], unique=True,
    )
    op.create_index(
        "ix_plume_customer_networks_customer_location_id",
        "plume_customer_networks", ["customer_location_id"],
    )
    op.create_index(
        "ix_plume_customer_networks_plume_customer_id",
        "plume_customer_networks", ["plume_customer_id"],
    )
    op.create_index(
        "ix_plume_customer_networks_plume_location_id",
        "plume_customer_networks", ["plume_location_id"],
    )
    op.create_index(
        "ix_plume_customer_networks_service_status",
        "plume_customer_networks", ["service_status"],
    )
    op.create_index(
        "ix_plume_customer_networks_sync_status",
        "plume_customer_networks", ["sync_status"],
    )

    op.create_table(
        "plume_pods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("network_id", sa.Integer(), nullable=False),
        sa.Column("plume_pod_id", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("serial_number", sa.String(length=120), nullable=False,
                  server_default=""),
        sa.Column("mac_address", sa.String(length=32), nullable=False,
                  server_default=""),
        sa.Column("model", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("role", sa.String(length=30), nullable=False,
                  server_default="extender"),
        sa.Column("connection_type", sa.String(length=30), nullable=False,
                  server_default="wireless"),
        sa.Column("status", sa.String(length=30), nullable=False,
                  server_default="unknown"),
        sa.Column("firmware_version", sa.String(length=80), nullable=False,
                  server_default=""),
        sa.Column("health_status", sa.String(length=40), nullable=False,
                  server_default=""),
        sa.Column("signal_strength", sa.Integer(), nullable=True),
        sa.Column("connected_device_count", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_snapshot_json", sa.Text(), nullable=False,
                  server_default="{}"),
        sa.ForeignKeyConstraint(
            ["network_id"], ["plume_customer_networks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("network_id", "plume_pod_id", name="uq_plume_network_pod"),
    )
    op.create_index("ix_plume_pods_network_id", "plume_pods", ["network_id"])
    op.create_index("ix_plume_pods_plume_pod_id", "plume_pods", ["plume_pod_id"])
    op.create_index("ix_plume_pods_serial_number", "plume_pods", ["serial_number"])
    op.create_index("ix_plume_pods_mac_address", "plume_pods", ["mac_address"])
    op.create_index("ix_plume_pods_status", "plume_pods", ["status"])

    op.create_table(
        "plume_client_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("network_id", sa.Integer(), nullable=False),
        sa.Column("pod_id", sa.Integer(), nullable=True),
        sa.Column("plume_device_id", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("mac_address", sa.String(length=32), nullable=False,
                  server_default=""),
        sa.Column("manufacturer", sa.String(length=160), nullable=False,
                  server_default=""),
        sa.Column("device_type", sa.String(length=80), nullable=False,
                  server_default=""),
        sa.Column("ipv4_address", sa.String(length=64), nullable=False,
                  server_default=""),
        sa.Column("ipv6_address", sa.String(length=128), nullable=False,
                  server_default=""),
        sa.Column("connection_type", sa.String(length=30), nullable=False,
                  server_default="wireless"),
        sa.Column("wifi_band", sa.String(length=20), nullable=False,
                  server_default=""),
        sa.Column("status", sa.String(length=30), nullable=False,
                  server_default="unknown"),
        sa.Column("signal_strength", sa.Integer(), nullable=True),
        sa.Column("link_speed_mbps", sa.Integer(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_snapshot_json", sa.Text(), nullable=False,
                  server_default="{}"),
        sa.ForeignKeyConstraint(
            ["network_id"], ["plume_customer_networks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pod_id"], ["plume_pods.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "network_id", "plume_device_id", name="uq_plume_network_device"
        ),
    )
    op.create_index(
        "ix_plume_client_devices_network_id", "plume_client_devices", ["network_id"]
    )
    op.create_index(
        "ix_plume_client_devices_pod_id", "plume_client_devices", ["pod_id"]
    )
    op.create_index(
        "ix_plume_client_devices_plume_device_id",
        "plume_client_devices", ["plume_device_id"],
    )
    op.create_index(
        "ix_plume_client_devices_mac_address", "plume_client_devices", ["mac_address"]
    )
    op.create_index(
        "ix_plume_client_devices_status", "plume_client_devices", ["status"]
    )


def downgrade() -> None:
    op.drop_table("plume_client_devices")
    op.drop_table("plume_pods")
    op.drop_table("plume_customer_networks")
    op.drop_table("service_rate_mappings")

    op.drop_index("ix_customer_services_source_rate_code", table_name="customer_services")
    op.drop_index("ix_customer_services_source_rate_id", table_name="customer_services")
    op.drop_index("ix_customer_services_source_system", table_name="customer_services")
    op.drop_column("customer_services", "source_snapshot_json")
    op.drop_column("customer_services", "last_synced_at")
    op.drop_column("customer_services", "managed_by_source")
    op.drop_column("customer_services", "source_rate_code")
    op.drop_column("customer_services", "source_rate_id")
    op.drop_column("customer_services", "source_system")
