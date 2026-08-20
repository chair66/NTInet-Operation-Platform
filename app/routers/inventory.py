import asyncio
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.dependencies import bw
from app.services.bandwidth import BandwidthAPIError, translate_bandwidth_error
from app.web import render
from app.security import require_bandwidth_site, visible_bandwidth_sites

router = APIRouter()


@router.get("/sites", response_class=HTMLResponse)
async def sites(request: Request):
    error = None
    sites = []
    try:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        location_results = await asyncio.gather(
            *(bw.inventory.list_locations(site.get("id")) for site in sites),
            return_exceptions=True,
        )
        total_results = await asyncio.gather(
            *(bw.inventory.site_total(site.get("id")) for site in sites),
            return_exceptions=True,
        )
        for site, locations, total in zip(sites, location_results, total_results):
            site["portal_locations"] = locations if isinstance(locations, list) else []
            site["portal_number_count"] = total if isinstance(total, int) else 0
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    return render(request, "sites.html", sites=sites, error=error)


@router.get("/sites/{site_id}/locations/{location_id}/numbers", response_class=HTMLResponse)
async def numbers(
    request: Request,
    site_id: int,
    location_id: int,
    site_name: str = "",
    location_name: str = "",
    page: str | None = Query(None),
    size: int = 50,
    q: str = "",
    call_forward: str = "all",
    sms: str = "all",
):
    require_bandwidth_site(request, site_id)
    error = None
    phone_numbers = []

    def configured(value) -> bool:
        if value in (None, "", False, 0):
            return False
        text = str(value).strip().casefold()
        return text not in {"", "none", "no", "false", "off", "disabled", "0", "n/a", "—"}

    try:
        # When filtering, retrieve a larger inventory window so a TN search is
        # useful across the location rather than only the currently displayed page.
        filtered_request = bool(q.strip() or call_forward != "all" or sms != "all")
        fetch_size = 1000 if filtered_request else max(1, min(size, 1000))
        phone_numbers = await bw.inventory.list_numbers(
            site_id, location_id, None if filtered_request else page, fetch_size
        )

        q_digits = "".join(ch for ch in q if ch.isdigit())
        if q_digits:
            phone_numbers = [
                row for row in phone_numbers
                if q_digits in "".join(ch for ch in str(row.get("phoneNumber") or "") if ch.isdigit())
            ]
        if call_forward == "configured":
            phone_numbers = [row for row in phone_numbers if configured(row.get("callForward"))]
        elif call_forward == "none":
            phone_numbers = [row for row in phone_numbers if not configured(row.get("callForward"))]
        if sms == "enabled":
            phone_numbers = [row for row in phone_numbers if configured(row.get("sms"))]
        elif sms == "disabled":
            phone_numbers = [row for row in phone_numbers if not configured(row.get("sms"))]
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    return render(
        request,
        "numbers.html",
        site_name=site_name,
        location_name=location_name,
        phone_numbers=phone_numbers,
        error=error,
        q=q, selected_call_forward=call_forward, selected_sms=sms,
    )


@router.get("/sites/{site_id}/locations/{location_id}/numbers/{tn}", response_class=HTMLResponse)
async def number_detail(request: Request, site_id: int, location_id: int, tn: str, site_name: str = "", location_name: str = "", notice: str = ""):
    require_bandwidth_site(request, site_id)
    error = None
    campaign_error = None
    details = {}
    campaigns = []
    sites = []
    locations_by_site = {}
    try:
        details = await bw.line_features.details(tn)
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        for site in sites:
            try:
                locations_by_site[str(site["id"])] = await bw.inventory.list_locations(site["id"])
            except BandwidthAPIError:
                locations_by_site[str(site["id"])] = []
        try:
            campaigns = await bw.messaging.list_a2p_campaigns()
        except BandwidthAPIError as exc:
            campaign_error = exc.diagnostic
    except BandwidthAPIError as exc:
        error = exc.diagnostic

    def find_value(value, *wanted):
        names = {name.casefold() for name in wanted}
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).casefold() in names and nested not in (None, ""):
                    return nested
            for nested in value.values():
                result = find_value(nested, *wanted)
                if result not in (None, ""):
                    return result
        elif isinstance(value, list):
            for nested in value:
                result = find_value(nested, *wanted)
                if result not in (None, ""):
                    return result
        return ""

    sms_settings = bw.messaging.extract_tn_sms_settings(details)
    current_sms = sms_settings["raw_sms"]
    current_sms_active = sms_settings["active"]
    current_campaign = sms_settings["campaign_id"]
    current_message_class = sms_settings["message_class"]
    campaign_fully_provisioned = sms_settings["fully_provisioned"]
    a2p_state = sms_settings["a2p_state"]
    assigned_nnid = sms_settings["assigned_nnid"]
    assigned_route_name = sms_settings["assigned_route_name"]
    current_passcode = find_value(details, "PortOutPasscode", "portOutPasscode")
    return render(
        request, "number_detail.html", site_id=site_id, location_id=location_id,
        tn=tn, site_name=site_name, location_name=location_name, details=details,
        sites=sites, locations_by_site=locations_by_site, error=error, notice=notice,
        campaigns=campaigns, campaign_error=campaign_error, current_sms=current_sms,
        current_sms_active=current_sms_active, current_campaign=current_campaign, current_message_class=current_message_class,
        campaign_fully_provisioned=campaign_fully_provisioned, a2p_state=a2p_state,
        assigned_nnid=assigned_nnid, assigned_route_name=assigned_route_name,
        current_passcode=current_passcode,
    )


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/move/review", response_class=HTMLResponse)
async def review_number_move(request: Request, site_id: int, location_id: int, tn: str, destination_site_id: int = Form(...), destination_location_id: int = Form(...), customer_order_id: str = Form(...), site_name: str = Form(""), location_name: str = Form("")):
    require_bandwidth_site(request, site_id)
    require_bandwidth_site(request, destination_site_id)
    sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
    destination_site = next((s for s in sites if str(s.get("id")) == str(destination_site_id)), {"id": destination_site_id, "name": str(destination_site_id)})
    locations = await bw.inventory.list_locations(destination_site_id)
    destination_location = next((l for l in locations if str(l.get("id")) == str(destination_location_id)), {"id": destination_location_id, "name": str(destination_location_id)})
    return render(request, "number_move_review.html", site_id=site_id, location_id=location_id, tn=tn, site_name=site_name, location_name=location_name, destination_site=destination_site, destination_location=destination_location, customer_order_id=customer_order_id)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/move", response_class=HTMLResponse)
async def move_number(request: Request, site_id: int, location_id: int, tn: str, destination_site_id: int = Form(...), destination_location_id: int = Form(...), customer_order_id: str = Form(...), site_name: str = Form(""), location_name: str = Form("")):
    require_bandwidth_site(request, site_id)
    try:
        require_bandwidth_site(request, destination_site_id)
        await bw.inventory.move_number(tn, destination_site_id, destination_location_id, customer_order_id)
        return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice=Move%20number%20order%20submitted", 303)
    except BandwidthAPIError as exc:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        destination_site = next((s for s in sites if str(s.get("id")) == str(destination_site_id)), {"id": destination_site_id, "name": str(destination_site_id)})
        locations = await bw.inventory.list_locations(destination_site_id)
        destination_location = next((l for l in locations if str(l.get("id")) == str(destination_location_id)), {"id": destination_location_id, "name": str(destination_location_id)})
        return render(request, "number_move_review.html", site_id=site_id, location_id=location_id, tn=tn, site_name=site_name, location_name=location_name, destination_site=destination_site, destination_location=destination_location, customer_order_id=customer_order_id, error=exc.diagnostic)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/routing")
async def update_number_routing(request: Request, site_id: int, location_id: int, tn: str, callForward: str = Form(""), failoverUri: str = Form(""), nnid: str = Form(""), site_name: str = Form(""), location_name: str = Form("")):
    require_bandwidth_site(request, site_id)
    await bw.line_features.update_routing(tn, call_forward=callForward or "systemDefault", failover_uri=failoverUri or "systemDefault", nnid=nnid or "unchanged")
    return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice=Routing%20settings%20order%20submitted", 303)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/sms")
async def update_number_sms(
    request: Request,
    site_id: int,
    location_id: int,
    tn: str,
    sms_active: str = Form(...),
    campaign_id: str = Form(""),
    site_name: str = Form(""),
    location_name: str = Form(""),
):
    require_bandwidth_site(request, site_id)
    active = sms_active.strip().casefold() == "yes"
    selected_campaign = campaign_id.strip()
    if not active and selected_campaign not in ("", "__remove__"):
        selected_campaign = "__remove__"
    await bw.line_features.update_sms(
        tn, sms_active=active, campaign_id=selected_campaign
    )
    return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice=SMS%20settings%20order%20submitted", 303)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/portout-passcode")
async def update_portout_passcode(request: Request, site_id: int, location_id: int, tn: str, passcode: str = Form(""), site_name: str = Form(""), location_name: str = Form("")):
    require_bandwidth_site(request, site_id)
    cleaned = passcode.strip()
    if cleaned and (len(cleaned) < 4 or len(cleaned) > 10 or not cleaned.isalnum()):
        return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice=Passcode%20must%20be%204-10%20alphanumeric%20characters", 303)
    await bw.line_features.update_portout_passcode(tn, cleaned)
    message = "Port-out passcode order submitted" if cleaned else "Port-out passcode removal submitted"
    return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice={message.replace(' ', '%20')}", 303)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/lidb")
async def update_number_lidb(request: Request, site_id: int, location_id: int, tn: str, subscriberInformation: str = Form(...), useType: str = Form("BUSINESS"), visibility: str = Form("PUBLIC"), site_name: str = Form(""), location_name: str = Form("")):
    require_bandwidth_site(request, site_id)
    await bw.line_features.update_lidb(tn, subscriberInformation, useType, visibility)
    return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={site_name}&location_name={location_name}&notice=LIDB%20order%20submitted", 303)


@router.post("/sites/{site_id}/locations/{location_id}/numbers/{tn}/dlda")
async def update_number_dlda(request: Request, site_id: int, location_id: int, tn: str):
    require_bandwidth_site(request, site_id)
    form = await request.form()
    fields = {key: str(value) for key, value in form.items()}
    await bw.line_features.update_dlda(tn, fields)
    return RedirectResponse(f"/sites/{site_id}/locations/{location_id}/numbers/{tn}?site_name={fields.get('site_name','')}&location_name={fields.get('location_name','')}&notice=Directory%20listing%20order%20submitted", 303)




@router.get("/my-numbers/search", response_class=HTMLResponse)
async def search_my_number(request: Request, phone_number: str = ""):
    query_digits = "".join(ch for ch in phone_number if ch.isdigit())
    if len(query_digits) == 11 and query_digits.startswith("1"):
        query_digits = query_digits[1:]
    matches = []
    error = None
    if query_digits:
        try:
            all_sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
            for site in all_sites:
                try:
                    locations = await bw.inventory.list_locations(site.get("id"))
                except BandwidthAPIError:
                    continue
                for location in locations:
                    try:
                        numbers = await bw.inventory.list_numbers(site.get("id"), location.get("id"), size=5000)
                    except BandwidthAPIError:
                        continue
                    for number in numbers:
                        digits = "".join(ch for ch in str(number.get("phoneNumber", "")) if ch.isdigit())
                        if digits.endswith(query_digits):
                            matches.append({"site": site, "location": location, "number": number})
        except BandwidthAPIError as exc:
            error = exc.diagnostic
    return render(request, "number_search.html", phone_number=phone_number, matches=matches, searched=bool(query_digits), error=error)



def _order_items(data):
    found = []
    def get_ci(item, *keys):
        wanted = {key.casefold() for key in keys}
        for key, value in item.items():
            if str(key).casefold() in wanted:
                return value
        return None
    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return
        order_id = get_ci(value, "orderId", "OrderId", "id")
        status = get_ci(value, "orderStatus", "OrderStatus", "status", "Status")
        if order_id and status:
            found.append({
                **value,
                "orderId": str(order_id),
                "status": str(status),
                "customerOrderId": get_ci(value, "customerOrderId", "CustomerOrderId") or "",
                "createdDate": get_ci(value, "createdDate", "CreatedDate", "orderCreateDate", "OrderCreateDate") or "",
                "completedNumbers": get_ci(value, "completedNumbers", "CompletedNumbers", "completedQuantity", "TotalQuantity") or "",
            })
            return
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)
    walk(data)
    return list({item["orderId"]: item for item in found}.values())


@router.get("/orders", response_class=HTMLResponse)
async def order_history(request: Request, q: str = ""):
    orders, error = [], None
    try:
        orders = _order_items(await bw.ordering.list(page=1, size=300))
        if q.strip():
            needle = q.strip().casefold()
            orders = [item for item in orders if needle in str(item.get("orderId", "")).casefold() or needle in str(item.get("customerOrderId", "")).casefold()]
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    return render(request, "orders.html", orders=orders, q=q, error=error)

@router.get("/available-numbers", response_class=HTMLResponse)
async def available(
    request: Request,
    searchMode: str = "area",
    areaCode: str = "",
    quantity: str = "",
    state: str = "",
    city: str = "",
    rateCenter: str = "",
):
    search_mode = searchMode if searchMode in {"area", "city", "rate", "advanced"} else "area"

    # Each simple search mode is intentionally isolated. Hidden or stale fields
    # from another tab must never be sent to Bandwidth. Combined filters are
    # supported only by Advanced search.
    raw_values = {
        "areaCode": areaCode.strip(),
        "quantity": quantity.strip(),
        "state": state.strip().upper(),
        "city": city.strip(),
        "rateCenter": rateCenter.strip(),
    }
    mode_fields = {
        "area": {"areaCode"},
        "city": {"state", "city"},
        "rate": {"state", "rateCenter"},
        "advanced": {"areaCode", "state", "city", "rateCenter"},
    }
    active_fields = mode_fields[search_mode]
    values = {
        key: (value if key == "quantity" or key in active_fields else "")
        for key, value in raw_values.items()
    }
    values["searchMode"] = search_mode
    has_search_criteria = any(values.get(key, "").strip() for key in active_fields)
    searched = has_search_criteria
    results, sites, error, notice, rate_centers = [], [], None, None, []
    try:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        if has_search_criteria:
            if rateCenter.strip() and not state.strip():
                discovery_query = {"areaCode": areaCode, "city": city, "quantity": 100}
                discovery = await bw.inventory.search_available_numbers(discovery_query)
                matched = next((item for item in discovery if str(item.get("rateCenter", "")).strip().upper() == rateCenter.strip().upper()), None)
                if matched and matched.get("state"):
                    state = str(matched.get("state")).strip().upper()
                    values["state"] = state
            search_query = {key: values[key] for key in (*active_fields, "quantity") if values.get(key)}
            results = await bw.inventory.search_available_numbers(search_query)
            rate_centers = sorted({str(item.get("rateCenter", "")).strip() for item in results if str(item.get("rateCenter", "")).strip()})
        elif quantity or any(key in request.query_params for key in ("areaCode", "state", "city", "rateCenter", "searchMode")):
            required_copy = {
                "area": "Enter an area code.",
                "city": "Enter a state and city.",
                "rate": "Enter a state and rate center.",
                "advanced": "Enter at least one search criterion.",
            }
            notice = required_copy[search_mode]
    except BandwidthAPIError as exc:
        error = translate_bandwidth_error(
            exc, operation="available_number_search", context=values
        )
    return render(request, "available.html", values=values, searched=searched, results=results, sites=sites, rate_centers=rate_centers, error=error, notice=notice)


@router.get("/available-numbers/rate-centers")
async def available_rate_centers(areaCode: str = "", state: str = "", city: str = ""):
    if not any((areaCode.strip(), state.strip(), city.strip())):
        return JSONResponse({"rateCenters": []})
    query = {"areaCode": areaCode, "state": state, "city": city, "quantity": 100}
    try:
        results = await bw.inventory.search_available_numbers(query)
        mapping = {}
        for item in results:
            rc = str(item.get("rateCenter", "")).strip()
            st = str(item.get("state", "")).strip().upper()
            if rc:
                mapping.setdefault(rc, st)
        rate_centers = [{"name": rc, "state": mapping.get(rc, "")} for rc in sorted(mapping)]
        return JSONResponse({"rateCenters": rate_centers})
    except BandwidthAPIError as exc:
        friendly = translate_bandwidth_error(
            exc,
            operation="available_number_search",
            context={"areaCode": areaCode, "state": state, "city": city},
        )
        return JSONResponse(
            {"rateCenters": [], "error": friendly},
            status_code=200,
        )


@router.get("/available-numbers/filter-options")
async def available_filter_options(areaCode: str = "", state: str = ""):
    if not any((areaCode.strip(), state.strip())):
        return JSONResponse({"cities": [], "rateCenters": []})
    query = {"areaCode": areaCode, "state": state, "quantity": 100}
    try:
        results = await bw.inventory.search_available_numbers(query)
        cities = sorted({str(item.get("city", "")).strip() for item in results if str(item.get("city", "")).strip()})
        rate_centers = sorted({str(item.get("rateCenter", "")).strip() for item in results if str(item.get("rateCenter", "")).strip()})
        return JSONResponse({"cities": cities, "rateCenters": rate_centers})
    except BandwidthAPIError as exc:
        friendly = translate_bandwidth_error(
            exc, operation="available_number_search", context=query
        )
        return JSONResponse({"cities": [], "rateCenters": [], "error": friendly})


@router.post("/available-numbers/review", response_class=HTMLResponse)
async def review_available_numbers(
    request: Request,
    site_id: int = Form(...),
    phone_numbers: list[str] = Form(...),
):
    require_bandwidth_site(request, site_id)
    sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
    site = next((item for item in sites if str(item.get("id")) == str(site_id)), None)
    return render(
        request,
        "available_review.html",
        site=site or {"id": site_id, "name": f"Sub Account {site_id}"},
        phone_numbers=phone_numbers,
    )


@router.post("/available-numbers/order", response_class=HTMLResponse)
async def order_available_numbers(
    request: Request,
    site_id: int = Form(...),
    phone_numbers: list[str] = Form(...),
):
    values = {"areaCode": "", "quantity": "", "state": "", "city": "", "rateCenter": ""}
    sites, error, notice = [], None, None
    try:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        require_bandwidth_site(request, site_id)
        response = await bw.ordering.create_existing_number_order(site_id, phone_numbers)
        order_id = None
        if isinstance(response, dict):
            order_id = response.get("id") or response.get("orderId")
            order = response.get("Order") or response.get("order")
            if isinstance(order, dict):
                order_id = order_id or order.get("id") or order.get("orderId")
        notice = f"Number order submitted successfully{f' — Order {order_id}' if order_id else ''}."
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    return render(request, "available.html", values=values, searched=False, results=[], sites=sites, error=error, notice=notice)
