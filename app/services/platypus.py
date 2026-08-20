from __future__ import annotations

from dataclasses import dataclass
import re
import secrets
from typing import Any, Iterable
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings


class PlatypusError(RuntimeError):
    """Base error for Platypus API operations."""


class PlatypusConfigurationError(PlatypusError):
    pass


class PlatypusTransportError(PlatypusError):
    pass


class PlatypusAPIError(PlatypusError):
    def __init__(self, action: str, code: str, message: str):
        self.action = action
        self.code = code
        self.message = message
        super().__init__(f"{action} failed ({code}): {message or 'Unknown Platypus error'}")


@dataclass(frozen=True)
class PlatypusResponse:
    action: str
    response_code: str
    response_text: str
    is_success: bool
    records: list[dict[str, str | None]]


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _record(node: ET.Element) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for child in list(node):
        if list(child):
            # Sprint 4.4.0a read proofs are flat recordsets. Preserve nested XML
            # rather than silently discarding it so future mappings can use it.
            result[child.tag] = ET.tostring(child, encoding="unicode")
        else:
            value = _text(child)
            result[child.tag] = None if value.upper() == "NULL" or value == "" else value
    return result


def _append_xml_value(parent: ET.Element, name: str, value: Any) -> None:
    """Append a scalar or the documented AddService column-array value."""
    node = ET.SubElement(parent, name)
    if isinstance(value, list):
        node.set("type", "array")
        for item in value:
            row = ET.SubElement(node, "row")
            for column_name, column_value in item.items():
                ET.SubElement(row, column_name).text = str(column_value or "")
        return
    node.text = str(value)


class PlatypusClient:
    """Minimal stateless Platypus 7 XML API client.

    Sprint 4.4.0a intentionally exposes read-only methods only. Write methods
    (AddRate, UpdateRate, AddService, etc.) belong in the later write sprint.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def validate_configuration(self) -> tuple[bool, str]:
        missing: list[str] = []
        if not self.settings.platypus_api_url.strip():
            missing.append("PLATYPUS_API_URL")
        if not self.settings.platypus_username.strip():
            missing.append("PLATYPUS_USERNAME")
        if not self.settings.platypus_password:
            missing.append("PLATYPUS_PASSWORD")
        if missing:
            return False, "Missing " + ", ".join(missing)
        return True, "Platypus API configured"

    def _request_xml(
        self,
        action: str,
        *,
        parameters: Iterable[tuple[str, Any]] = (),
        properties: Iterable[tuple[str, Any]] = (),
    ) -> bytes:
        root = ET.Element("PLATXML")
        ET.SubElement(root, "header")
        body = ET.SubElement(root, "body")
        block = ET.SubElement(body, "data_block")
        ET.SubElement(block, "protocol").text = "Plat"
        ET.SubElement(block, "object").text = "addusr"
        ET.SubElement(block, "action").text = action
        ET.SubElement(block, "logintype").text = self.settings.platypus_login_type
        ET.SubElement(block, "username").text = self.settings.platypus_username
        ET.SubElement(block, "password").text = self.settings.platypus_password

        params_node = ET.SubElement(block, "parameters")
        for name, value in parameters:
            _append_xml_value(params_node, name, value)

        props_node = ET.SubElement(block, "properties")
        for name, value in properties:
            _append_xml_value(props_node, name, value)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    async def call(
        self,
        action: str,
        *,
        parameters: Iterable[tuple[str, Any]] = (),
        properties: Iterable[tuple[str, Any]] = (),
    ) -> PlatypusResponse:
        valid, detail = self.validate_configuration()
        if not valid:
            raise PlatypusConfigurationError(detail)

        payload = self._request_xml(action, parameters=parameters, properties=properties)
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.platypus_timeout_seconds,
                verify=self.settings.platypus_verify_ssl,
            ) as client:
                response = await client.post(
                    self.settings.platypus_api_url.rstrip("/"),
                    content=payload,
                    headers={
                        "Content-Type": "application/xml",
                        "Accept": "application/xml, text/xml, */*",
                        "User-Agent": f"NOP/{self.settings.app_version}",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PlatypusTransportError(f"Platypus transport error: {exc}") from exc

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            preview = response.text[:300].replace("\n", " ")
            raise PlatypusTransportError(
                f"Platypus returned non-XML content: {preview}"
            ) from exc

        reply = root.find("./body/data_block")
        if reply is None:
            raise PlatypusTransportError("Platypus response did not contain body/data_block")

        response_code = _text(reply.find("response_code"))
        response_text = _text(reply.find("response_text"))
        is_success = _text(reply.find("is_success")) in {"1", "true", "True"}
        records = [_record(node) for node in reply.findall("./attributes/data_block")]

        if not is_success:
            raise PlatypusAPIError(action, response_code or "ERROR", response_text)

        return PlatypusResponse(action, response_code, response_text, is_success, records)

    async def search_customers(
        self,
        search: str = "",
        *,
        where_clause: str | None = None,
        store_list: str | None = None,
    ) -> list[dict[str, str | None]]:
        # SearchCustomer compares the Search property to name, attention,
        # phone, customer id, and username. Platypus also documents optional
        # WhereClause and StoreList parameters after DataType.  An empty Search
        # string is useful for complete customer discovery because the API guide
        # does not expose a separate ListCustomers method.
        params: list[tuple[str, Any]] = [("datatype", "XML")]
        if where_clause is not None or store_list is not None:
            params.append(("whereclause", (where_clause or "").strip()))
        if store_list is not None:
            params.append(("storelist", store_list.strip()))
        result = await self.call(
            "SearchCustomer",
            parameters=params,
            properties=(("search", search.strip()),),
        )
        return result.records

    async def get_customer(self, customer_id: str | int) -> dict[str, str | None]:
        result = await self.call(
            "GetCustomer",
            parameters=(("datatype", "XML"),),
            properties=(("custid", customer_id),),
        )
        return result.records[0] if result.records else {}

    async def add_customer(
        self,
        *,
        name: str,
        phone: str,
        username: str,
        address_line_1: str,
        address_line_2: str = "",
        city: str,
        state: str,
        postal_code: str,
        country: str = "US",
        email: str = "",
        billing_method: str = "check",
        store_id: str | int = "1",
        staff_id: str | int = "1",
        temporary_password: str = "",
    ) -> dict[str, str]:
        """Create one Platypus customer without bundling rates or services.

        Rates are intentionally added in separate calls so NOP can retain the
        returned customer ID and recover safely from later partial failures.
        """
        required = {
            "Customer name": name,
            "Phone": phone,
            "Username": username,
            "Address": address_line_1,
            "City": city,
            "State": state,
            "Postal code": postal_code,
        }
        missing = [label for label, value in required.items() if not str(value or "").strip()]
        if missing:
            raise ValueError("Platypus customer is missing: " + ", ".join(missing))
        clean_phone = re.sub(r"\D", "", phone or "")
        if len(clean_phone) not in {10, 11}:
            raise ValueError("Platypus customer phone must contain 10 digits.")
        method = str(billing_method or "check").strip().lower()
        if method not in {"check", "ccard"}:
            raise ValueError("Platypus billing method must be check or ccard.")
        password = temporary_password or secrets.token_urlsafe(18)
        result = await self.call(
            "AddToPlat",
            parameters=(
                ("activeconn", "false"),
                ("datatype", "XML"),
            ),
            properties=(
                ("billingmeth", method),
                ("phone", clean_phone[-10:]),
                ("fax", ""),
                ("username", str(username).strip()),
                ("password", password),
                ("name2", str(name).strip()),
                ("address", str(address_line_1).strip()),
                ("address2", str(address_line_2 or "").strip()),
                ("city", str(city).strip()),
                ("state", str(state).strip().upper()),
                ("zip", str(postal_code).strip()),
                ("country", str(country or "US").strip().upper()),
                ("email", str(email or username).strip()),
                ("bonustype", "F"),
                ("staffid", str(staff_id)),
                ("storeid", str(store_id)),
                ("selectpop", "1"),
                ("selectrate", "-1"),
                ("selectshell", "1"),
                ("htmlemail", "Y"),
            ),
        )
        customer_id = str(
            (result.records[0] if result.records else {}).get("custid") or ""
        ).strip()
        if not customer_id or customer_id == "0":
            raise PlatypusAPIError(
                "AddToPlat",
                result.response_code or "DATA_ERROR",
                "Platypus did not return the new customer ID.",
            )
        return {
            "customer_id": customer_id,
            "username": str(username).strip(),
            "temporary_password": password,
        }

    async def get_rates(self, customer_id: str | int) -> list[dict[str, str | None]]:
        result = await self.call(
            "GetRates",
            parameters=(("datatype", "XML"),),
            properties=(("custid", customer_id),),
        )
        return result.records

    async def add_rate(self, customer_id: str | int, rate_group_id: str | int, *, frequency: int = 1, quantity: int = 1) -> str:
        """Assign a billing rate group and return its new CRID."""
        result = await self.call(
            "AddRate",
            parameters=(("rate", rate_group_id), ("noconn", "false"), ("datatype", "XML"), ("frequency", max(int(frequency), 1)), ("quantity", max(int(quantity), 1))),
            properties=(("custid", customer_id),),
        )
        crid = str((result.records[0] if result.records else {}).get("crid") or "").strip()
        if not crid or crid == "0":
            raise PlatypusAPIError("AddRate", result.response_code or "DATA_ERROR", "Platypus did not return the new CRID.")
        return crid

    async def delete_rate(
        self,
        customer_id: str | int,
        crid: str | int,
        *,
        no_closeout: bool = False,
    ) -> None:
        """Delete one customer rate assignment and its attached services."""
        await self.call(
            "DeleteRate",
            parameters=(
                ("cCRID", crid),
                ("bNoCloseout", "True" if no_closeout else "False"),
                ("datatype", "XML"),
            ),
            properties=(("custid", customer_id),),
        )

    async def get_available_rates(self) -> list[dict[str, str | None]]:
        result = await self.call(
            "GetAvailableRates",
            parameters=(("datatype", "XML"),),
        )
        return result.records

    async def get_available_web_rates(
        self,
        customer_id: str | int,
        store_id: str | int,
        *,
        iccs: bool = False,
    ) -> list[dict[str, str | None]]:
        """Return live rate groups available to this customer and company.

        Platypus GetAvailableRates can return DATA_ERROR for API-only staff
        accounts even when those accounts may add rates. GetAvailableWebRates
        applies the documented customer/store availability and dependency
        checks and is therefore the appropriate discovery call for NOP.
        """
        result = await self.call(
            "GetAvailableWebRates",
            parameters=(
                ("datatype", "XML"),
                ("ICCS", "true" if iccs else "false"),
            ),
            properties=(("custid", customer_id), ("storeid", store_id)),
        )
        return result.records

    async def list_service_tree(self, customer_id: str | int) -> list[dict[str, str | None]]:
        result = await self.call(
            "ListServiceTree",
            parameters=(("datatype", "XML"),),
            properties=(("custid", customer_id),),
        )
        return result.records

    async def get_service_info(
        self, service_type_id: str | int, *, rgid: str | int = 0, crid: str | int = 0
    ) -> list[dict[str, str | None]]:
        result = await self.call(
            "GetServiceInfo",
            parameters=(("svcid", service_type_id), ("datatype", "XML"), ("rgid", rgid), ("crid", crid)),
        )
        return result.records

    async def add_service(
        self,
        customer_id: str | int,
        *,
        service_type_id: str | int,
        crid: str | int,
        custom_fields: list[dict[str, str]],
    ) -> str:
        """Add one service instance to an assigned customer rate."""
        column_array = [
            {"column_name": "crid", "newvalue": crid, "oldvalue": "", "control": "txt_text", "display": "CRID"},
            {"column_name": "d_custid", "newvalue": customer_id, "oldvalue": "", "control": "txt_text", "display": "Customer ID"},
            {"column_name": "d_active", "newvalue": "Y", "oldvalue": "", "control": "txt_text", "display": "Active"},
        ]
        column_array.extend(custom_fields)
        result = await self.call(
            "AddService",
            parameters=(("serviceid", service_type_id), ("crid", crid), ("columnarray", column_array), ("datatype", "XML")),
            properties=(("custid", customer_id),),
        )
        data_id = str((result.records[0] if result.records else {}).get("dataid") or "").strip()
        if not data_id or data_id == "0":
            raise PlatypusAPIError("AddService", result.response_code or "DATA_ERROR", "Platypus did not return the new service Data ID.")
        return data_id

    async def delete_service(
        self,
        customer_id: str | int,
        *,
        service_type_id: str | int,
        data_id: str | int,
    ) -> None:
        """Delete one service instance while preserving its assigned rate."""
        await self.call(
            "DeleteService",
            parameters=(
                ("svcid", service_type_id),
                ("dataid", data_id),
                ("datatype", "XML"),
            ),
            properties=(("custid", customer_id),),
        )

    async def list_service_instances(
        self,
        customer_id: str | int,
        *,
        crid: str | int | None = None,
    ) -> list[dict[str, str | None]]:
        # The documented stateless example uses service=0 and instance=0 to
        # list instances, followed by datatype and CRID in parameter order.
        params: list[tuple[str, Any]] = [
            ("service", "0"),
            ("instance", "0"),
            ("datatype", "XML"),
        ]
        if crid is not None:
            params.append(("crid", crid))
        result = await self.call(
            "ListServiceInstances",
            parameters=params,
            properties=(("custid", customer_id),),
        )
        return result.records

    async def get_addresses(self, customer_id: str | int) -> list[dict[str, str | None]]:
        """Return all address records for a Platypus customer."""
        result = await self.call(
            "GetAddress",
            parameters=(("datatype", "XML"),),
            properties=(("custid", customer_id),),
        )
        return result.records

    async def list_services2(
        self,
        customer_id: str | int,
        *,
        crid: str | int | None = None,
    ) -> list[dict[str, str | None]]:
        """Return service instances for a customer, optionally scoped to one CRID.

        Platypus documents ListServices2 specifically as the customer service-instance
        listing that can be filtered by Customer Rate (CRID).  We also enforce the
        returned s_custrate value locally because older Platypus builds can return a
        broader recordset than requested.
        """
        params: list[tuple[str, Any]] = []
        if crid is not None:
            params.append(("crid", crid))
        params.append(("datatype", "XML"))
        result = await self.call(
            "ListServices2",
            parameters=params,
            properties=(("custid", customer_id),),
        )
        records = result.records
        if crid is None:
            return records
        wanted = str(crid).strip()
        return [
            row for row in records
            if str(row.get("s_custrate") or "").strip() == wanted
        ]

    async def get_service_detail(
        self,
        customer_id: str | int,
        service_type_id: str | int,
        data_id: str | int,
    ) -> dict[str, str | None]:
        """Return every custom field stored for one Platypus service instance."""
        result = await self.call(
            "GetServiceDetail",
            parameters=(
                ("svcid", service_type_id),
                ("dataid", data_id),
                ("datatype", "XML"),
            ),
            properties=(("custid", customer_id),),
        )
        return result.records[0] if result.records else {}

    async def get_phones(self, customer_id: str | int) -> list[dict[str, str | None]]:
        """Return all phone records for a Platypus customer."""
        result = await self.call(
            "GetPhone",
            parameters=(("datatype", "XML"),),
            properties=(("custid", customer_id),),
        )
        return result.records

    async def get_staff_notes(self, customer_id: str | int) -> list[dict[str, str | None]]:
        """Return Platypus Tasks/Notes attached to a customer.

        Despite its name, GetStaffNotes is also the documented customer-note
        reader. NoteIDType=Customer makes the customer filter explicit and an
        empty NoteType requests every status (Incomplete, Waiting, Complete).
        """
        result = await self.call(
            "GetStaffNotes",
            parameters=(("datatype", "XML"),),
            properties=(
                ("custid", customer_id),
                ("noteidtype", "Customer"),
                ("notetype", ""),
            ),
        )
        return result.records

    @staticmethod
    def _sanitize_customer(record: dict[str, str | None]) -> dict[str, str | None]:
        """Remove credentials/payment fields that ticketing must never receive."""
        blocked = {
            "password", "secretword", "ccnumber", "ccdate", "cctype",
            "routenumber", "bank_name", "bank_acct_type", "acctnumber",
            "creditcardmasked", "acctnumbermasked", "osrsusername",
            "osrspassword", "cuskey",
        }
        return {key: value for key, value in record.items() if key.lower() not in blocked}

    @staticmethod
    def _sanitize_search_record(record: dict[str, str | None]) -> dict[str, str | None]:
        allowed = {"id", "name", "attn", "phone", "phonemasked", "username", "active", "storename"}
        return {key: value for key, value in record.items() if key.lower() in allowed}

    @staticmethod
    def _popup_notes(record: dict[str, str | None]) -> list[str]:
        """Extract Platypus customer popup messages across API field variants."""
        popup_fields = {
            "popup", "popupnote", "popupnotes", "popupmessage", "popuptext",
            "customerpopup", "customerpopupnote", "alertnote", "alertmessage",
        }
        flag_fields = {"showpopup", "popupenabled", "popupflag", "haspopup"}
        note_fields = {"note", "notes", "comment", "comments", "message", "warning"}
        notes: list[str] = []
        popup_enabled = False
        for key, value in record.items():
            normalized = "".join(ch for ch in str(key).lower() if ch.isalnum())
            text = str(value or "").strip()
            if normalized in flag_fields:
                popup_enabled = text.lower() in {"1", "true", "yes", "y", "on"}
            is_popup_content = (
                normalized in popup_fields
                or "popup" in normalized
                or normalized.startswith("popnote")
                or "note" in normalized
                or "memo" in normalized
                or "notice" in normalized
                or "warning" in normalized
                or "alert" in normalized
                or normalized in note_fields
            )
            if is_popup_content and text.lower() not in {
                "", "0", "1", "false", "true", "no", "yes", "n", "y", "off", "on",
            }:
                notes.append(text)
        if popup_enabled and not notes:
            for key, value in record.items():
                normalized = "".join(ch for ch in str(key).lower() if ch.isalnum())
                text = str(value or "").strip()
                if normalized in note_fields and text:
                    notes.append(text)
        return list(dict.fromkeys(notes))

    @staticmethod
    def _is_completed_note(record: dict[str, str | None]) -> bool:
        """Return True when Platypus marks a Task/Note as completed."""
        status_fields = {"status", "notestatus", "notetype", "type", "taskstatus"}
        for key, value in record.items():
            normalized_key = "".join(ch for ch in str(key).lower() if ch.isalnum())
            normalized_value = str(value or "").strip().lower()
            if normalized_key in status_fields and normalized_value in {
                "complete", "completed", "closed",
            }:
                return True
        return False

    async def search_ticketing_customers(self, search: str) -> list[dict[str, str | None]]:
        """Live customer directory lookup used by NOP ticketing/customer UI."""
        return [self._sanitize_search_record(row) for row in await self.search_customers(search)]

    async def get_ticketing_customer(self, customer_id: str | int) -> dict[str, Any]:
        """Build a safe operational customer profile from live Platypus data."""
        selected_id = str(customer_id).strip()
        customer = self._sanitize_customer(await self.get_customer(selected_id))

        async def optional_records(loader):
            try:
                return await loader(selected_id)
            except PlatypusAPIError as exc:
                if exc.code == "DATA_ERROR":
                    return []
                raise

        addresses = await optional_records(self.get_addresses)
        # Ticketing only needs the two operational address types.  Platypus
        # returns typename on GetAddress records (for example, Billing).
        address_types = {"billing", "service"}
        addresses = [
            row for row in addresses
            if str(row.get("typename") or "").strip().lower() in address_types
        ]
        billing_address = next(
            (row for row in addresses if str(row.get("typename") or "").strip().lower() == "billing"),
            None,
        )
        service_address = next(
            (row for row in addresses if str(row.get("typename") or "").strip().lower() == "service"),
            None,
        )
        if billing_address is None and any(customer.get(k) for k in ("addr1", "addr2", "city", "state", "zip")):
            billing_address = {
                "typename": "Billing",
                "addr1": customer.get("addr1"),
                "addr2": customer.get("addr2"),
                "city": customer.get("city"),
                "state": customer.get("state"),
                "zip": customer.get("zip"),
                "country": customer.get("country"),
            }
        phones = await optional_records(self.get_phones)
        staff_notes = [
            note for note in await optional_records(self.get_staff_notes)
            if not self._is_completed_note(note)
        ]

        try:
            rates = await self.get_rates(selected_id)
        except PlatypusAPIError as exc:
            if exc.action == "GetRates" and "No Rate Groups have been assigned" in exc.message:
                rates = []
            else:
                raise

        services: list[dict[str, str | None]] = []
        services_by_crid: dict[str, list[dict[str, str | None]]] = {}
        for rate in rates:
            crid = str(rate.get("crid") or rate.get("cr_id") or rate.get("CRID") or "").strip()
            if not crid:
                continue
            try:
                rate_services = await self.list_services2(selected_id, crid=crid)
            except PlatypusAPIError as exc:
                if exc.code == "DATA_ERROR":
                    rate_services = []
                else:
                    raise
            # ListServices2 exposes the service's display value, which may be
            # only its numeric instance ID (for example Adtran Gateway #108).
            # Load the documented service-detail record so integrations can use
            # the actual gateway serial/location stored in its custom fields.
            for service in rate_services:
                service_name = str(service.get("s_name") or "").lower()
                if not any(token in service_name for token in (
                    "plume", "pod", "adtran", "gateway", "managed wifi", "managed wi-fi",
                )):
                    continue
                service_type_id = service.get("s_svc_id") or service.get("svc_id")
                data_id = service.get("s_num") or service.get("data_id")
                if not service_type_id or not data_id:
                    continue
                try:
                    service["detail"] = await self.get_service_detail(
                        selected_id, service_type_id, data_id
                    )
                except PlatypusAPIError as exc:
                    if exc.code == "DATA_ERROR":
                        service["detail"] = {}
                    else:
                        raise
            services_by_crid[crid] = rate_services
            services.extend(rate_services)

        # Attach services to a copy of each rate for template/API consumers while
        # retaining the original flat services list for compatibility.
        mapped_rates: list[dict[str, Any]] = []
        for rate in rates:
            mapped = dict(rate)
            crid = str(rate.get("crid") or rate.get("cr_id") or rate.get("CRID") or "").strip()
            mapped["services"] = services_by_crid.get(crid, [])
            mapped_rates.append(mapped)

        return {
            "source": "platypus",
            "platypus_customer_id": selected_id,
            "customer": customer,
            # Keep legacy inline fields as a fallback, but the documented
            # GetStaffNotes recordset is the authoritative note source.
            "popup_notes": self._popup_notes(customer),
            "staff_notes": staff_notes,
            "addresses": addresses,
            "billing_address": billing_address,
            "service_address": service_address,
            "phones": phones,
            "rates": mapped_rates,
            "services": services,
        }

    async def read_customer_proof(self, customer_id: str | int) -> dict[str, Any]:
        """Load the exact Platypus customer selected by custid.

        Customer search is intentionally separate from detail/rate/service reads.
        A search must never fail because one matching customer has no rates.
        """
        selected_id = str(customer_id).strip()
        customer = await self.get_customer(selected_id)

        try:
            rates = await self.get_rates(selected_id)
        except PlatypusAPIError as exc:
            if exc.action == "GetRates" and "No Rate Groups have been assigned" in exc.message:
                rates = []
            else:
                raise

        services: list[dict[str, str | None]] = []
        if rates:
            # Read services by CRID so each service remains tied to the rate
            # assignment that owns it. One empty rate must not invalidate the
            # rest of the customer.
            for rate in rates:
                crid = rate.get("crid") or rate.get("cr_id") or rate.get("CRID")
                if not crid:
                    continue
                try:
                    services.extend(await self.list_service_instances(selected_id, crid=crid))
                except PlatypusAPIError as exc:
                    if exc.code == "DATA_ERROR":
                        continue
                    raise

        return {
            "selected_customer_id": selected_id,
            "customer": customer,
            "rates": rates,
            "services": services,
        }

    async def read_proof(self, search: str, customer_id: str | int | None = None) -> dict[str, Any]:
        """Backward-compatible helper for Sprint 4.4.0a callers.

        Without customer_id this is search-only. With customer_id it returns
        the search results plus detail reads for that exact customer.
        """
        matches = await self.search_customers(search)
        if customer_id is None:
            return {"search": matches}
        detail = await self.read_customer_proof(customer_id)
        return {"search": matches, **detail}
