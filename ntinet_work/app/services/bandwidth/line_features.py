from __future__ import annotations

from html import escape
from typing import Any

from .client import BandwidthClient


class LineFeaturesService:
    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self) -> str:
        return self.client.settings.bandwidth_account_id

    @property
    def legacy_base(self) -> str:
        return self.client.settings.bandwidth_api_base.split("/api/v2")[0].rstrip("/") + "/api"

    async def details(self, tn: str) -> dict[str, Any]:
        data = await self.client.request("GET", f"{self.legacy_base}/tns/{_digits(tn)}/tndetails")
        return data if isinstance(data, dict) else {"raw": data}

    async def list_campaigns(self, page: int = 1, size: int = 25) -> list[dict[str, Any]]:
        """Return account campaigns, with imported-campaign fallback.

        The regular Campaign Management endpoint contains campaigns created under
        Bandwidth CSP management. The imports endpoint contains campaigns shared
        from another CSP. Accounts can use either or both.
        """
        endpoints = [
            f"{self.legacy_base}/accounts/{self.account_id}/campaignManagement/10dlc/campaigns",
            f"{self.legacy_base}/accounts/{self.account_id}/campaignManagement/10dlc/campaigns/imports",
        ]
        campaigns: list[dict[str, Any]] = []
        last_error: Exception | None = None

        def ci(obj: dict[str, Any], *names: str) -> Any:
            lookup = {n.casefold() for n in names}
            for key, value in obj.items():
                if str(key).casefold() in lookup:
                    return value
            return None

        def collect(data: Any) -> None:
            def walk(value: Any) -> None:
                if isinstance(value, list):
                    for item in value:
                        walk(item)
                    return
                if not isinstance(value, dict):
                    return
                campaign_id = ci(value, "CampaignId", "campaignId", "BandwidthId", "bandwidthId")
                if campaign_id:
                    campaigns.append({
                        "id": str(campaign_id),
                        "description": str(ci(value, "Description", "description", "Usecase", "usecase") or ""),
                        "messageClass": str(ci(value, "MessageClass", "messageClass") or ""),
                        "status": str(ci(value, "Status", "status") or ""),
                    })
                    return
                for nested in value.values():
                    if isinstance(nested, (dict, list)):
                        walk(nested)
            walk(data)

        for endpoint in endpoints:
            try:
                data = await self.client.request(
                    "GET", endpoint, params={"page": page, "size": size}
                )
                collect(data)
            except Exception as exc:  # try the other campaign source before failing
                last_error = exc

        unique = {c["id"]: c for c in campaigns}
        if not unique and last_error:
            raise last_error
        return sorted(unique.values(), key=lambda c: (c["description"], c["id"]))

    async def update_routing(
        self,
        tn: str,
        *,
        call_forward: str = "",
        failover_uri: str = "",
        nnid: str = "",
    ) -> Any:
        options: list[str] = []
        if call_forward:
            options.append(f"<CallForward>{escape(call_forward)}</CallForward>")
        if failover_uri:
            options.append(f"<FinalDestinationURI>{escape(failover_uri)}</FinalDestinationURI>")
        if nnid:
            options.append(f"<NNID>{escape(nnid)}</NNID>")
        return await self._submit_options(tn, options)

    async def update_sms(
        self,
        tn: str,
        *,
        sms_active: bool,
        campaign_id: str = "",
    ) -> Any:
        options: list[str] = [f"<Sms>{'on' if sms_active else 'off'}</Sms>"]
        if campaign_id == "__remove__":
            options.append("<A2pSettings><Action>delete</Action></A2pSettings>")
        elif campaign_id:
            options.append(
                "<A2pSettings><Action>asSpecified</Action>"
                f"<CampaignId>{escape(campaign_id)}</CampaignId></A2pSettings>"
            )
        return await self._submit_options(tn, options)

    async def update_portout_passcode(self, tn: str, passcode: str) -> Any:
        value = passcode if passcode else "systemDefault"
        return await self._submit_options(
            tn, [f"<PortOutPasscode>{escape(value)}</PortOutPasscode>"]
        )

    async def _submit_options(self, tn: str, options: list[str]) -> Any:
        body = (
            "<TnOptionOrder><TnOptionGroups><TnOptionGroup>"
            + "".join(options)
            + f"<TelephoneNumbers><TelephoneNumber>{_digits(tn)}</TelephoneNumber></TelephoneNumbers>"
            + "</TnOptionGroup></TnOptionGroups></TnOptionOrder>"
        )
        return await self.client.request(
            "POST",
            f"{self.legacy_base}/accounts/{self.account_id}/tnOptions",
            content=body,
            content_type="application/xml; charset=utf-8",
        )

    async def update_lidb(
        self, tn: str, subscriber_information: str, use_type: str, visibility: str
    ) -> Any:
        body = (
            "<LidbOrder><LidbTnGroups><LidbTnGroup>"
            f"<TelephoneNumbers><TelephoneNumber>{_digits(tn)}</TelephoneNumber></TelephoneNumbers>"
            f"<SubscriberInformation>{escape(subscriber_information)}</SubscriberInformation>"
            f"<UseType>{escape(use_type)}</UseType><Visibility>{escape(visibility)}</Visibility>"
            "</LidbTnGroup></LidbTnGroups></LidbOrder>"
        )
        return await self.client.request(
            "POST",
            f"{self.legacy_base}/accounts/{self.account_id}/lidbs",
            content=body,
            content_type="application/xml; charset=utf-8",
        )

    async def update_dlda(self, tn: str, fields: dict[str, str]) -> Any:
        def tag(name: str, value: str) -> str:
            return f"<{name}>{escape(value)}</{name}>" if value else ""

        body = (
            "<DldaOrder><DldaTnGroups><DldaTnGroup>"
            f"<TelephoneNumbers><TelephoneNumber>{_digits(tn)}</TelephoneNumber></TelephoneNumbers>"
        )
        for name in (
            "ListingType", "SubscriberType", "LastName", "FirstName",
            "HouseNumber", "StreetName", "AddressLine2", "City",
            "StateCode", "Zip", "PlusFour",
        ):
            body += tag(name, fields.get(name, ""))
        body += "</DldaTnGroup></DldaTnGroups></DldaOrder>"
        return await self.client.request(
            "POST",
            f"{self.legacy_base}/accounts/{self.account_id}/dldas",
            content=body,
            content_type="application/xml; charset=utf-8",
        )


def _digits(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
