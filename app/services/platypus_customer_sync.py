from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.customer_models import (
    Customer,
    CustomerContact,
    CustomerLocation,
    CustomerService,
    ExternalRecordLink,
)
from app.database.models import Organization
from app.security.context import SecurityContext


def _text(value) -> str:
    return str(value or "").strip()


def _decimal(value) -> Decimal | None:
    raw = _text(value)
    if not raw or raw.upper() == "NULL":
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _active_status(value: str | None) -> str:
    # GetCustomer commonly returns the one-letter database code while
    # SearchCustomer returns the display values documented by Platypus:
    # Active, Hold, Suspend and Inactive. Normalize both representations.
    raw = _text(value).strip().upper().replace("-", " ").replace("_", " ")
    return {
        "Y": "active",
        "ACTIVE": "active",
        "H": "on_hold",
        "HOLD": "on_hold",
        "ON HOLD": "on_hold",
        "S": "suspended",
        "SUSPEND": "suspended",
        "SUSPENDED": "suspended",
        "N": "inactive",
        "INACTIVE": "inactive",
    }.get(raw, "inactive")


def _service_type(rate: dict, service: dict | None = None) -> str:
    haystack = " ".join(
        _text(value).lower()
        for value in (
            rate.get("rg_name"), rate.get("name"), rate.get("rg_description"),
            (service or {}).get("s_name"), (service or {}).get("s_data"),
        )
    )
    if any(word in haystack for word in ("plume", "managed wi-fi", "managed wifi", "wifi pod", "wi-fi pod")):
        return "plume_wifi"
    if any(word in haystack for word in ("digital voice", "hosted voice", "pbx", "sip trunk", "telephone", "phone")):
        return "phone"
    if any(word in haystack for word in ("nti mobile", "mobile", "cellular", "wireless line")):
        return "mobile"
    if any(word in haystack for word in ("fiber", "broadband", "internet", "dsl", "dial-up", "dialup", "fixed wireless")):
        return "internet"
    if "email" in haystack:
        return "email"
    return "other"


def _staff_owner(db: Session, context: SecurityContext) -> Organization:
    owner = db.scalar(select(Organization).where(Organization.slug == "ntinet"))
    if owner is None:
        owner = db.scalar(
            select(Organization)
            .where(Organization.organization_type == Organization.STAFF_TYPE)
            .order_by(Organization.id.asc())
        )
    return owner or context.organization


def _split_name(value: str) -> tuple[str, str]:
    parts = value.strip().split()
    if not parts:
        return ("Account", "Contact")
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], " ".join(parts[1:]))


class PlatypusCustomerSync:
    """Upsert a Platypus billing account into NOP's customer master.

    NOP owns the durable operational customer identity and history. Platypus remains
    authoritative for billing-specific rate/service data while the external customer
    link lets NOP refresh that data without making Platypus the NOP primary key.
    """

    def __init__(self, db: Session, context: SecurityContext) -> None:
        self.db = db
        self.context = context

    def sync(self, profile: dict) -> Customer:
        now = datetime.now(timezone.utc)
        external_id = _text(profile.get("platypus_customer_id"))
        source = profile.get("customer") or {}
        if not external_id:
            raise ValueError("Platypus customer id is required for NOP synchronization.")

        link = self.db.scalar(
            select(ExternalRecordLink).where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                ExternalRecordLink.external_id == external_id,
            )
        )
        customer = link.customer if link else None
        owner = _staff_owner(self.db, self.context)

        if customer is None:
            customer = Customer(
                customer_number=f"PENDING-PLAT-{external_id}"[:32],
                name=_text(source.get("name")) or f"Platypus Customer {external_id}",
                customer_type="direct",
                status=_active_status(source.get("active")),
                source_type="platypus",
                owner_organization_id=owner.id,
                servicing_organization_id=(None if self.context.is_staff else self.context.organization_id),
                billing_method="direct",
                billing_email=_text(source.get("email")).lower(),
                billing_phone=_text(source.get("phone")),
                notes="Live Platypus customer synchronized for NOP operations.",
                created_by_user_id=self.context.user_id,
                updated_by_user_id=self.context.user_id,
            )
            self.db.add(customer)
            self.db.flush()
            # NOP owns the permanent customer identity. External system ids live in
            # ExternalRecordLink and never become the database primary key.
            customer.customer_number = f"NOP-{customer.id:06d}"
            link = ExternalRecordLink(
                customer_id=customer.id,
                system_name="platypus",
                record_type="customer",
                external_id=external_id,
                external_account_number=_text(source.get("acctnumber")) or external_id,
                link_status="live",
            )
            self.db.add(link)
        else:
            customer.name = _text(source.get("name")) or customer.name
            customer.status = _active_status(source.get("active"))
            customer.source_type = "platypus"
            customer.billing_email = _text(source.get("email")).lower()
            customer.billing_phone = _text(source.get("phone"))
            customer.updated_by_user_id = self.context.user_id
            if not self.context.is_staff and customer.servicing_organization_id is None:
                customer.servicing_organization_id = self.context.organization_id

        link.external_account_number = _text(source.get("acctnumber")) or external_id
        link.link_status = "live"
        link.last_seen_at = now
        link.last_synced_at = now
        link.source_snapshot_json = json.dumps(
            {
                "platypus_customer_id": external_id,
                "customer": source,
                "billing_address": profile.get("billing_address"),
                "service_address": profile.get("service_address"),
            },
            default=str,
            sort_keys=True,
        )

        self._sync_service_fusion_link(customer, source, now)
        self._sync_contact(customer, source, profile.get("phones") or [])
        locations = self._sync_locations(customer, profile)
        self._sync_services(customer, profile, locations.get("service") or locations.get("billing"), now)
        self.db.flush()
        return customer

    @staticmethod
    def _service_fusion_id(source: dict) -> str:
        # Platypus installations often expose the Service Fusion customer id as
        # a custom customer field. Accept common spellings without guessing from
        # unrelated generic source fields.
        preferred = (
            "service_fusion_id", "servicefusionid", "service_fusion_customer_id",
            "servicefusioncustomerid", "service_fusion", "servicefusion",
            "sf_customer_id", "sfcustomerid",
        )
        lowered = {str(key).strip().lower(): value for key, value in source.items()}
        for key in preferred:
            value = _text(lowered.get(key))
            if value:
                return value
        for key, value in lowered.items():
            if "service" in key and "fusion" in key and _text(value):
                return _text(value)
        return ""

    def _sync_service_fusion_link(self, customer: Customer, source: dict, now: datetime) -> None:
        sf_id = self._service_fusion_id(source)
        if not sf_id:
            return
        existing = self.db.scalar(select(ExternalRecordLink).where(
            ExternalRecordLink.system_name == "service_fusion",
            ExternalRecordLink.record_type == "customer",
            ExternalRecordLink.external_id == sf_id,
        ))
        if existing is not None and existing.customer_id != customer.id:
            # Never silently merge two NOP customers because of a conflicting legacy id.
            customer.notes = (customer.notes + f"\nService Fusion link conflict: {sf_id} already belongs to NOP customer {existing.customer_id}.").strip()
            return
        link = existing or self.db.scalar(select(ExternalRecordLink).where(
            ExternalRecordLink.customer_id == customer.id,
            ExternalRecordLink.system_name == "service_fusion",
            ExternalRecordLink.record_type == "customer",
        ))
        if link is None:
            link = ExternalRecordLink(
                customer_id=customer.id, system_name="service_fusion", record_type="customer",
                external_id=sf_id, external_account_number=sf_id, link_status="legacy",
            )
            self.db.add(link)
        else:
            link.external_id = sf_id
            link.external_account_number = sf_id
        link.link_status = "legacy"
        link.last_seen_at = now
        link.last_synced_at = now
        link.notes = "Legacy Service Fusion customer id supplied by Platypus."

    def _sync_contact(self, customer: Customer, source: dict, phones: list[dict]) -> None:
        contact = next((item for item in customer.contacts if item.is_primary), None)
        if contact is None:
            contact = CustomerContact(customer_id=customer.id, first_name="Account", last_name="Contact", is_primary=True)
            self.db.add(contact)
            customer.contacts.append(contact)
        display_name = _text(source.get("attn")) or _text(source.get("name")) or "Account Contact"
        first, last = _split_name(display_name)
        contact.first_name = first
        contact.last_name = last
        contact.email = _text(source.get("email")).lower()

        primary_phone = _text(source.get("phone"))
        mobile_phone = ""
        office_phone = primary_phone
        for phone in phones:
            if not isinstance(phone, dict):
                continue
            number = _text(phone.get("number") or phone.get("phone") or phone.get("phonemasked"))
            if not number:
                continue
            phone_type = _text(
                phone.get("typename") or phone.get("phone_type") or phone.get("type_name")
                or phone.get("name") or phone.get("type")
            ).lower()
            if any(label in phone_type for label in ("cellular", "mobile", "cell", "wireless")):
                if not mobile_phone:
                    mobile_phone = number
            elif not office_phone:
                office_phone = number

        contact.office_phone = office_phone
        contact.mobile_phone = mobile_phone
        contact.active = True
        contact.authorized_for_support = True
        contact.notes = "Live Platypus account contact."

    def _sync_locations(self, customer: Customer, profile: dict) -> dict[str, CustomerLocation]:
        result: dict[str, CustomerLocation] = {}
        for key, label in (("billing", "Billing Address"), ("service", "Service Address")):
            address = profile.get(f"{key}_address")
            if not address:
                continue
            location = next((item for item in customer.locations if item.name == label), None)
            if location is None:
                location = CustomerLocation(
                    customer_id=customer.id,
                    name=label,
                    address_line_1=_text(address.get("addr1")) or "Not provided",
                    city=_text(address.get("city")) or "Unknown",
                    state=_text(address.get("state")) or "SC",
                    postal_code=_text(address.get("zip")) or "00000",
                )
                self.db.add(location)
                customer.locations.append(location)
            location.address_line_1 = _text(address.get("addr1")) or location.address_line_1
            location.address_line_2 = _text(address.get("addr2"))
            location.city = _text(address.get("city")) or location.city
            location.state = _text(address.get("state")) or location.state
            location.postal_code = _text(address.get("zip")) or location.postal_code
            location.country = (_text(address.get("country")) or "US")[:2]
            location.active = True
            location.is_primary = key == "service"
            result[key] = location
        if "service" not in result and "billing" in result:
            result["billing"].is_primary = True
        elif "service" in result:
            for item in customer.locations:
                if item is not result["service"]:
                    item.is_primary = False
        return result

    def _sync_services(self, customer: Customer, profile: dict, location: CustomerLocation | None, now: datetime) -> None:
        existing = [item for item in customer.services if item.source_system == "platypus"]
        by_key = {item.service_identifier: item for item in existing if item.service_identifier}
        touched: set[int] = set()

        for rate in profile.get("rates") or []:
            crid = _text(rate.get("crid") or rate.get("cr_id") or rate.get("CRID"))
            rgid = _text(rate.get("rgid") or rate.get("rg_id") or rate.get("id"))
            rate_name = _text(rate.get("rg_name") or rate.get("name")) or f"Rate {rgid or crid}"
            quantity = int(float(_text(rate.get("cr_quantity") or rate.get("quantity")) or "1"))
            price = _decimal(rate.get("cr_override_price") if _text(rate.get("cr_overridden")).upper() == "Y" else rate.get("price"))
            if price is None:
                price = _decimal(rate.get("fee"))
            rate_services = rate.get("services") or []
            if not rate_services:
                rate_services = [None]

            for svc in rate_services:
                if svc:
                    svc_id = _text(svc.get("s_svc_id"))
                    data_id = _text(svc.get("s_num"))
                    stable = f"svc:{svc_id}:{data_id}"
                    service_data = _text(svc.get("s_data"))
                    service_name = rate_name if not service_data else f"{rate_name} — {service_data}"
                    status = "active" if _text(svc.get("s_active")).upper() == "Y" else "inactive"
                else:
                    stable = f"rate:{crid or rgid}"
                    service_data = ""
                    service_name = rate_name
                    status = "active" if _text(rate.get("rg_active") or "Y").upper() == "Y" else "inactive"

                record = by_key.get(stable)
                if record is None:
                    record = CustomerService(customer_id=customer.id, service_identifier=stable)
                    self.db.add(record)
                    customer.services.append(record)
                    by_key[stable] = record
                record.location_id = location.id if location and location.id else record.location_id
                record.service_type = _service_type(rate, svc)
                record.service_name = service_name[:160]
                record.status = status
                record.quantity = max(1, quantity)
                record.recurring_price = price
                record.billing_responsibility = "customer"
                record.source_system = "platypus"
                record.source_rate_id = crid
                record.source_rate_code = rgid
                record.managed_by_source = True
                record.last_synced_at = now
                record.source_snapshot_json = json.dumps({"rate": rate, "service": svc}, default=str, sort_keys=True)
                record.notes = "Live Platypus rate/service mapping."
                if record.id:
                    touched.add(record.id)

        self.db.flush()
        touched.update(item.id for item in customer.services if item.source_system == "platypus" and item.last_synced_at == now)
        for record in existing:
            if record.id not in touched:
                # Keep the row for historical Ticket/Job/Estimate foreign keys, but
                # do not offer a removed Platypus service as a current selection.
                record.status = "inactive"
                record.last_synced_at = now
