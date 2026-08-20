from typing import Any
from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.config import get_settings

settings = get_settings()
templates = Jinja2Templates(directory="app/templates")

def render(request: Request, template: str, status_code: int = 200, **context: Any):
    user = getattr(request.state, "user", None)
    account_id = settings.bandwidth_account_id
    if user and user.organization and user.organization.bandwidth_account_id:
        account_id = user.organization.bandwidth_account_id
    base = {
        "request": request,
        "app_name": settings.app_name,
        "account_id": account_id,
        "active_path": request.url.path,
        "current_user": user,
        "can": (lambda permission: bool(user and user.can(permission))),
    }
    base.update(context)
    return templates.TemplateResponse(template, base, status_code=status_code)
