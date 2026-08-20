from __future__ import annotations

from typing import Any

from .errors import BandwidthAPIError


def _first_api_error(payload: Any) -> tuple[str, str]:
    """Return the first provider error code and description from nested payloads."""
    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, dict):
                    code = str(item.get("code") or "")
                    message = str(item.get("description") or item.get("message") or "")
                    if code or message:
                        return code, message
        for value in payload.values():
            code, message = _first_api_error(value)
            if code or message:
                return code, message
    elif isinstance(payload, list):
        for value in payload:
            code, message = _first_api_error(value)
            if code or message:
                return code, message
    return "", ""


def translate_bandwidth_error(
    exc: BandwidthAPIError,
    *,
    operation: str = "request",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Translate a Bandwidth API exception into safe, actionable UI copy.

    Raw request/response data remains available in ``technical`` so support staff
    can troubleshoot without exposing API-oriented language as the primary error.
    """
    context = context or {}
    status = exc.status_code
    raw_message = str(exc)
    searchable = f"{raw_message} {exc.payload}".casefold()
    api_error_code, api_error_message = _first_api_error(exc.payload)

    title = "Bandwidth request could not be completed"
    message = "Bandwidth could not complete the request. Review the search criteria and try again."
    suggestions: list[str] = []

    if operation == "port_submit":
        title = "Port request could not be submitted"
        if status == 400:
            message = "The request needs one or more corrections before it can be submitted. Your draft was saved automatically."
            suggestions = ["Open the saved draft, review the request details, and submit it again."]
        elif status in (401, 403):
            message = "The porting service could not authorize this request. Your draft was saved automatically."
        elif status == 409:
            message = "The request conflicts with an existing or active port order. Your draft was saved automatically."
        elif status == 429:
            message = "The porting service is temporarily busy. Your draft was saved automatically; try again shortly."
        elif status and status >= 500:
            message = "The porting service is temporarily unavailable. Your draft was saved automatically."
        else:
            message = "The request could not be accepted. Your draft was saved automatically."
    elif operation == "available_number_search":
        area_code = str(context.get("areaCode") or "").strip()
        city = str(context.get("city") or "").strip()
        state = str(context.get("state") or "").strip().upper()

        if status == 400 and area_code and city:
            title = "Search filters do not match"
            location = f"{city}{', ' + state if state else ''}"
            message = (
                f"{location} may not be served by area code {area_code}, or Bandwidth "
                "does not have inventory for that filter combination."
            )
            suggestions = [
                f"Search area code {area_code} without the city filter.",
                f"Search {location} without specifying an area code.",
                "Choose a city or rate center returned by the available-filter lookup.",
            ]
        elif status == 400:
            title = "The search criteria were not accepted"
            message = "One or more number-search filters are incompatible or invalid."
            suggestions = [
                "Remove one optional filter and search again.",
                "Use either area code, city/state, or rate center as the primary search method.",
            ]
        elif status == 404:
            title = "No matching number inventory was found"
            message = "Bandwidth did not find an inventory resource matching this search."
        elif status == 429:
            title = "Too many number searches"
            message = "Bandwidth is temporarily limiting requests. Wait a moment and try again."
    elif status in (401, 403):
        title = "Bandwidth authentication or permission error"
        message = "The portal could not access this Bandwidth feature with its current API credentials."
        suggestions = ["Verify the API user's role and account access in Bandwidth."]
    elif status == 404:
        title = "Bandwidth resource not found"
        message = "The requested Bandwidth resource or endpoint could not be found."
    elif status == 409:
        title = "The requested change conflicts with the current state"
        message = "Bandwidth could not apply the change because the resource is already assigned or being modified."
    elif status == 429:
        title = "Bandwidth rate limit reached"
        message = "Bandwidth is temporarily limiting requests. Try again shortly."
    elif status and status >= 500:
        title = "Bandwidth service is temporarily unavailable"
        message = "Bandwidth encountered a server-side problem. No portal data was changed."

    # Preserve useful provider text when it is clearly human-readable, but never
    # make it the main message for the known friendly cases above.
    provider_message = api_error_message or (raw_message if raw_message and not raw_message.startswith("Bandwidth returned HTTP") else "")

    return {
        "title": title,
        "message": message,
        "suggestions": suggestions,
        "provider_message": provider_message,
        "status_code": status,
        "error_code": api_error_code,
        "technical": exc.diagnostic,
    }
