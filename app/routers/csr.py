from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies import bw
from app.services.bandwidth import BandwidthAPIError
from app.web import render
from app.security import require_platform_staff

router = APIRouter(prefix="/csrs")


@router.get("", response_class=HTMLResponse)
async def list_csrs(request: Request):
    require_platform_staff(request)
    try:
        data = await bw.csr.list()
        return render(request, "csrs.html", csr_orders=data.get("csrOrders", []), error=None)
    except BandwidthAPIError as exc:
        return render(request, "csrs.html", csr_orders=[], error=exc.diagnostic)


@router.get("/new", response_class=HTMLResponse)
async def new_csr(request: Request):
    require_platform_staff(request)
    return render(request, "csr_new.html", error=None)


@router.post("/new")
async def create_csr(
    request: Request,
    workingOrBillingTelephoneNumber: str = Form(...),
    accountNumber: str = Form(""),
    accountTelephoneNumber: str = Form(""),
    endUserName: str = Form(""),
    authorizingUserName: str = Form(""),
    customerCode: str = Form(""),
    endUserPin: str = Form(""),
    endUserPassword: str = Form(""),
    addressLine1: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    zipCode: str = Form(""),
    typeOfService: str = Form("residential"),
):
    require_platform_staff(request)
    payload = {
        key: value for key, value in locals().items()
        if key not in {"request"} and value != ""
    }
    try:
        await bw.csr.create(payload)
        return RedirectResponse("/csrs", 303)
    except BandwidthAPIError as exc:
        return render(request, "csr_new.html", error=exc.diagnostic)
