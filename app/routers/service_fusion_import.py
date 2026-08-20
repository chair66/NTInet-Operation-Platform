from __future__ import annotations

import json
import secrets
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from app.database import SessionLocal
from app.security import require_permission, require_platform_staff
from app.security import context_from_request
from app.services.service_fusion_import import CUSTOMER_HEADERS, LOCATION_HEADERS, ServiceFusionImportService, parse_csv_bytes
from app.web import render

router = APIRouter(prefix="/admin/imports/service-fusion", tags=["Administration"])
IMPORT_ROOT = Path("data/service_fusion_imports")


def _require(request: Request) -> None:
    require_permission(request, "admin.organizations")
    require_platform_staff(request)


def _paths(token: str) -> tuple[Path, Path]:
    safe = "".join(ch for ch in token if ch.isalnum() or ch in "-_")
    if safe != token or not safe:
        raise HTTPException(status_code=400, detail="Invalid import token.")
    folder = IMPORT_ROOT / safe
    return folder / "customers.csv", folder / "locations.csv"


def _load(token: str):
    customer_path, location_path = _paths(token)
    if not customer_path.is_file():
        raise HTTPException(status_code=404, detail="Import preview has expired or is missing.")
    customers, customer_headers = parse_csv_bytes(customer_path.read_bytes())
    locations, location_headers = parse_csv_bytes(location_path.read_bytes()) if location_path.is_file() else ([], [])
    return customers, customer_headers, locations, location_headers


@router.get("")
async def import_home(request: Request, token: str = "", done: str = ""):
    _require(request)
    preview = None
    error = None
    if token:
        try:
            customers, customer_headers, locations, location_headers = _load(token)
            with SessionLocal() as db:
                preview = ServiceFusionImportService(db, context_from_request(request)).preview(customers, locations, token)
        except Exception as exc:
            error = str(exc)
    result = request.session.pop("service_fusion_import_result", None) if done else None
    return render(request, "admin/service_fusion_import.html", preview=preview, import_error=error, result=result,
                  expected_customer_headers=sorted(CUSTOMER_HEADERS), expected_location_headers=sorted(LOCATION_HEADERS), token=token)


@router.post("/preview")
async def preview_import(request: Request, customers_file: UploadFile = File(...), locations_file: UploadFile | None = File(None)):
    _require(request)
    if not (customers_file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Customer & Contact export must be a CSV file.")
    customer_content = await customers_file.read()
    location_content = await locations_file.read() if locations_file and locations_file.filename else b""
    customer_rows, customer_headers = parse_csv_bytes(customer_content)
    missing = sorted(CUSTOMER_HEADERS - set(customer_headers))
    # Required identity fields; optional columns may be absent in older SF exports.
    critical = [name for name in ("Customer Name", "PlatCustomerID") if name in missing]
    if critical:
        raise HTTPException(status_code=400, detail=f"Customer CSV is missing required column(s): {', '.join(critical)}")
    if location_content:
        location_rows, location_headers = parse_csv_bytes(location_content)
        critical_locations = [name for name in ("Customer Name", "Address 1") if name not in location_headers]
        if critical_locations:
            raise HTTPException(status_code=400, detail=f"Locations CSV is missing required column(s): {', '.join(critical_locations)}")
    token = secrets.token_urlsafe(18)
    customer_path, location_path = _paths(token)
    customer_path.parent.mkdir(parents=True, exist_ok=True)
    customer_path.write_bytes(customer_content)
    if location_content:
        location_path.write_bytes(location_content)
    return RedirectResponse(f"/admin/imports/service-fusion?token={token}", status_code=303)


@router.post("/commit")
async def commit_import(request: Request, token: str = Form(...)):
    _require(request)
    customers, customer_headers, locations, location_headers = _load(token)
    with SessionLocal() as db:
        service = ServiceFusionImportService(db, context_from_request(request))
        preview = service.preview(customers, locations, token)
        try:
            result = await service.commit(customers, locations, preview)
            db.commit()
        except Exception:
            db.rollback()
            raise
    request.session["service_fusion_import_result"] = result
    customer_path, location_path = _paths(token)
    try:
        if customer_path.exists(): customer_path.unlink()
        if location_path.exists(): location_path.unlink()
        if customer_path.parent.exists(): customer_path.parent.rmdir()
    except OSError:
        pass
    return RedirectResponse("/admin/imports/service-fusion?done=1", status_code=303)
