from __future__ import annotations
from datetime import datetime, timezone
import re
from fastapi import HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.database.models import DigiCloudDomain, DigiCloudOrganizationSettings, DigiCloudPhoneNumber, DigiCloudUserHiddenDomain, Organization
from app.providers.netsapiens import NetSapiensDomains, NetSapiensError, NetSapiensPhoneNumbers
from app.security.context import SecurityContext
from app.services.audit_service import AuditService


def normalize_tn(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"): digits = digits[1:]
    if len(digits) != 10: raise HTTPException(400, "Phone number must contain 10 digits")
    return digits

class DigiCloudService:
    def __init__(self, db: Session, context: SecurityContext, request: Request | None = None):
        self.db, self.context, self.request = db, context, request
        self.provider = NetSapiensDomains()
        self.phone_number_provider = NetSapiensPhoneNumbers(self.provider.client)

    @property
    def _specialist_scoped(self) -> bool:
        return "DigiCloud & Porting Specialist" in self.context.role_names and not self.context.is_superuser

    @property
    def _organization_scoped(self) -> bool:
        return (not self.context.is_staff) or self._specialist_scoped

    def _org_filter(self, model):
        return model.organization_id == self.context.organization_id if self._organization_scoped else True

    def _hidden_domains(self) -> set[str]:
        if self.context.is_superuser:
            return set()
        return {
            str(name).strip().lower().rstrip(".")
            for name in self.db.scalars(
                select(DigiCloudUserHiddenDomain.domain_name).where(
                    DigiCloudUserHiddenDomain.user_id == self.context.user_id
                )
            ).all()
            if str(name or "").strip()
        }

    def _require_domain_visible(self, domain_name: str) -> None:
        normalized = str(domain_name or "").strip().lower().rstrip(".")
        if normalized and normalized in self._hidden_domains():
            raise HTTPException(403, "This DigiCloud domain has been hidden from your account")

    def organizations(self):
        if self._organization_scoped: return [self.context.organization]
        return list(self.db.scalars(select(Organization).where(Organization.active.is_(True), Organization.deleted_at.is_(None)).order_by(Organization.name)))

    def settings_for(self, organization_id: int, create: bool = True):
        if self._organization_scoped and organization_id != self.context.organization_id: raise HTTPException(403, "Organization access denied")
        obj = self.db.scalar(select(DigiCloudOrganizationSettings).where(DigiCloudOrganizationSettings.organization_id == organization_id))
        if obj is None and create:
            obj = DigiCloudOrganizationSettings(organization_id=organization_id)
            self.db.add(obj); self.db.flush()
        return obj

    def save_settings(self, organization_id: int, **values):
        if not (self.context.is_staff and self.context.is_superuser): raise HTTPException(403, "Platform Admin access required")
        obj = self.settings_for(organization_id)
        for key, value in values.items(): setattr(obj, key, value)
        obj.updated_by_user_id = self.context.user.id
        AuditService(self.db, self.request, self.context).record("digicloud.settings.update", "organization", organization_id, "Updated DigiCloud defaults", module="digicloud", organization_id=organization_id)
        return obj

    def list_domains(self, q: str = ""):
        stmt = select(DigiCloudDomain).where(DigiCloudDomain.deleted_at.is_(None))
        if self._organization_scoped: stmt = stmt.where(DigiCloudDomain.organization_id == self.context.organization_id)
        hidden = self._hidden_domains()
        if hidden: stmt = stmt.where(~DigiCloudDomain.domain_name.in_(hidden))
        if q.strip():
            term=f"%{q.strip().lower()}%"; stmt=stmt.where(or_(func.lower(DigiCloudDomain.domain_name).like(term), func.lower(DigiCloudDomain.description).like(term)))
        return list(self.db.scalars(stmt.order_by(DigiCloudDomain.domain_name)).unique())


    @staticmethod
    def _remote_value(row: dict, *keys, default=None):
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return default

    @staticmethod
    def _remote_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}

    def sync_domains(self):
        """Import and refresh domains from NetSapiens for accessible organizations."""
        if not self.provider.client.configured:
            raise HTTPException(400, "NetSapiens API is not configured in .env")

        organizations = self.organizations()
        summary = {"organizations": 0, "received": 0, "created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
        errors: list[str] = []

        for organization in organizations:
            settings = self.settings_for(organization.id, create=False)
            reseller = (settings.netsapiens_reseller if settings else "").strip()
            if not reseller:
                summary["skipped"] += 1
                continue

            summary["organizations"] += 1
            try:
                remote_domains = self.provider.list(reseller)
            except NetSapiensError as exc:
                errors.append(f"{organization.name}: {exc}")
                continue

            summary["received"] += len(remote_domains)
            for row in remote_domains:
                name = str(self._remote_value(row, "domain", "domain_name", "name", default="")).strip().lower()
                if not name:
                    summary["skipped"] += 1
                    continue

                obj = self.db.scalar(
                    select(DigiCloudDomain).where(
                        DigiCloudDomain.domain_name == name,
                        DigiCloudDomain.deleted_at.is_(None),
                    )
                )

                if obj is not None and obj.organization_id != organization.id:
                    summary["skipped"] += 1
                    errors.append(f"{name}: already belongs to another organization")
                    continue

                created = obj is None
                if created:
                    obj = DigiCloudDomain(
                        organization_id=organization.id,
                        domain_name=name,
                        area_code=settings.default_area_code,
                        time_zone=settings.default_time_zone,
                        max_calls=settings.default_max_calls,
                        max_offnet_calls=settings.default_max_offnet_calls,
                        recording_enabled=settings.default_recording_enabled,
                        transcription_enabled=settings.default_transcription_enabled,
                        transcription_provider=settings.default_transcription_provider,
                        email_from=settings.default_email_from,
                    )
                    self.db.add(obj)

                before = (
                    obj.description, obj.caller_id_name, obj.caller_id_number,
                    obj.emergency_caller_id, obj.area_code, obj.time_zone,
                    obj.max_calls, obj.max_offnet_calls, obj.recording_enabled,
                    obj.transcription_enabled, obj.transcription_provider,
                    obj.email_from, obj.provider_domain_id, obj.status, obj.last_error,
                )

                obj.description = str(self._remote_value(row, "description", "domain_description", default=obj.description) or "")
                obj.caller_id_name = str(self._remote_value(row, "caller_id_name", "callerIdName", default=obj.caller_id_name) or "")
                obj.caller_id_number = str(self._remote_value(row, "caller_id_number", "callerIdNumber", default=obj.caller_id_number) or "")
                obj.emergency_caller_id = str(self._remote_value(row, "emergency_caller_id", "emergencyCallerId", "emergency_number", default=obj.emergency_caller_id) or "")
                obj.area_code = str(self._remote_value(row, "area_code", "areaCode", default=obj.area_code) or obj.area_code)
                obj.time_zone = str(self._remote_value(row, "time_zone", "timezone", "timeZone", default=obj.time_zone) or obj.time_zone)

                max_calls = self._remote_value(row, "max_calls", "maxCalls")
                max_offnet = self._remote_value(row, "max_offnet_calls", "maxOffnetCalls", "max_off_net_calls")
                try:
                    if max_calls is not None: obj.max_calls = int(max_calls)
                except (TypeError, ValueError):
                    pass
                try:
                    if max_offnet is not None: obj.max_offnet_calls = int(max_offnet)
                except (TypeError, ValueError):
                    pass

                obj.recording_enabled = self._remote_bool(
                    self._remote_value(row, "recording", "recording_enabled", "recordingEnabled"),
                    obj.recording_enabled,
                )
                obj.transcription_enabled = self._remote_bool(
                    self._remote_value(row, "transcription", "transcription_enabled", "transcriptionEnabled"),
                    obj.transcription_enabled,
                )
                obj.transcription_provider = str(self._remote_value(row, "transcription_provider", "transcriptionProvider", default=obj.transcription_provider) or obj.transcription_provider)
                obj.email_from = str(self._remote_value(row, "email_from", "emailFrom", default=obj.email_from) or obj.email_from)
                obj.provider_domain_id = str(self._remote_value(row, "id", "domain_id", "domainId", "domain", default=obj.provider_domain_id or name))

                remote_status = str(self._remote_value(row, "status", "active", default="active")).strip().lower()
                if remote_status in {"false", "0", "inactive", "disabled", "suspended"}:
                    obj.status = "inactive"
                else:
                    obj.status = "active"
                obj.last_error = ""

                after = (
                    obj.description, obj.caller_id_name, obj.caller_id_number,
                    obj.emergency_caller_id, obj.area_code, obj.time_zone,
                    obj.max_calls, obj.max_offnet_calls, obj.recording_enabled,
                    obj.transcription_enabled, obj.transcription_provider,
                    obj.email_from, obj.provider_domain_id, obj.status, obj.last_error,
                )

                if created:
                    summary["created"] += 1
                elif before != after:
                    summary["updated"] += 1
                else:
                    summary["unchanged"] += 1

        if summary["organizations"] == 0:
            raise HTTPException(400, "No accessible organization has a NetSapiens reseller configured")
        if errors and summary["received"] == 0:
            raise HTTPException(502, "; ".join(errors[:3]))

        self.db.flush()
        detail = (
            f"NetSapiens domain sync: {summary['created']} created, "
            f"{summary['updated']} updated, {summary['unchanged']} unchanged, "
            f"{summary['skipped']} skipped"
        )
        if errors:
            detail += f", {len(errors)} warning(s)"
        AuditService(self.db, self.request, self.context).record(
            "digicloud.domain.sync", "domain", None, detail,
            module="digicloud", organization_id=self.context.organization_id,
        )
        summary["errors"] = errors
        return summary


    def domain_assignment_conflicts(self):
        """Return domains whose live NetSapiens reseller differs from local ownership."""
        if not (self.context.is_staff and self.context.is_superuser):
            raise HTTPException(403, "Platform Admin access required")
        if not self.provider.client.configured:
            raise HTTPException(400, "NetSapiens API is not configured in .env")

        conflicts = []
        warnings = []
        seen = set()
        for organization in self.organizations():
            settings = self.settings_for(organization.id, create=False)
            reseller = (settings.netsapiens_reseller if settings else "").strip()
            if not reseller:
                continue
            try:
                rows = self.provider.list(reseller)
            except NetSapiensError as exc:
                warnings.append(f"{organization.name}: {exc}")
                continue
            for row in rows:
                name = str(self._remote_value(row, "domain", "domain_name", "name", default="")).strip().lower()
                if not name:
                    continue
                local = self.db.scalar(select(DigiCloudDomain).where(
                    DigiCloudDomain.domain_name == name,
                    DigiCloudDomain.deleted_at.is_(None),
                ))
                if local is None or local.organization_id == organization.id:
                    continue
                key = (local.id, organization.id)
                if key in seen:
                    continue
                seen.add(key)
                number_count = self.db.scalar(select(func.count(DigiCloudPhoneNumber.id)).where(
                    DigiCloudPhoneNumber.domain_id == local.id
                )) or 0
                conflicts.append({
                    "domain": local,
                    "current_organization": local.organization,
                    "target_organization": organization,
                    "target_reseller": reseller,
                    "phone_number_count": number_count,
                })
        conflicts.sort(key=lambda item: item["domain"].domain_name)
        return conflicts, warnings

    def reassign_domain(self, domain_id: int, target_organization_id: int):
        """Move a local domain and all linked numbers to another organization."""
        if not (self.context.is_staff and self.context.is_superuser):
            raise HTTPException(403, "Platform Admin access required")
        domain = self.db.get(DigiCloudDomain, domain_id)
        if domain is None or domain.deleted_at is not None:
            raise HTTPException(404, "Domain not found")
        target = self.db.get(Organization, target_organization_id)
        if target is None or target.deleted_at is not None or not target.active:
            raise HTTPException(404, "Target organization not found")
        if domain.organization_id == target.id:
            raise HTTPException(400, "Domain already belongs to the selected organization")

        old_organization = domain.organization
        linked_numbers = list(self.db.scalars(select(DigiCloudPhoneNumber).where(
            DigiCloudPhoneNumber.domain_id == domain.id
        )))
        domain.organization_id = target.id
        for number in linked_numbers:
            number.organization_id = target.id

        self.db.flush()
        AuditService(self.db, self.request, self.context).record(
            "digicloud.domain.reassign",
            "domain",
            domain.id,
            f"Reassigned {domain.domain_name} from {old_organization.name} to {target.name}; moved {len(linked_numbers)} linked phone number(s)",
            module="digicloud",
            organization_id=target.id,
        )
        return domain, len(linked_numbers), old_organization, target

    def get_domain(self, domain_id: int):
        obj=self.db.get(DigiCloudDomain, domain_id)
        if not obj or obj.deleted_at is not None: raise HTTPException(404, "Domain not found")
        if self._organization_scoped and obj.organization_id != self.context.organization_id: raise HTTPException(403, "Domain access denied")
        self._require_domain_visible(obj.domain_name)
        return obj

    def create_domain(self, organization_id: int, domain_name: str, sync_provider: bool = True, **values):
        if self._organization_scoped: organization_id=self.context.organization_id
        settings=self.settings_for(organization_id)
        name=domain_name.strip().lower()
        if not name or "." not in name: raise HTTPException(400, "Enter a valid domain name")
        if self.db.scalar(select(DigiCloudDomain).where(DigiCloudDomain.domain_name == name, DigiCloudDomain.deleted_at.is_(None))): raise HTTPException(400, "Domain already exists")
        obj=DigiCloudDomain(organization_id=organization_id, domain_name=name, **values)
        self.db.add(obj); self.db.flush()
        if sync_provider:
            if not settings.netsapiens_reseller: raise HTTPException(400, "NetSapiens reseller is not configured for this organization")
            try:
                result=self.provider.create(settings.netsapiens_reseller, self._provider_payload(obj))
                obj.provider_domain_id=str(result.get("id") or result.get("domain") or name)
            except NetSapiensError as exc:
                obj.status="provider_error"; obj.last_error=str(exc)
        AuditService(self.db, self.request, self.context).record("digicloud.domain.create", "domain", obj.id, f"Created {name}", module="digicloud", organization_id=organization_id)
        return obj

    def update_domain(self, domain_id: int, sync_provider: bool = True, **values):
        obj=self.get_domain(domain_id)
        for key,value in values.items(): setattr(obj,key,value)
        if sync_provider:
            try: self.provider.update(obj.domain_name, self._provider_payload(obj)); obj.status="active"; obj.last_error=""
            except NetSapiensError as exc: obj.status="provider_error"; obj.last_error=str(exc)
        AuditService(self.db, self.request, self.context).record("digicloud.domain.update", "domain", obj.id, f"Updated {obj.domain_name}", module="digicloud", organization_id=obj.organization_id)
        return obj

    def delete_domain(self, domain_id: int, confirmation: str):
        """Delete the DigiCloud domain and its local NOP DigiCloud inventory.

        This operation deliberately does *not* call any carrier inventory API.
        Telephone numbers remain carrier-owned, but their DigiCloud/NOP inventory
        records are removed together with the deleted domain.
        """
        obj = self.get_domain(domain_id)
        if confirmation.strip().lower() != obj.domain_name.lower():
            raise HTTPException(400, "Domain confirmation did not match")

        # Always remove the live DigiCloud/NetSapiens domain.  There is no
        # local-only delete option because that can leave NOP out of sync.
        try:
            self.provider.delete(obj.domain_name)
        except NetSapiensError as exc:
            raise HTTPException(502, str(exc)) from exc

        # Remove the numbers from NOP's DigiCloud inventory along with the
        # domain.  This is a local database delete only: no carrier inventory
        # endpoint is called, so the numbers remain owned by the carrier.
        removed_numbers = list(self.db.scalars(
            select(DigiCloudPhoneNumber).where(DigiCloudPhoneNumber.domain_id == obj.id)
        ))
        for number in removed_numbers:
            self.db.delete(number)

        obj.deleted_at = datetime.now(timezone.utc)
        obj.status = "deleted"
        AuditService(self.db, self.request, self.context).record(
            "digicloud.domain.delete",
            "domain",
            obj.id,
            f"Deleted {obj.domain_name} from DigiCloud and NOP; removed {len(removed_numbers)} phone number(s) from NOP DigiCloud inventory; carrier inventory unchanged",
            module="digicloud",
            organization_id=obj.organization_id,
        )

    @staticmethod
    def _remote_phone_number(row: dict) -> str:
        raw = DigiCloudService._remote_value(
            row,
            "phonenumber", "phone_number", "phoneNumber", "telephone_number",
            "telephoneNumber", "number", "did", "tn", "matchrule",
            default="",
        )
        digits = re.sub(r"\D", "", str(raw or ""))
        # A dial-plan match rule may contain other digits. Prefer the final
        # North American 10/11-digit sequence when possible.
        matches = re.findall(r"(?:1?\d{10})", str(raw or ""))
        if matches:
            digits = re.sub(r"\D", "", matches[-1])
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        return digits if len(digits) == 10 else ""

    def sync_phone_numbers(self):
        """Import and reconcile NetSapiens phone numbers without changing NetSapiens."""
        if not self.phone_number_provider.client.configured:
            raise HTTPException(400, "NetSapiens API is not configured in .env")

        organizations = self.organizations()
        summary = {
            "organizations": 0,
            "received": 0,
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
            "reassigned": 0,
            "unmatched_domains": 0,
        }
        errors: list[str] = []

        for organization in organizations:
            settings = self.settings_for(organization.id, create=False)
            reseller = (settings.netsapiens_reseller if settings else "").strip()
            if not reseller:
                summary["skipped"] += 1
                continue

            summary["organizations"] += 1
            try:
                remote_numbers = self.phone_number_provider.list(reseller)
            except NetSapiensError as exc:
                errors.append(f"{organization.name}: {exc}")
                continue

            summary["received"] += len(remote_numbers)
            domains = {
                d.domain_name.lower(): d
                for d in self.db.scalars(
                    select(DigiCloudDomain).where(
                        DigiCloudDomain.organization_id == organization.id,
                        DigiCloudDomain.deleted_at.is_(None),
                    )
                )
            }

            for row in remote_numbers:
                tn = self._remote_phone_number(row)
                if not tn:
                    summary["skipped"] += 1
                    continue

                domain_name = str(self._remote_value(
                    row, "domain", "domain_name", "domainName", "host", default=""
                ) or "").strip().lower()
                domain = domains.get(domain_name) if domain_name else None
                if domain_name and domain is None:
                    summary["unmatched_domains"] += 1

                obj = self.db.scalar(
                    select(DigiCloudPhoneNumber).where(
                        DigiCloudPhoneNumber.telephone_number == tn
                    )
                )
                if obj is not None and obj.organization_id != organization.id:
                    # A number may legitimately move between resellers together with its
                    # domain. Permit the local ownership change only when the live
                    # NetSapiens row identifies a domain that is already owned by the
                    # target organization. Unassigned numbers remain protected from
                    # silent cross-organization transfers.
                    if domain is None:
                        summary["skipped"] += 1
                        errors.append(f"{tn}: already belongs to another organization and has no matched target domain")
                        continue
                    summary["reassigned"] += 1

                created = obj is None
                if created:
                    obj = DigiCloudPhoneNumber(
                        organization_id=organization.id,
                        telephone_number=tn,
                    )
                    self.db.add(obj)

                before = (obj.organization_id, obj.domain_id, obj.status)
                obj.organization_id = organization.id
                obj.domain_id = domain.id if domain else None

                enabled = self._remote_value(row, "enabled", "active", "status", default="yes")
                enabled_text = str(enabled).strip().lower()
                if enabled_text in {"no", "false", "0", "disabled", "inactive", "suspended"}:
                    obj.status = "inactive"
                elif domain is not None:
                    obj.status = "assigned"
                else:
                    obj.status = "available"

                after = (obj.organization_id, obj.domain_id, obj.status)
                if created:
                    summary["created"] += 1
                elif before != after:
                    summary["updated"] += 1
                else:
                    summary["unchanged"] += 1

        if summary["organizations"] == 0:
            raise HTTPException(400, "No accessible organization has a NetSapiens reseller configured")
        if errors and summary["received"] == 0:
            raise HTTPException(502, "; ".join(errors[:3]))

        AuditService(self.db, self.request, self.context).record(
            "digicloud.number.sync",
            "phone_number",
            None,
            (
                f"NetSapiens phone number sync: {summary['created']} created, "
                f"{summary['updated']} updated, {summary['unchanged']} unchanged, "
                f"{summary['reassigned']} reassigned, {summary['skipped']} skipped"
            ),
            module="digicloud",
            organization_id=None if self.context.is_staff else self.context.organization_id,
        )
        return summary

    def list_numbers(self, q: str = ""):
        stmt=select(DigiCloudPhoneNumber)
        if self._organization_scoped:
            stmt=stmt.where(DigiCloudPhoneNumber.organization_id==self.context.organization_id)
        search_digits = re.sub(r"\D", "", q)
        if search_digits:
            stmt = stmt.where(
                DigiCloudPhoneNumber.telephone_number.like(f"%{search_digits}%")
            )
        rows = list(self.db.scalars(stmt.order_by(DigiCloudPhoneNumber.telephone_number)).unique())
        hidden = self._hidden_domains()
        if hidden:
            rows = [row for row in rows if not row.domain or row.domain.domain_name.strip().lower().rstrip(".") not in hidden]
        return rows

    def add_number(self, organization_id: int, telephone_number: str, notes: str=""):
        if self._organization_scoped: organization_id=self.context.organization_id
        tn=normalize_tn(telephone_number)
        if self.db.scalar(select(DigiCloudPhoneNumber).where(DigiCloudPhoneNumber.telephone_number==tn)): raise HTTPException(400,"Phone number already exists")
        obj=DigiCloudPhoneNumber(organization_id=organization_id,telephone_number=tn,notes=notes.strip())
        self.db.add(obj); self.db.flush()
        AuditService(self.db,self.request,self.context).record("digicloud.number.add","phone_number",obj.id,f"Added {tn}",module="digicloud",organization_id=organization_id)
        return obj

    def assign_number(self, number_id: int, domain_id: int | None):
        obj=self.db.get(DigiCloudPhoneNumber,number_id)
        if not obj: raise HTTPException(404,"Phone number not found")
        if self._organization_scoped and obj.organization_id!=self.context.organization_id: raise HTTPException(403,"Phone number access denied")
        if domain_id:
            domain=self.get_domain(domain_id)
            if domain.organization_id!=obj.organization_id: raise HTTPException(400,"Phone number and domain must belong to the same organization")
            obj.domain_id=domain.id; obj.status="assigned"
        else: obj.domain_id=None; obj.status="available"
        AuditService(self.db,self.request,self.context).record("digicloud.number.assign","phone_number",obj.id,f"Assignment changed for {obj.telephone_number}",module="digicloud",organization_id=obj.organization_id)
        return obj

    def remove_number(self, number_id: int):
        obj=self.db.get(DigiCloudPhoneNumber,number_id)
        if not obj: raise HTTPException(404,"Phone number not found")
        if self._organization_scoped and obj.organization_id!=self.context.organization_id: raise HTTPException(403,"Phone number access denied")
        if obj.domain_id: raise HTTPException(400,"Unassign the phone number before removing it")
        self.db.delete(obj)

    def dashboard_counts(self):
        domains=self.list_domains(); numbers=self.list_numbers()
        return {"domains":len(domains),"active_domains":sum(d.status=="active" for d in domains),"assigned_numbers":sum(n.domain_id is not None for n in numbers),"available_numbers":sum(n.domain_id is None for n in numbers)}

    @staticmethod
    def _provider_payload(obj):
        return {"domain":obj.domain_name,"description":obj.description,"caller_id_name":obj.caller_id_name,"caller_id_number":obj.caller_id_number,"emergency_caller_id":obj.emergency_caller_id,"area_code":obj.area_code,"time_zone":obj.time_zone,"max_calls":obj.max_calls,"max_offnet_calls":obj.max_offnet_calls,"recording":obj.recording_enabled,"transcription":obj.transcription_enabled,"transcription_provider":obj.transcription_provider,"email_from":obj.email_from}

    def get_number(self, number_id: int):
        obj = self.db.get(DigiCloudPhoneNumber, number_id)
        if not obj:
            raise HTTPException(404, "Phone number not found")
        if self._organization_scoped and obj.organization_id != self.context.organization_id:
            raise HTTPException(403, "Phone number access denied")
        if obj.domain:
            self._require_domain_visible(obj.domain.domain_name)
        return obj

    def number_domains(self, organization_id: int):
        if self._organization_scoped and organization_id != self.context.organization_id:
            raise HTTPException(403, "Organization access denied")
        stmt = select(DigiCloudDomain).where(
            DigiCloudDomain.organization_id == organization_id,
            DigiCloudDomain.deleted_at.is_(None),
            DigiCloudDomain.status != "deleted",
        )
        hidden = self._hidden_domains()
        if hidden:
            stmt = stmt.where(~DigiCloudDomain.domain_name.in_(hidden))
        return list(self.db.scalars(stmt.order_by(DigiCloudDomain.domain_name)))

    @staticmethod
    def _provider_route_payload(row: dict, fallback_user: str, fallback_domain: str) -> dict:
        keys = (
            "enabled",
            "dial-rule-application",
            "dial-rule-parameter",
            "dial-rule-translation-destination-user",
            "dial-rule-translation-destination-host",
            "dial-rule-translation-source-name",
            "dial-rule-description",
        )
        payload = {key: row[key] for key in keys if row.get(key) not in (None, "")}
        payload.setdefault("enabled", "yes")
        payload.setdefault("dial-rule-translation-destination-user", fallback_user)
        payload.setdefault("dial-rule-translation-destination-host", fallback_domain)
        return payload

    TREATMENT_LABELS = {
        "available": "Available Number",
        "user": "User / Extension",
        "conference": "Conference",
        "voicemail": "Voicemail",
        "auto_attendant": "Auto Attendant",
        "sip_trunk": "SIP Trunk",
    }

    @classmethod
    def normalize_treatment(cls, value: str | None) -> str:
        treatment = (value or "available").strip().lower() or "available"
        if treatment not in cls.TREATMENT_LABELS:
            raise HTTPException(400, "Select a valid assignment treatment")
        return treatment

    def live_number_settings(self, obj: DigiCloudPhoneNumber) -> dict:
        settings = {
            "treatment": "available",
            "destination_user": "",
            "enabled": True,
            "description": obj.notes or "",
        }
        if not obj.domain:
            return settings
        try:
            row = self.phone_number_provider.get_for_domain(
                obj.domain.domain_name, obj.telephone_number
            )
        except NetSapiensError:
            return settings
        app = str(row.get("dial-rule-application") or "").strip().lower()
        aliases = {
            "available number": "available",
            "available": "available",
            "user": "user",
            "user / extension": "user",
            "conference": "conference",
            "voicemail": "voicemail",
            "auto attendant": "auto_attendant",
            "auto_attendant": "auto_attendant",
            "sip trunk": "sip_trunk",
            "sip_trunk": "sip_trunk",
        }
        settings["treatment"] = aliases.get(app, "user" if row.get("dial-rule-translation-destination-user") else "available")
        settings["destination_user"] = str(row.get("dial-rule-translation-destination-user") or "")
        settings["enabled"] = self._remote_bool(row.get("enabled"), True)
        settings["description"] = str(row.get("dial-rule-description") or obj.notes or "")
        return settings

    def add_or_move_number_live(
        self,
        number_id: int | None,
        telephone_number: str,
        organization_id: int,
        domain_id: int | None,
        destination_user: str,
        description: str = "",
        treatment: str = "available",
        enabled: bool = True,
    ):
        """Add, update, or move a number while preserving explicit removal semantics.

        Saving with no treatment defaults to Available Number inside the selected
        domain. Only the separate remove action deletes the live domain mapping.
        """
        if not self.phone_number_provider.client.configured:
            raise HTTPException(400, "NetSapiens API is not configured in .env")

        if self._organization_scoped:
            organization_id = self.context.organization_id

        treatment = self.normalize_treatment(treatment)
        destination_user = (destination_user or "").strip()
        description = (description or "").strip()
        if treatment == "available":
            destination_user = ""
        elif not destination_user:
            raise HTTPException(400, f"Enter a destination for {self.TREATMENT_LABELS[treatment]}")
        if domain_id is None:
            raise HTTPException(400, "Select a domain")

        tn = normalize_tn(telephone_number)
        obj = self.get_number(number_id) if number_id else self.db.scalar(
            select(DigiCloudPhoneNumber).where(DigiCloudPhoneNumber.telephone_number == tn)
        )
        if obj and obj.organization_id != organization_id:
            raise HTTPException(400, "Phone number belongs to another organization")

        domain = self.get_domain(domain_id)
        if domain.organization_id != organization_id:
            raise HTTPException(400, "Phone number and domain must belong to the same organization")
        old_domain = obj.domain if obj and obj.domain_id else None

        try:
            if old_domain and old_domain.id == domain.id:
                self.phone_number_provider.update_in_domain(
                    domain.domain_name, tn,
                    destination_user=destination_user, description=description,
                    treatment=treatment, enabled=enabled,
                )
                action = "updated"
            elif old_domain:
                old_row = {}
                try:
                    old_row = self.phone_number_provider.get_for_domain(old_domain.domain_name, tn)
                except NetSapiensError:
                    pass
                restore_payload = self._provider_route_payload(
                    old_row,
                    fallback_user=str(old_row.get("dial-rule-translation-destination-user") or ""),
                    fallback_domain=old_domain.domain_name,
                )
                self.phone_number_provider.remove_from_domain(old_domain.domain_name, tn)
                try:
                    self.phone_number_provider.add_to_domain(
                        domain.domain_name, tn, destination_user=destination_user,
                        description=description, treatment=treatment, enabled=enabled,
                    )
                except NetSapiensError as move_error:
                    try:
                        self.phone_number_provider.add_to_domain(
                            old_domain.domain_name, tn,
                            destination_user=str(restore_payload.get("dial-rule-translation-destination-user", "")),
                            description=str(restore_payload.get("dial-rule-description", "")),
                            treatment=str(restore_payload.get("dial-rule-application", "available")),
                            enabled=self._remote_bool(restore_payload.get("enabled"), True),
                            payload=restore_payload,
                        )
                    except NetSapiensError:
                        pass
                    raise move_error
                action = "moved"
            else:
                self.phone_number_provider.add_to_domain(
                    domain.domain_name, tn, destination_user=destination_user,
                    description=description, treatment=treatment, enabled=enabled,
                )
                action = "assigned"
        except NetSapiensError as exc:
            raise HTTPException(502, str(exc)) from exc

        if obj is None:
            obj = DigiCloudPhoneNumber(organization_id=organization_id, telephone_number=tn)
            self.db.add(obj)
            self.db.flush()
        obj.organization_id = organization_id
        obj.domain_id = domain.id
        obj.status = "assigned" if enabled else "disabled"
        obj.notes = description

        detail = self.TREATMENT_LABELS[treatment]
        AuditService(self.db, self.request, self.context).record(
            f"digicloud.number.{action}", "phone_number", obj.id,
            f"{action.title()} {tn} to {domain.domain_name}; treatment {detail}"
            + (f"; destination {destination_user}" if destination_user else ""),
            module="digicloud", organization_id=organization_id,
        )
        return obj, action

    def delete_number_live(self, number_id: int, confirmation: str):
        """Delete a phone number from DigiCloud and NOP, never from the carrier.

        DigiCloud phone-number deletion is the domain-scoped NetSapiens DELETE.
        After that succeeds, remove the local NOP inventory row as well. Carrier
        inventory is intentionally untouched by this workflow.
        """
        obj = self.get_number(number_id)
        if normalize_tn(confirmation) != obj.telephone_number:
            raise HTTPException(400, "Phone number confirmation did not match")

        tn = obj.telephone_number
        organization_id = obj.organization_id
        old_domain = obj.domain

        if old_domain:
            try:
                self.phone_number_provider.remove_from_domain(
                    old_domain.domain_name,
                    tn,
                )
            except NetSapiensError as exc:
                raise HTTPException(502, str(exc)) from exc

        AuditService(self.db, self.request, self.context).record(
            "digicloud.number.delete",
            "phone_number",
            obj.id,
            (f"Deleted {tn} from DigiCloud domain {old_domain.domain_name} and NOP inventory; "
             "carrier inventory unchanged") if old_domain else
            f"Deleted {tn} from NOP inventory; carrier inventory unchanged",
            module="digicloud",
            organization_id=organization_id,
        )
        self.db.delete(obj)
        return tn, old_domain
