from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.customer_models import Customer, CustomerContact, CustomerLocation, ExternalRecordLink
from app.security.context import SecurityContext
from app.services.customer_directory import CustomerDirectory
from app.services.platypus_customer_sync import PlatypusCustomerSync

CUSTOMER_HEADERS = {
    "Customer Name", "Parent Account Name", "Account Number", "Primary Contact First Name",
    "Primary Contact Last Name", "Primary Contact Phone 1", "Primary Contact Email 1",
    "Primary Contact Job Title", "Primary Service Location Name",
    "Primary Service Location Address 1", "Primary Service Location Address 2",
    "Primary Service Location City", "Primary Service Location State/Province",
    "Primary Service Location Zip/Postal Code", "Secondary Contact First Name",
    "Secondary Contact Last Name", "Secondary Contact Phone 1", "Secondary Contact Email 1",
    "Secondary Contact Job Title", "Secondary Contact Department", "Tags", "Assigned Contract",
    "Is Taxable", "Business Number", "Source", "PlatCustomerID",
}

LOCATION_HEADERS = {
    "Is Active", "Customer Name", "Customer Parent Name", "Primary Location", "Billing Location",
    "Location Name", "Address 1", "Address 2", "City", "State/Province", "Zip/Postal Code",
    "Is Gated Property", "Gate Access Instructions",
}


def _clean_header(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _text(value: Any) -> str:
    value = str(value or "").strip()
    return "" if value.upper() in {"NULL", "NONE", "N/A"} else value


def _bool(value: Any) -> bool:
    return _text(value).lower() in {"1", "true", "yes", "y", "active", "x"}


def _phone(value: Any) -> str:
    digits = re.sub(r"\D", "", _text(value))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def _email(value: Any) -> str:
    return _text(value).lower()


def _name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _text(value).lower()).strip()


_STREET_WORDS = {
    "street": "st", "st.": "st", "road": "rd", "rd.": "rd", "avenue": "ave", "ave.": "ave",
    "boulevard": "blvd", "blvd.": "blvd", "drive": "dr", "dr.": "dr", "lane": "ln", "ln.": "ln",
    "court": "ct", "ct.": "ct", "highway": "hwy", "hwy.": "hwy", "saint": "st",
}


def _address_key(row: dict[str, Any], *, prefix: str = "") -> str:
    def pick(name: str) -> str:
        return _text(row.get(f"{prefix}{name}"))
    street = f"{pick('Address 1')} {pick('Address 2')}".lower()
    tokens = [re.sub(r"[^a-z0-9]", "", _STREET_WORDS.get(tok, tok)) for tok in street.split()]
    tokens = [t for t in tokens if t]
    city = re.sub(r"[^a-z0-9]", "", pick("City").lower())
    state = re.sub(r"[^a-z0-9]", "", pick("State/Province").lower())
    postal = re.sub(r"\D", "", pick("Zip/Postal Code"))[:5]
    return "|".join([" ".join(tokens), city, state, postal])


def _location_key(location: CustomerLocation) -> str:
    return _address_key({
        "Address 1": location.address_line_1,
        "Address 2": location.address_line_2,
        "City": location.city,
        "State/Province": location.state,
        "Zip/Postal Code": location.postal_code,
    })


def parse_csv_bytes(content: bytes) -> tuple[list[dict[str, str]], list[str]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    raw_headers = reader.fieldnames or []
    headers = [_clean_header(h) for h in raw_headers if _clean_header(h)]
    rows: list[dict[str, str]] = []
    for raw in reader:
        row: dict[str, str] = {}
        for key, value in raw.items():
            clean = _clean_header(key or "")
            if clean:
                row[clean] = _text(value)
        if any(row.values()):
            rows.append(row)
    return rows, headers


@dataclass
class ImportPreview:
    token: str
    customer_rows: int = 0
    location_rows: int = 0
    matched_platypus: int = 0
    matched_service_fusion: int = 0
    matched_contact: int = 0
    platypus_no_nop: int = 0
    new_customers: int = 0
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    invalid: list[dict[str, Any]] = field(default_factory=list)
    customer_decisions: list[dict[str, Any]] = field(default_factory=list)
    location_summary: dict[str, int] = field(default_factory=lambda: {"matched": 0, "ambiguous": 0, "orphan": 0})

    @property
    def safe_customer_rows(self) -> int:
        return self.customer_rows - len(self.conflicts) - len(self.invalid)


class ServiceFusionImportService:
    def __init__(self, db: Session, context: SecurityContext, directory: CustomerDirectory | None = None):
        self.db = db
        self.context = context
        self.directory = directory or CustomerDirectory()

    def preview(self, customer_rows: list[dict[str, str]], location_rows: list[dict[str, str]], token: str) -> ImportPreview:
        preview = ImportPreview(token=token, customer_rows=len(customer_rows), location_rows=len(location_rows))
        customers = list(self.db.scalars(select(Customer).options(
            selectinload(Customer.contacts), selectinload(Customer.locations), selectinload(Customer.external_links)
        )).unique())
        by_plat: dict[str, Customer] = {}
        by_sf: dict[str, Customer] = {}
        phone_index: dict[str, set[int]] = {}
        email_index: dict[str, set[int]] = {}
        by_id = {c.id: c for c in customers}
        for customer in customers:
            for link in customer.external_links:
                system = link.system_name.lower()
                if system == "platypus" and link.record_type.lower() == "customer":
                    by_plat[_text(link.external_id)] = customer
                elif system == "service_fusion" and link.record_type.lower() == "customer":
                    by_sf[_text(link.external_id)] = customer
            emails = {_email(customer.billing_email)} if customer.billing_email else set()
            phones = {_phone(customer.billing_phone)} if customer.billing_phone else set()
            for contact in customer.contacts:
                if contact.email: emails.add(_email(contact.email))
                for p in (contact.office_phone, contact.mobile_phone):
                    if _phone(p): phones.add(_phone(p))
            for value in emails:
                if value: email_index.setdefault(value, set()).add(customer.id)
            for value in phones:
                if value: phone_index.setdefault(value, set()).add(customer.id)

        customer_name_map: dict[tuple[str, str], list[int]] = {}
        for idx, row in enumerate(customer_rows):
            display_name = _text(row.get("Customer Name"))
            if not display_name:
                preview.invalid.append({"row": idx + 2, "reason": "Customer Name is blank."})
                continue
            plat_id = _text(row.get("PlatCustomerID"))
            sf_id = _text(row.get("Account Number"))
            plat_customer = by_plat.get(plat_id) if plat_id else None
            sf_customer = by_sf.get(sf_id) if sf_id else None
            if plat_customer and sf_customer and plat_customer.id != sf_customer.id:
                preview.conflicts.append({"row": idx + 2, "customer": display_name, "reason": f"PlatCustomerID {plat_id} and Service Fusion account {sf_id} point to different NOP customers."})
                continue
            matched = plat_customer or sf_customer
            match_type = "platypus" if plat_customer else ("service_fusion" if sf_customer else "")
            if matched is None:
                candidate_ids: set[int] = set()
                email = _email(row.get("Primary Contact Email 1"))
                phone = _phone(row.get("Primary Contact Phone 1"))
                if email: candidate_ids |= email_index.get(email, set())
                if phone: candidate_ids |= phone_index.get(phone, set())
                if len(candidate_ids) == 1:
                    matched = by_id[next(iter(candidate_ids))]
                    match_type = "contact"
                elif len(candidate_ids) > 1:
                    preview.conflicts.append({"row": idx + 2, "customer": display_name, "reason": "Phone/email matches more than one NOP customer."})
                    continue
            if matched:
                if match_type == "platypus": preview.matched_platypus += 1
                elif match_type == "service_fusion": preview.matched_service_fusion += 1
                else: preview.matched_contact += 1
                action = "update"
                local_id = matched.id
                if plat_id and matched.platypus_link and _text(row.get("Primary Service Location Address 1")):
                    staged_key = _address_key({
                        "Address 1": row.get("Primary Service Location Address 1"),
                        "Address 2": row.get("Primary Service Location Address 2"),
                        "City": row.get("Primary Service Location City"),
                        "State/Province": row.get("Primary Service Location State/Province"),
                        "Zip/Postal Code": row.get("Primary Service Location Zip/Postal Code"),
                    })
                    live_service = next((loc for loc in matched.locations if loc.name.lower() == "service address"), None)
                    if live_service and staged_key and _location_key(live_service) != staged_key:
                        preview.conflicts.append({"row": idx + 2, "customer": display_name, "reason": "Service Fusion primary service location does not match the current Platypus Service Address."})
                        continue
            elif plat_id:
                preview.platypus_no_nop += 1
                action = "sync_platypus"
                local_id = None
            else:
                preview.new_customers += 1
                action = "create"
                local_id = None
            decision = {"row_index": idx, "row_number": idx + 2, "name": display_name, "action": action, "local_id": local_id, "plat_id": plat_id, "sf_id": sf_id}
            preview.customer_decisions.append(decision)
            key = (_name(display_name), _name(row.get("Parent Account Name")))
            customer_name_map.setdefault(key, []).append(idx)

        # Location export has no stable customer id, so associate to the staged customer export by name+parent.
        for idx, row in enumerate(location_rows):
            key = (_name(row.get("Customer Name")), _name(row.get("Customer Parent Name")))
            candidates = customer_name_map.get(key, [])
            if len(candidates) == 1:
                preview.location_summary["matched"] += 1
            elif len(candidates) > 1:
                preview.location_summary["ambiguous"] += 1
                preview.conflicts.append({"row": idx + 2, "customer": row.get("Customer Name"), "reason": "Location matches multiple Service Fusion customer rows by name/parent."})
            else:
                preview.location_summary["orphan"] += 1
        return preview

    async def commit(self, customer_rows: list[dict[str, str]], location_rows: list[dict[str, str]], preview: ImportPreview) -> dict[str, int]:
        stats = {"created": 0, "updated": 0, "platypus_synced": 0, "contacts": 0, "locations": 0, "locations_merged": 0, "locations_skipped": 0, "conflicts_skipped": len(preview.conflicts), "invalid_skipped": len(preview.invalid)}
        blocked_customer_rows = {int(item["row"]) - 2 for item in preview.conflicts if item.get("row") and item.get("reason", "").lower().find("location") < 0}
        blocked_customer_rows |= {int(item["row"]) - 2 for item in preview.invalid if item.get("row")}

        # Existing indices are refreshed as rows are committed.
        def get_links(system: str) -> dict[str, Customer]:
            links = list(self.db.scalars(select(ExternalRecordLink).where(
                ExternalRecordLink.system_name == system, ExternalRecordLink.record_type == "customer"
            )).unique())
            return {_text(link.external_id): link.customer for link in links}
        by_plat = get_links("platypus")
        by_sf = get_links("service_fusion")
        row_customers: dict[int, Customer] = {}

        for idx, row in enumerate(customer_rows):
            if idx in blocked_customer_rows or not _text(row.get("Customer Name")):
                continue
            plat_id = _text(row.get("PlatCustomerID"))
            sf_id = _text(row.get("Account Number"))
            customer = by_plat.get(plat_id) if plat_id else None
            if customer is None and sf_id:
                customer = by_sf.get(sf_id)
            if customer is None and plat_id:
                try:
                    profile = await self.directory.get(plat_id)
                    customer = PlatypusCustomerSync(self.db, self.context).sync(profile)
                    self.db.flush()
                    by_plat[plat_id] = customer
                    stats["platypus_synced"] += 1
                except Exception:
                    stats["conflicts_skipped"] += 1
                    continue
            if customer is None:
                customer = self._find_unique_contact_match(row)
            if customer is None:
                customer = self._create_customer(row)
                stats["created"] += 1
            else:
                stats["updated"] += 1
            row_customers[idx] = customer
            self._upsert_service_fusion_link(customer, row)
            stats["contacts"] += self._upsert_contacts(customer, row)
            self._upsert_primary_location(customer, row, stats)
            self.db.flush()

        # Associate location export rows to customer import rows by normalized customer+parent name.
        name_map: dict[tuple[str, str], list[int]] = {}
        for idx, row in enumerate(customer_rows):
            if idx not in row_customers:
                continue
            key = (_name(row.get("Customer Name")), _name(row.get("Parent Account Name")))
            name_map.setdefault(key, []).append(idx)
        for row in location_rows:
            key = (_name(row.get("Customer Name")), _name(row.get("Customer Parent Name")))
            candidates = name_map.get(key, [])
            if len(candidates) != 1:
                stats["locations_skipped"] += 1
                continue
            self._upsert_location(row_customers[candidates[0]], row, stats)

        self.db.flush()
        return stats

    def _find_unique_contact_match(self, row: dict[str, str]) -> Customer | None:
        email = _email(row.get("Primary Contact Email 1"))
        phone = _phone(row.get("Primary Contact Phone 1"))
        customers = list(self.db.scalars(select(Customer).options(selectinload(Customer.contacts))).unique())
        matches = []
        for customer in customers:
            values_email = {_email(customer.billing_email)} if customer.billing_email else set()
            values_phone = {_phone(customer.billing_phone)} if customer.billing_phone else set()
            for c in customer.contacts:
                if c.email: values_email.add(_email(c.email))
                for p in (c.office_phone, c.mobile_phone):
                    if _phone(p): values_phone.add(_phone(p))
            if (email and email in values_email) or (phone and phone in values_phone):
                matches.append(customer)
        return matches[0] if len(matches) == 1 else None

    def _create_customer(self, row: dict[str, str]) -> Customer:
        from app.services.platypus_customer_sync import _staff_owner
        owner = _staff_owner(self.db, self.context)
        customer = Customer(
            customer_number=f"SF-PENDING-{id(row)}"[:32], name=_text(row.get("Customer Name")),
            customer_type="direct", status="active", source_type="imported",
            owner_organization_id=owner.id, servicing_organization_id=None,
            billing_method="direct", billing_email=_email(row.get("Primary Contact Email 1")),
            billing_phone=_text(row.get("Primary Contact Phone 1")),
            tax_exempt=not _bool(row.get("Is Taxable")),
            notes="Imported from Service Fusion.", created_by_user_id=self.context.user_id, updated_by_user_id=self.context.user_id,
        )
        self.db.add(customer); self.db.flush()
        customer.customer_number = f"SF-{customer.id:06d}"
        return customer

    def _upsert_service_fusion_link(self, customer: Customer, row: dict[str, str]) -> None:
        sf_id = _text(row.get("Account Number"))
        if not sf_id:
            return
        link = self.db.scalar(select(ExternalRecordLink).where(
            ExternalRecordLink.system_name == "service_fusion", ExternalRecordLink.record_type == "customer",
            ExternalRecordLink.external_id == sf_id,
        ))
        now = datetime.now(timezone.utc)
        if link is None:
            link = ExternalRecordLink(customer_id=customer.id, system_name="service_fusion", record_type="customer", external_id=sf_id, link_status="imported")
            self.db.add(link)
        elif link.customer_id != customer.id:
            raise ValueError(f"Service Fusion account {sf_id} is already linked to another NOP customer.")
        link.external_account_number = sf_id
        link.link_status = "imported"
        link.last_seen_at = now; link.last_synced_at = now
        link.source_snapshot_json = json.dumps(row, sort_keys=True)

    def _upsert_contacts(self, customer: Customer, row: dict[str, str]) -> int:
        count = 0
        specs = [
            ("Primary", "Primary Contact First Name", "Primary Contact Last Name", "Primary Contact Phone 1", "Primary Contact Email 1", "Primary Contact Job Title"),
            ("Secondary", "Secondary Contact First Name", "Secondary Contact Last Name", "Secondary Contact Phone 1", "Secondary Contact Email 1", "Secondary Contact Job Title"),
        ]
        for label, fk, lk, pk, ek, tk in specs:
            first, last, phone, email = _text(row.get(fk)), _text(row.get(lk)), _text(row.get(pk)), _email(row.get(ek))
            if not any((first, last, phone, email)):
                continue
            contact = next((c for c in customer.contacts if (email and _email(c.email) == email) or (phone and _phone(c.office_phone) == _phone(phone))), None)
            if contact is None:
                contact = CustomerContact(customer_id=customer.id, first_name=first or label, last_name=last)
                self.db.add(contact); customer.contacts.append(contact)
            contact.first_name = first or contact.first_name; contact.last_name = last or contact.last_name
            contact.office_phone = phone; contact.email = email; contact.job_title = _text(row.get(tk))
            contact.active = True; contact.authorized_for_support = True; contact.is_primary = label == "Primary"
            if label == "Secondary" and _text(row.get("Secondary Contact Department")):
                contact.notes = f"Department: {_text(row.get('Secondary Contact Department'))}"
            count += 1
        if customer.contacts and not any(c.is_primary for c in customer.contacts):
            customer.contacts[0].is_primary = True
        return count

    def _upsert_primary_location(self, customer: Customer, row: dict[str, str], stats: dict[str, int]) -> None:
        addr = {
            "Address 1": row.get("Primary Service Location Address 1"), "Address 2": row.get("Primary Service Location Address 2"),
            "City": row.get("Primary Service Location City"), "State/Province": row.get("Primary Service Location State/Province"),
            "Zip/Postal Code": row.get("Primary Service Location Zip/Postal Code"),
        }
        if not _text(addr["Address 1"]):
            return
        target_key = _address_key(addr)
        existing = next((loc for loc in customer.locations if _location_key(loc) == target_key), None)
        service_location = next((loc for loc in customer.locations if loc.name.lower() == "service address"), None)
        if service_location and existing is None:
            # Platypus-linked customer's Service Address and SF primary service location must represent one location.
            if customer.platypus_link:
                # Do not create a duplicate or silently replace a mismatched live billing-system address.
                stats["locations_skipped"] += 1
                return
        if existing is None:
            existing = CustomerLocation(customer_id=customer.id, name=_text(row.get("Primary Service Location Name")) or "Primary Service Location", address_line_1=_text(addr["Address 1"]), city=_text(addr["City"]) or "Unknown", state=_text(addr["State/Province"]) or "SC", postal_code=_text(addr["Zip/Postal Code"]) or "00000")
            self.db.add(existing); customer.locations.append(existing); stats["locations"] += 1
        else:
            stats["locations_merged"] += 1
        existing.name = _text(row.get("Primary Service Location Name")) or existing.name
        existing.address_line_1 = _text(addr["Address 1"]); existing.address_line_2 = _text(addr["Address 2"])
        existing.city = _text(addr["City"]) or existing.city; existing.state = _text(addr["State/Province"]) or existing.state
        existing.postal_code = _text(addr["Zip/Postal Code"]) or existing.postal_code; existing.active = True; existing.is_primary = True
        for loc in customer.locations:
            if loc is not existing: loc.is_primary = False

    def _upsert_location(self, customer: Customer, row: dict[str, str], stats: dict[str, int]) -> None:
        if not _text(row.get("Address 1")):
            stats["locations_skipped"] += 1; return
        target_key = _address_key(row)
        existing = next((loc for loc in customer.locations if _location_key(loc) == target_key), None)
        is_primary = _bool(row.get("Primary Location"))
        if existing is None and is_primary and customer.platypus_link:
            live_service = next((loc for loc in customer.locations if loc.name.lower() == "service address"), None)
            if live_service and _location_key(live_service) != target_key:
                stats["locations_skipped"] += 1; return
        if existing is None:
            existing = CustomerLocation(customer_id=customer.id, name=_text(row.get("Location Name")) or "Service Location", address_line_1=_text(row.get("Address 1")), city=_text(row.get("City")) or "Unknown", state=_text(row.get("State/Province")) or "SC", postal_code=_text(row.get("Zip/Postal Code")) or "00000")
            self.db.add(existing); customer.locations.append(existing); stats["locations"] += 1
        else:
            stats["locations_merged"] += 1
        existing.address_line_1 = _text(row.get("Address 1")); existing.address_line_2 = _text(row.get("Address 2"))
        existing.city = _text(row.get("City")) or existing.city; existing.state = _text(row.get("State/Province")) or existing.state; existing.postal_code = _text(row.get("Zip/Postal Code")) or existing.postal_code
        existing.active = _bool(row.get("Is Active"))
        if _text(row.get("Location Name")): existing.name = _text(row.get("Location Name"))
        gate = _text(row.get("Gate Access Instructions"))
        gated = _bool(row.get("Is Gated Property"))
        existing.access_instructions = (f"Gated property. {gate}" if gated else gate).strip()
        if is_primary:
            existing.is_primary = True
            for loc in customer.locations:
                if loc is not existing: loc.is_primary = False
        if _bool(row.get("Billing Location")):
            marker = "Service Fusion billing location"
            if marker.lower() not in existing.dispatch_notes.lower():
                existing.dispatch_notes = (existing.dispatch_notes + "\n" + marker).strip()
