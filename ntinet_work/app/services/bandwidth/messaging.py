from __future__ import annotations

from typing import Any

from .client import BandwidthClient


class MessagingService:
    """Bandwidth messaging/A2P operations used by the current Bandwidth App.

    Campaign discovery intentionally uses the Numbers V2 messaging-product
    endpoint instead of the separately licensed legacy Campaign Import API.
    """

    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self) -> str:
        return self.client.settings.bandwidth_account_id

    async def list_a2p_campaigns(self) -> list[dict[str, Any]]:
        data = await self.client.request(
            "GET",
            f"/accounts/{self.account_id}/products/messaging/a2pCampaigns/",
            accept="application/xml",
        )
        campaigns = _collect_campaigns(data)
        return sorted(
            (campaign for campaign in campaigns if campaign.get("status") == "ACTIVE"),
            key=lambda campaign: (campaign.get("description", "").casefold(), campaign["id"]),
        )

    @staticmethod
    def extract_tn_sms_settings(details: Any) -> dict[str, Any]:
        """Extract the effective messaging state from TelephoneNumberDetails.

        Bandwidth's TN detail response exposes the authoritative values under
        ``TelephoneNumberDetails/MessagingSettings``.  Use that mapping first;
        older A2pSettings/TNOptions shapes remain fallback-only for compatibility.
        """
        messaging = _find_named_mapping(details, "MessagingSettings") or {}
        a2p = _find_named_mapping(details, "A2pSettings") or {}

        sms_value = _value_ci(messaging, "SmsEnabled")
        campaign_id = _value_ci(messaging, "CampaignId")
        message_class = _value_ci(messaging, "MessageClass")
        fully_provisioned = _value_ci(messaging, "CampaignFullyProvisioned")
        a2p_state = _value_ci(messaging, "A2pState")

        assigned_route = _value_ci(messaging, "AssignedNnRoute")
        if not isinstance(assigned_route, dict):
            assigned_route = {}
        assigned_nnid = _value_ci(assigned_route, "Nnid")
        assigned_route_name = _value_ci(assigned_route, "Name")

        # Compatibility fallbacks for response variants that do not include
        # MessagingSettings.  These must never override explicit TN values.
        if sms_value in (None, ""):
            sms_value = _value_ci(a2p, "Sms", "SmsEnabled")
        if sms_value in (None, ""):
            sms_value = _find_named_value(details, "SmsEnabled", "Sms", "MessagingEnabled")
        if not campaign_id:
            campaign_id = _value_ci(a2p, "CampaignId")
        if not campaign_id:
            campaign_id = _find_named_value(details, "CampaignId")
        if not message_class:
            message_class = _value_ci(a2p, "MessageClass", "A2pMessageClass")
        if not message_class:
            message_class = _find_named_value(details, "MessageClass", "A2pMessageClass")

        active = _as_bool(sms_value, default=bool(campaign_id))
        provisioned = _as_bool(fully_provisioned, default=False)

        return {
            "active": active,
            "raw_sms": sms_value or "",
            "campaign_id": str(campaign_id or ""),
            "message_class": str(message_class or ""),
            "fully_provisioned": provisioned,
            "a2p_state": str(a2p_state or ""),
            "assigned_nnid": str(assigned_nnid or ""),
            "assigned_route_name": str(assigned_route_name or ""),
        }



def _collect_campaigns(data: Any) -> list[dict[str, Any]]:
    campaigns: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return

        campaign_id = _value_ci(value, "CampaignId")
        account_id = _value_ci(value, "AccountId")
        if campaign_id and account_id:
            campaigns.append(
                {
                    "id": str(campaign_id),
                    "description": str(_value_ci(value, "Description") or ""),
                    "account_id": str(account_id),
                    "messageClass": str(_value_ci(value, "MessageClass") or ""),
                    "imported": str(_value_ci(value, "Imported") or "").casefold() == "true",
                    "created_date": str(_value_ci(value, "CreatedDate") or ""),
                    "status": str(_value_ci(value, "Status") or ""),
                }
            )
            return

        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(data)
    return list({campaign["id"]: campaign for campaign in campaigns}.values())


def _find_named_mapping(value: Any, name: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).casefold() == name.casefold() and isinstance(nested, dict):
                return nested
        for nested in value.values():
            found = _find_named_mapping(nested, name)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_named_mapping(nested, name)
            if found is not None:
                return found
    return None


def _find_named_value(value: Any, *names: str) -> Any:
    wanted = {name.casefold() for name in names}
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).casefold() in wanted and nested not in (None, ""):
                return nested
        for nested in value.values():
            found = _find_named_value(nested, *names)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_named_value(nested, *names)
            if found not in (None, ""):
                return found
    return ""


def _as_bool(value: Any, *, default: bool = False) -> bool:
    text = str(value or "").strip().casefold()
    if text in {"on", "true", "yes", "enabled", "active", "1"}:
        return True
    if text in {"off", "false", "no", "disabled", "inactive", "0"}:
        return False
    return default


def _value_ci(mapping: dict[str, Any], *names: str) -> Any:
    wanted = {name.casefold() for name in names}
    for key, value in mapping.items():
        if str(key).casefold() in wanted:
            return value
    return None
