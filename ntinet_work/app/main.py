from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request
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
from app.routers import admin, auth, csr, dashboard, identity, inventory, mobile, porting


configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_builtin_modules()
    register_builtin_providers()
    init_database()
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

PUBLIC_PATHS = {
    "/login",
    "/health",
    "/mfa/setup",
    "/mfa/challenge",
    "/mfa/recovery-codes",
}

MODULE_PATHS = (
    ("/admin", "administration"),
    ("/identity", "administration"),
    ("/available-numbers", "lnp-management"),
    ("/sites", "lnp-management"),
    ("/ports", "lnp-management"),
    ("/csrs", "lnp-management"),
    ("/mobile", "nti-mobile"),
)


def module_for_path(path: str) -> str | None:
    if path == "/":
        return "dashboard"

    for prefix, module_slug in MODULE_PATHS:
        if path.startswith(prefix):
            return module_slug

    return None


def permission_for_path(path: str, method: str) -> str | None:
    is_get = method.upper() == "GET"

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
            return JSONResponse(
                {
                    "detail": (
                        "Your organization does not have access to this module."
                    )
                },
                status_code=403,
            )

        permission = permission_for_path(path, request.method)

        if permission and not request.state.user.can(permission):
            return JSONResponse(
                {
                    "detail": (
                        "You do not have permission to access this resource."
                    )
                },
                status_code=403,
            )

    if (
        not request.state.user
        and path not in PUBLIC_PATHS
        and not path.startswith("/static/")
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
app.include_router(inventory.router)
app.include_router(csr.router)
app.include_router(porting.router)
app.include_router(mobile.router)
app.include_router(admin.router)
app.include_router(identity.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "version": settings.app_version,
        "authentication": "enabled",
    }
