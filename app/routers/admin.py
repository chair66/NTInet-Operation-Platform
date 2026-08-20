import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.dependencies import bw
from app.providers.netsapiens import NETSAPIENS_API_LOG
from app.web import render
from app.security import require_permission, require_platform_staff

router = APIRouter(prefix="/admin")


@router.get("/api-log", response_class=HTMLResponse)
async def api_log(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    events = sorted(
        list(bw.client.api_log) + list(NETSAPIENS_API_LOG),
        key=lambda event: event.get("timestamp", ""),
        reverse=True,
    )
    return render(request, "admin/api_log.html", events=events, error=None)


@router.get("/api-log/{event_index}", response_class=HTMLResponse)
async def api_log_detail(request: Request, event_index: int):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    events = sorted(
        list(bw.client.api_log) + list(NETSAPIENS_API_LOG),
        key=lambda item: item.get("timestamp", ""),
        reverse=True,
    )
    event = events[event_index] if 0 <= event_index < len(events) else None
    pretty_payload = json.dumps(event.get("payload"), indent=2, default=str) if event else ""
    return render(request, "admin/api_log_detail.html", event=event, pretty_payload=pretty_payload, error=None)


@router.get("/system-diagnostics", response_class=HTMLResponse)
async def system_diagnostics(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    from sqlalchemy import text
    from app.config import get_settings
    from app.database import SessionLocal

    settings = get_settings()
    database = {"ok": False, "message": "Not tested"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        database = {"ok": True, "message": "Database connection succeeded."}
    except Exception as exc:
        database = {"ok": False, "message": str(exc)}

    smtp_configured = bool(settings.smtp_host and settings.smtp_from)
    default_recipient = (
        settings.port_notification_email
        or getattr(request.state.user, "email", "")
    )
    return render(
        request,
        "admin/system_diagnostics.html",
        database=database,
        smtp={
            "configured": smtp_configured,
            "host": settings.smtp_host or "Not configured",
            "port": settings.smtp_port,
            "from_address": settings.smtp_from or "Not configured",
            "ssl": settings.smtp_use_ssl,
            "username_configured": bool(settings.smtp_username),
        },
        bandwidth={"tested": False, "ok": None, "message": "Run diagnostics to test connectivity."},
        smtp_test={"tested": False, "ok": None, "message": "Run diagnostics to test connection and authentication."},
        default_recipient=default_recipient,
        notice=None,
        error=None,
    )


@router.post("/system-diagnostics/run", response_class=HTMLResponse)
async def run_system_diagnostics(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    from sqlalchemy import text
    from app.config import get_settings
    from app.database import SessionLocal
    from app.services.notifications import test_smtp_connection

    settings = get_settings()
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        database = {"ok": True, "message": "Database connection succeeded."}
    except Exception as exc:
        database = {"ok": False, "message": str(exc)}

    smtp_result = test_smtp_connection()
    try:
        sites = await bw.inventory.list_sites()
        bandwidth = {
            "tested": True,
            "ok": True,
            "message": f"API connection succeeded. {len(sites)} sub-account(s) returned.",
        }
    except Exception as exc:
        bandwidth = {"tested": True, "ok": False, "message": str(exc)}

    default_recipient = settings.port_notification_email or getattr(request.state.user, "email", "")
    return render(
        request,
        "admin/system_diagnostics.html",
        database=database,
        smtp={
            "configured": bool(settings.smtp_host and settings.smtp_from),
            "host": settings.smtp_host or "Not configured",
            "port": settings.smtp_port,
            "from_address": settings.smtp_from or "Not configured",
            "ssl": settings.smtp_use_ssl,
            "username_configured": bool(settings.smtp_username),
        },
        bandwidth=bandwidth,
        smtp_test={"tested": True, "ok": smtp_result.ok, "message": smtp_result.message},
        default_recipient=default_recipient,
        notice="Diagnostics completed.",
        error=None,
    )


@router.post("/system-diagnostics/test-email", response_class=HTMLResponse)
async def system_diagnostics_test_email(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    from fastapi import Form
    from sqlalchemy import text
    from app.config import get_settings
    from app.database import SessionLocal
    from app.services.notifications import send_test_email

    form = await request.form()
    recipient = str(form.get("recipient") or "").strip()
    settings = get_settings()
    result = send_test_email([recipient], app_version=settings.app_version)

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        database = {"ok": True, "message": "Database connection succeeded."}
    except Exception as exc:
        database = {"ok": False, "message": str(exc)}

    return render(
        request,
        "admin/system_diagnostics.html",
        database=database,
        smtp={
            "configured": bool(settings.smtp_host and settings.smtp_from),
            "host": settings.smtp_host or "Not configured",
            "port": settings.smtp_port,
            "from_address": settings.smtp_from or "Not configured",
            "ssl": settings.smtp_use_ssl,
            "username_configured": bool(settings.smtp_username),
        },
        bandwidth={"tested": False, "ok": None, "message": "Run diagnostics to test connectivity."},
        smtp_test={"tested": True, "ok": result.ok, "message": result.message},
        default_recipient=recipient,
        notice=(f"Test email sent to {recipient}." if result.ok else None),
        email_error=(None if result.ok else result.message),
        error=None,
    )


@router.get("/providers", response_class=HTMLResponse)
async def provider_dashboard(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    from app.providers import provider_registry

    providers = [provider.health() for provider in provider_registry.all()]
    return render(
        request,
        "admin/providers.html",
        providers=providers,
        checks_run=False,
        notice=None,
        error=None,
    )


@router.post("/providers/check", response_class=HTMLResponse)
async def provider_dashboard_check(request: Request):
    require_permission(request, "admin.api_logs")
    require_platform_staff(request)
    from dataclasses import asdict
    from app.providers import provider_registry

    providers = []
    for provider in provider_registry.all():
        providers.append(asdict(await provider.check_health()))

    return render(
        request,
        "admin/providers.html",
        providers=providers,
        checks_run=True,
        notice="Provider health checks completed.",
        error=None,
    )
