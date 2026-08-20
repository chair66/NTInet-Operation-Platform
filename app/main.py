from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_database
from app.database.models import User
from app.database.seed import seed_database
from app.logging_config import configure_logging
from app.modules import register_builtin_modules, user_can_access_module
from app.providers import register_builtin_providers
from app.routers import (
    admin, auth, bandwidth_webhooks, catalog, communication_profiles, conversations,
    csr, customers, dashboard, digicloud, identity, inventory, jobs, mobile, notifications,
    partner_portal, plume, porting, tickets, service_fusion_import, platypus_sync,
)
from app.web import render


configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_builtin_modules()
    register_builtin_providers()
    init_database()
    with SessionLocal() as db:
        seed_database(db)
    watcher_task = None
    digicloud_watcher_task = None
    if settings.platypus_customer_watcher_enabled and settings.platypus_api_url:
        from app.services.platypus_bootstrap import start_watcher, stop_watcher
        watcher_statuses = {value.strip() for value in settings.platypus_customer_watcher_statuses.split(",") if value.strip()}
        watcher_task = start_watcher(settings.platypus_customer_watcher_seconds, watcher_statuses)
    if (
        settings.digicloud_user_reconcile_enabled
        and settings.netsapiens_api_url
        and settings.netsapiens_token
    ):
        from app.services.digicloud_reconciliation import start_watcher as start_digicloud_watcher
        digicloud_watcher_task = start_digicloud_watcher(
            settings.digicloud_user_reconcile_seconds
        )
    try:
        yield
    finally:
        if watcher_task is not None:
            from app.services.platypus_bootstrap import stop_watcher
            await stop_watcher()
        if digicloud_watcher_task is not None:
            from app.services.digicloud_reconciliation import stop_watcher as stop_digicloud_watcher
            await stop_digicloud_watcher()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

PUBLIC_PATHS = {
    "/login",
    "/health",
    "/mfa/setup",
    "/mfa/challenge",
    "/mfa/recovery-codes",
    "/ports/webhooks/bandwidth",
    "/estimate/accept/",
    "/api/webhooks/bandwidth/",
}

MODULE_PATHS = (
    ("/admin", "administration"),
    ("/identity", "administration"),
    ("/available-numbers", "lnp-management"),
    ("/sites", "lnp-management"),
    ("/ports", "lnp-management"),
    ("/csrs", "lnp-management"),
    ("/mobile", "nti-mobile"),
    ("/digicloud", "digicloud"),
)


def module_for_path(path: str) -> str | None:
    if path == "/":
        return "dashboard"

    # Organization and reseller administrators may manage users within
    # their own organization. Access is controlled by the admin.users
    # permission and UserService organization scoping, not by the
    # platform-only Administration module assignment.
    if path.startswith("/admin/users"):
        return None

    for prefix, module_slug in MODULE_PATHS:
        if path.startswith(prefix):
            return module_slug

    return None


def permission_for_path(path: str, method: str) -> str | None:
    is_get = method.upper() == "GET"

    if path.startswith("/customers") or path.startswith("/api/customers"):
        return "customers.read"

    if path.startswith("/available-numbers"):
        return "numbers.buy"

    if path.startswith("/sites"):
        return "numbers.read" if is_get else "numbers.features"

    if path.startswith("/ports/new"):
        return "ports.create"

    if path.startswith("/ports"):
        return "ports.read" if is_get else "ports.manage"

    if path.startswith("/csrs"):
        return "csr.read" if is_get else "csr.create"

    if path.startswith("/digicloud/admin/settings") or path.startswith("/digicloud/admin/device-models"):
        return "digicloud.settings"

    if path.startswith("/digicloud/users"):
        return "digicloud.users.manage"

    if path.startswith("/digicloud/phone-hardware"):
        return "digicloud.hardware.read" if is_get else "digicloud.hardware.manage"

    if path.startswith("/digicloud/phone-numbers") or path.startswith("/digicloud/numbers"):
        return "digicloud.numbers.read" if is_get else "digicloud.numbers.manage"

    if path.startswith("/digicloud/domains"):
        if path.endswith("/delete"):
            return "digicloud.domains.delete"
        return "digicloud.domains.read" if is_get else "digicloud.domains.manage"

    if path in {"/digicloud", "/digicloud/"}:
        return "digicloud.view"

    if path.startswith("/mobile/orders/new"):
        return "nti_mobile.orders.create"

    if path.startswith("/mobile/orders"):
        return "nti_mobile.orders.read" if is_get else "nti_mobile.orders.manage"

    if path.startswith("/mobile/customers"):
        return "nti_mobile.customers.read" if is_get else "nti_mobile.customers.manage"

    if path.startswith("/mobile/lines"):
        return "nti_mobile.lines.read" if is_get else "nti_mobile.lines.manage"

    if path.startswith("/mobile/sims"):
        return "nti_mobile.sims.read" if is_get else "nti_mobile.sims.manage"

    if path.startswith("/mobile/numbers"):
        return "nti_mobile.numbers.read" if is_get else "nti_mobile.numbers.manage"

    if path.startswith("/mobile/plans"):
        return "nti_mobile.plans.read" if is_get else "nti_mobile.plans.manage"

    if path.startswith("/mobile/ports/new"):
        return "nti_mobile.ports.create"

    if path.startswith("/mobile/ports"):
        return "nti_mobile.ports.read" if is_get else "nti_mobile.ports.manage"

    if path.startswith("/mobile/exceptions"):
        return (
            "nti_mobile.exceptions.read"
            if is_get
            else "nti_mobile.exceptions.manage"
        )

    if path.startswith("/mobile/settings"):
        return "nti_mobile.settings"

    if path in {"/mobile", "/mobile/"}:
        return "nti_mobile.dashboard"

    if path == "/":
        return "dashboard.read"

    return None


def _browser_request(request: Request) -> bool:
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/ports/webhooks/"):
        return False
    accept = (request.headers.get("accept") or "").lower()
    return "text/html" in accept or accept in {"", "*/*"}


def _access_denied_response(request: Request, detail: str, status_code: int = 403):
    if not _browser_request(request):
        return JSONResponse({"detail": detail}, status_code=status_code)
    return render(
        request,
        "errors/access_denied.html",
        status_code=status_code,
        access_detail=detail,
    )


@app.exception_handler(HTTPException)
async def friendly_http_exception(request: Request, exc: HTTPException):
    if exc.status_code in {401, 403} and getattr(request.state, "user", None):
        return _access_denied_response(request, str(exc.detail), exc.status_code)
    if not _browser_request(request):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    if exc.status_code == 401:
        return RedirectResponse(f"/login?next={quote(request.url.path)}", status_code=303)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    request.state.user = None
    user_id = request.session.get("user_id")

    if user_id:
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(
                    User.id == int(user_id),
                    User.active.is_(True),
                )
            )

            if user and user.organization.active:
                _ = user.organization.name
                _ = tuple(user.organization.modules)
                _ = user.permissions
                db.expunge(user)
                request.state.user = user
            else:
                request.session.clear()

    path = request.url.path

    if request.state.user:
        module_slug = module_for_path(path)

        if module_slug and not user_can_access_module(
            request.state.user,
            module_slug,
        ):
            return _access_denied_response(
                request,
                "Your organization does not have access to this module.",
                403,
            )

        permission = permission_for_path(path, request.method)

        if permission and not request.state.user.can(permission):
            return _access_denied_response(
                request,
                "You do not have permission to access this resource.",
                403,
            )

    if (
        not request.state.user
        and path not in PUBLIC_PATHS
        and not path.startswith("/static/")
        and not path.startswith("/estimate/accept/")
        and not path.startswith("/user-signatures/")
        and not path.startswith("/api/webhooks/bandwidth/")
    ):
        if path.startswith("/api/"):
            return JSONResponse(
                {"detail": "Authentication required"},
                status_code=401,
            )

        return RedirectResponse(
            f"/login?next={quote(path)}",
            status_code=303,
        )

    return await call_next(request)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.app_env.lower() == "production",
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(customers.api_router)
app.include_router(tickets.router)
app.include_router(jobs.router)
app.include_router(catalog.router)
app.include_router(conversations.router)
app.include_router(notifications.router)
app.include_router(communication_profiles.router)
app.include_router(partner_portal.router)
app.include_router(bandwidth_webhooks.router)
app.include_router(plume.router)
app.include_router(inventory.router)
app.include_router(csr.router)
app.include_router(porting.router)
app.include_router(mobile.router)
app.include_router(digicloud.router)
app.include_router(admin.router)
app.include_router(service_fusion_import.router)
app.include_router(platypus_sync.router)
app.include_router(identity.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "version": settings.app_version,
        "authentication": "enabled",
    }
