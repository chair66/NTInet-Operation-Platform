"""Seed a fictitious read-only Platypus rate and service cache.

Run from the NOP project directory:

    python -m app.database.seed_demo_platypus

The records are intentionally fictional. Stable source IDs model the Platypus
RGID/CRID/SVC_ID/DATA_ID hierarchy without connecting to or modifying Platypus.
The seed is idempotent: existing mock records are updated, not duplicated.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json

from sqlalchemy import select

from app.database import SessionLocal
from app.database import customer_models
from app.database.customer_models import Customer, CustomerService, ExternalRecordLink


SOURCE_SYSTEM = "platypus_demo"


@dataclass(frozen=True, slots=True)
class DemoRate:
    rgid: str
    code: str
    source_name: str
    service_type: str
    service_name: str
    module_slug: str
    quantity_mode: str


@dataclass(frozen=True, slots=True)
class DemoAssignment:
    customer_name: str
    rgid: str
    crid: str
    svc_id: str
    data_id: str
    identifier: str
    quantity: int
    monthly_price: Decimal
    billing_responsibility: str = "customer"
    service_type: str = ""
    service_name: str = ""


RATES = (
    DemoRate("11001", "DEMO-FIBER-100", "Demo Fiber 100/100 Mbps", "internet",
             "NTInet Fiber 100/100", "support-tickets", "rate_quantity"),
    DemoRate("11002", "DEMO-FIBER-500", "Demo Business Fiber 500/500 Mbps", "internet",
             "NTInet Business Fiber 500/500", "support-tickets", "rate_quantity"),
    DemoRate("11003", "DEMO-FIBER-1000", "Demo Business Fiber 1 Gbps", "internet",
             "NTInet Business Fiber 1 Gbps", "support-tickets", "rate_quantity"),
    DemoRate("21001", "DEMO-VOICE-USER", "Demo DigiCloud Hosted Voice User", "phone",
             "DigiCloud PBX User", "digicloud", "rate_quantity"),
    DemoRate("21002", "DEMO-VOICE-TRUNK", "Demo DigiCloud SIP Trunk", "phone",
             "DigiCloud SIP Trunk", "digicloud", "rate_quantity"),
    DemoRate("31001", "DEMO-PLUME-WIFI", "Demo Plume Managed Wi-Fi", "plume_wifi",
             "Plume Managed Wi-Fi", "plume", "rate_quantity"),
    DemoRate("31002", "DEMO-PLUME-POD", "Demo Plume Wi-Fi Pod", "plume_wifi",
             "Plume Wi-Fi Pod", "plume", "rate_quantity"),
)


ASSIGNMENTS = (
    DemoAssignment("Carolina Demo Manufacturing", "11002", "51001", "101", "71001",
                   "DEMO-FIBER-001", 1, Decimal("149.95")),
    DemoAssignment("Carolina Demo Manufacturing", "21001", "51002", "201", "71002",
                   "DEMO-VOICE-MFG", 12, Decimal("24.95")),
    DemoAssignment("Carolina Demo Manufacturing", "31001", "51003", "301", "71003",
                   "DEMO-PLUME-MFG", 1, Decimal("19.95")),
    DemoAssignment("Carolina Demo Manufacturing", "31001", "51003", "302", "71004",
                   "DEMO-PODS-MFG", 4, Decimal("7.00"), service_type="plume_pod",
                   service_name="Plume Wi-Fi Pods"),
    DemoAssignment("Lakeview Dental Group (Demo)", "11001", "52001", "101", "72001",
                   "DEMO-FIBER-DENTAL", 1, Decimal("79.95"), "reseller"),
    DemoAssignment("Lakeview Dental Group (Demo)", "21001", "52002", "201", "72002",
                   "lakeview-demo.example.test", 8, Decimal("24.95"), "reseller"),
    DemoAssignment("Lakeview Dental Group (Demo)", "31001", "52003", "301", "72003",
                   "DEMO-PLUME-DENTAL", 1, Decimal("19.95"), "reseller"),
    DemoAssignment("Lakeview Dental Group (Demo)", "31001", "52003", "302", "72004",
                   "DEMO-PODS-DENTAL", 3, Decimal("7.00"), "reseller", "plume_pod",
                   "Plume Wi-Fi Pods"),
    DemoAssignment("Santee Retail Center (Demo)", "11001", "53001", "101", "73001",
                   "DEMO-FIBER-RETAIL", 1, Decimal("79.95"), "reseller"),
    DemoAssignment("Santee Retail Center (Demo)", "21002", "53002", "202", "73002",
                   "DEMO-TRUNK-RETAIL", 1, Decimal("49.95"), "reseller"),
    DemoAssignment("Santee Retail Center (Demo)", "31001", "53003", "301", "73003",
                   "DEMO-PLUME-RETAIL", 1, Decimal("19.95"), "reseller"),
    DemoAssignment("Santee Retail Center (Demo)", "31001", "53003", "302", "73004",
                   "DEMO-PODS-RETAIL", 2, Decimal("7.00"), "reseller", "plume_pod",
                   "Plume Wi-Fi Pods"),
    DemoAssignment("Regional Support Account (Demo)", "11003", "54001", "101", "74001",
                   "DEMO-FIBER-SUPPORT", 1, Decimal("249.95")),
    DemoAssignment("Regional Support Account (Demo)", "21001", "54002", "201", "74002",
                   "DEMO-VOICE-SUPPORT", 6, Decimal("24.95")),
    DemoAssignment("Regional Support Account (Demo)", "31001", "54003", "301", "74003",
                   "DEMO-PLUME-SUPPORT", 1, Decimal("19.95")),
    DemoAssignment("Regional Support Account (Demo)", "31001", "54003", "302", "74004",
                   "DEMO-PODS-SUPPORT", 3, Decimal("7.00"), service_type="plume_pod",
                   service_name="Plume Wi-Fi Pods"),
)


CUSTOMER_BILLING = {
    "Carolina Demo Manufacturing": {
        "external_id": "DEMO-PLAT-20001", "account": "DEMO-C-0020001",
        "contact_name": "Casey Morgan", "email": "casey.morgan@example.test",
        "phone": "803-555-0102", "address_line_1": "PO Box 820",
        "address_line_2": "", "city": "Orangeburg", "state": "SC", "postal_code": "29116",
    },
    "Lakeview Dental Group (Demo)": {
        "external_id": "DEMO-PLAT-20002", "account": "DEMO-C-0020002",
        "contact_name": "Avery Lewis", "email": "avery.lewis@example.test",
        "phone": "803-555-0104", "address_line_1": "900 Accounts Payable Way",
        "address_line_2": "Suite 20", "city": "Orangeburg", "state": "SC", "postal_code": "29115",
    },
    "Santee Retail Center (Demo)": {
        "external_id": "DEMO-PLAT-20003", "account": "DEMO-C-0020003",
        "contact_name": "Riley Brooks", "email": "riley.brooks@example.test",
        "phone": "803-555-0105", "address_line_1": "PO Box 415",
        "address_line_2": "", "city": "Santee", "state": "SC", "postal_code": "29142",
    },
    "Regional Support Account (Demo)": {
        "external_id": "DEMO-PLAT-10457", "account": "DEMO-C-0010457",
        "contact_name": "Morgan Hayes", "email": "morgan.hayes@example.test",
        "phone": "803-555-0106", "address_line_1": "725 Billing Center Drive",
        "address_line_2": "", "city": "Orangeburg", "state": "SC", "postal_code": "29115",
    },
}


def _set_if_supported(record, **values) -> None:
    for name, value in values.items():
        if hasattr(record, name):
            setattr(record, name, value)


def seed_demo_platypus(db) -> tuple[int, int, int, int]:
    """Return rate-created, rate-updated, service-created, service-updated counts."""
    mapping_model = getattr(customer_models, "ServiceRateMapping", None)
    if mapping_model is None:
        raise RuntimeError(
            "ServiceRateMapping is unavailable. Apply the Platypus service/rate foundation "
            "migration before running this demo seed."
        )

    now = datetime.now(timezone.utc)
    rate_created = rate_updated = service_created = service_updated = 0
    rates_by_id = {item.rgid: item for item in RATES}

    for customer_name, billing in CUSTOMER_BILLING.items():
        customer = db.scalar(select(Customer).where(Customer.name == customer_name))
        if customer is None:
            raise RuntimeError(f"Demo customer {customer_name!r} is missing.")
        customer.billing_email = billing["email"]
        customer.billing_phone = billing["phone"]
        link = db.scalar(select(ExternalRecordLink).where(
            ExternalRecordLink.customer_id == customer.id,
            ExternalRecordLink.system_name == "platypus",
            ExternalRecordLink.record_type == "customer",
        ))
        if link is None:
            link = ExternalRecordLink(
                customer_id=customer.id, system_name="platypus", record_type="customer",
                external_id=billing["external_id"], external_account_number=billing["account"],
                link_status="simulated",
            )
            db.add(link)
        link.external_id = billing["external_id"]
        link.external_account_number = billing["account"]
        link.link_status = "simulated"
        service_location = customer.primary_location
        link.source_snapshot_json = json.dumps({
            "demo": True, "read_only": True,
            "billing": {key: value for key, value in billing.items()
                        if key not in {"external_id", "account"}},
            "primary_service_address": ({
                "address_line_1": service_location.address_line_1,
                "address_line_2": service_location.address_line_2,
                "city": service_location.city, "state": service_location.state,
                "postal_code": service_location.postal_code,
            } if service_location else {}),
        }, sort_keys=True)
        link.last_synced_at = now

    for rate in RATES:
        mapping = db.scalar(select(mapping_model).where(
            mapping_model.source_system == SOURCE_SYSTEM,
            mapping_model.source_rate_id == rate.rgid,
        ))
        if mapping is None:
            mapping = mapping_model(source_system=SOURCE_SYSTEM, source_rate_id=rate.rgid)
            db.add(mapping)
            rate_created += 1
        else:
            rate_updated += 1
        mapping.source_rate_code = rate.code
        mapping.source_rate_name = rate.source_name
        mapping.service_type = rate.service_type
        mapping.service_name = rate.service_name
        mapping.module_slug = rate.module_slug
        mapping.quantity_mode = rate.quantity_mode
        mapping.active = True

    for assignment in ASSIGNMENTS:
        customer = db.scalar(select(Customer).where(Customer.name == assignment.customer_name))
        if customer is None:
            raise RuntimeError(
                f"Demo customer {assignment.customer_name!r} is missing. "
                "Start NOP once with SEED_DEMO_CUSTOMERS=true, then rerun this command."
            )
        rate = rates_by_id[assignment.rgid]
        service_type = assignment.service_type or rate.service_type
        service_name = assignment.service_name or rate.service_name
        service = db.scalar(select(CustomerService).where(
            CustomerService.customer_id == customer.id,
            CustomerService.service_identifier == assignment.identifier,
        ))
        if service is None:
            service = CustomerService(
                customer_id=customer.id,
                location_id=customer.primary_location.id if customer.primary_location else None,
                service_type=service_type,
                service_name=service_name,
                service_identifier=assignment.identifier,
                status="active",
            )
            db.add(service)
            service_created += 1
        else:
            service_updated += 1

        snapshot = {
            "demo": True,
            "read_only": True,
            "source": SOURCE_SYSTEM,
            "rgid": assignment.rgid,
            "crid": assignment.crid,
            "svc_id": assignment.svc_id,
            "data_id": assignment.data_id,
            "frequency": "Monthly",
            "quantity": assignment.quantity,
            "unit_price": str(assignment.monthly_price),
            "rate_name": rate.source_name,
            "rate_quantity": assignment.quantity,
            "next_bill": "2026-09-01",
            "module_slug": rate.module_slug,
            "allowed": assignment.quantity,
            "used": assignment.quantity,
        }
        service.location_id = customer.primary_location.id if customer.primary_location else service.location_id
        service.service_type = service_type
        service.service_name = service_name
        service.status = "active"
        service.quantity = assignment.quantity
        service.recurring_price = assignment.monthly_price
        service.billing_responsibility = assignment.billing_responsibility
        service.notes = "Fictitious Platypus rate/service assignment for NOP demonstrations only."
        _set_if_supported(
            service,
            source_system=SOURCE_SYSTEM,
            source_rate_id=assignment.rgid,
            source_rate_code=rate.code,
            managed_by_source=True,
            last_synced_at=now,
            source_snapshot_json=json.dumps(snapshot, sort_keys=True),
        )

    network_model = getattr(customer_models, "PlumeCustomerNetwork", None)
    pod_model = getattr(customer_models, "PlumePod", None)
    device_model = getattr(customer_models, "PlumeClientDevice", None)
    if network_model and pod_model and device_model:
        plume_customers = sorted({
            assignment.customer_name for assignment in ASSIGNMENTS
            if assignment.rgid == "31001"
        })
        for customer_index, customer_name in enumerate(plume_customers, start=1):
            customer = db.scalar(select(Customer).where(Customer.name == customer_name))
            pod_assignment = next(
                item for item in ASSIGNMENTS
                if item.customer_name == customer_name and item.service_type == "plume_pod"
            )
            network = db.scalar(select(network_model).where(
                network_model.customer_id == customer.id
            ))
            if network is None:
                network = network_model(customer_id=customer.id)
                db.add(network); db.flush()
            network.customer_location_id = customer.primary_location.id if customer.primary_location else None
            network.plume_customer_id = f"DEMO-PLUME-CUST-{customer_index:04d}"
            network.plume_location_id = f"DEMO-PLUME-LOC-{customer_index:04d}"
            network.network_name = f"{customer.name} Managed Wi-Fi"
            network.service_status = "active"
            network.sync_status = "synced"
            network.last_synced_at = now
            network.last_sync_error = ""
            network.source_snapshot_json = json.dumps({"demo": True, "read_only": True})
            for pod_index in range(1, pod_assignment.quantity + 1):
                plume_pod_id = f"DEMO-POD-{customer_index:02d}-{pod_index:02d}"
                pod = db.scalar(select(pod_model).where(
                    pod_model.network_id == network.id,
                    pod_model.plume_pod_id == plume_pod_id,
                ))
                if pod is None:
                    pod = pod_model(network_id=network.id, plume_pod_id=plume_pod_id)
                    db.add(pod)
                pod.name = "Gateway Pod" if pod_index == 1 else f"Wi-Fi Pod {pod_index}"
                pod.serial_number = f"DEMO{customer_index:04d}{pod_index:04d}"
                pod.mac_address = f"02:DE:{customer_index:02X}:00:00:{pod_index:02X}"
                pod.model = "Plume SuperPod AX"
                pod.role = "gateway" if pod_index == 1 else "extender"
                pod.connection_type = "ethernet" if pod_index == 1 else "wireless"
                pod.status = "online"
                pod.firmware_version = "DEMO-6.4.0"
                pod.health_status = "excellent" if pod_index == 1 else "good"
                pod.signal_strength = -42 if pod_index == 1 else -58
                pod.connected_device_count = 2 if pod_index == 1 else 1
                pod.last_seen_at = now; pod.last_synced_at = now
                pod.source_snapshot_json = json.dumps({"demo": True, "read_only": True})
            db.flush()
            gateway = db.scalar(select(pod_model).where(
                pod_model.network_id == network.id, pod_model.role == "gateway"
            ).order_by(pod_model.id))
            for device_index, (name, manufacturer, device_type) in enumerate((
                ("Office Laptop", "Demo Computer Co.", "computer"),
                ("Reception Phone", "Demo Voice Devices", "phone"),
                ("Lobby Tablet", "Demo Mobile Co.", "tablet"),
            ), start=1):
                plume_device_id = f"DEMO-DEVICE-{customer_index:02d}-{device_index:02d}"
                device = db.scalar(select(device_model).where(
                    device_model.network_id == network.id,
                    device_model.plume_device_id == plume_device_id,
                ))
                if device is None:
                    device = device_model(network_id=network.id,
                                          plume_device_id=plume_device_id)
                    db.add(device)
                device.pod_id = gateway.id if gateway else None
                device.name = name; device.manufacturer = manufacturer
                device.device_type = device_type
                device.mac_address = f"02:CA:{customer_index:02X}:00:00:{device_index:02X}"
                device.ipv4_address = f"192.0.2.{10 + device_index}"
                device.connection_type = "wireless"
                device.wifi_band = "5 GHz"
                device.status = "online"
                device.signal_strength = -48 - device_index
                device.link_speed_mbps = 600
                device.last_seen_at = now; device.last_synced_at = now
                device.source_snapshot_json = json.dumps({"demo": True, "read_only": True})

    db.flush()
    return rate_created, rate_updated, service_created, service_updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and report changes, then roll back.")
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            counts = seed_demo_platypus(db)
            if args.dry_run:
                db.rollback()
            else:
                db.commit()
        except Exception:
            db.rollback()
            raise
    action = "Validated" if args.dry_run else "Seeded"
    print(
        f"{action} fictitious Platypus demo data: "
        f"rates {counts[0]} created/{counts[1]} updated; "
        f"services {counts[2]} created/{counts[3]} updated."
    )


if __name__ == "__main__":
    main()
