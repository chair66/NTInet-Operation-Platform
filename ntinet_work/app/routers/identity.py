import csv
from datetime import datetime, time, timezone
from io import StringIO
import re
from urllib.parse import quote_plus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select

from app.database.core import SessionLocal
from app.database.models import Organization
from app.security import context_from_request, require_permission, require_platform_staff
from app.services import AuditService, OrganizationService, RoleService, UserService
from app.web import render

router = APIRouter(prefix="/admin", tags=["identity"])


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _parse_site_ids(value: str) -> list[int]:
    result = []
    for item in re.split(r"[\s,]+", value.strip()):
        if not item:
            continue
        if not item.isdigit():
            raise ValueError(f"Invalid Bandwidth site ID: {item}")
        result.append(int(item))
    return sorted(set(result))


def _redirect_error(path: str, exc: HTTPException) -> RedirectResponse:
    return RedirectResponse(f"{path}?error={quote_plus(str(exc.detail))}", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def users(
    request: Request,
    q: str = "",
    status_filter: str = "all",
    mfa: str = "all",
    organization_id: int | None = None,
    role_id: int | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        user_service = UserService(db, context, request)
        role_service = RoleService(db, context)
        user_page = user_service.list_users_page(
            query=q,
            account_status=status_filter,
            mfa_status=mfa,
            organization_id=organization_id,
            role_id=role_id,
            sort=sort,
            direction=direction,
            page=page,
            per_page=per_page,
        )
        filters = {
            "q": q, "status_filter": status_filter, "mfa": mfa,
            "organization_id": organization_id, "role_id": role_id,
            "sort": sort, "direction": direction, "per_page": user_page.per_page,
        }
        return render(
            request,
            "admin/users.html",
            users=user_page.items,
            user_page=user_page,
            filters=filters,
            organizations=user_service.visible_organizations(),
            roles=role_service.list_visible(),
        )


@router.post("/users")
async def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    organization_id: int = Form(...),
    role_ids: list[int] = Form(default=[]),
):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).create_user(
                full_name=full_name,
                email=email,
                password=password,
                organization_id=organization_id,
                role_ids=role_ids,
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/users", exc)
    return RedirectResponse("/admin/users?notice=User+created", status_code=303)


@router.post("/users/{user_id}/toggle")
async def toggle_user(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).toggle_active(user_id)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/users", exc)
    return RedirectResponse("/admin/users", status_code=303)


@router.get("/organizations", response_class=HTMLResponse)
async def organizations(
    request: Request,
    q: str = "",
    status_filter: str = "all",
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        service = OrganizationService(db, context, request)
        organization_page = service.list_page(query=q, status_filter=status_filter, sort=sort, direction=direction, page=page, per_page=per_page)
        return render(
            request,
            "admin/organizations.html",
            organization_page=organization_page,
            organizations=organization_page.items,
            counts=service.dashboard_counts(),
            filters={"q": q, "status_filter": status_filter, "sort": sort, "direction": direction, "per_page": organization_page.per_page},
        )


@router.post("/organizations")
async def create_organization(
    request: Request,
    name: str = Form(...),
    display_name: str = Form(""),
    organization_type: str = Form("reseller"),
    status: str = Form("active"),
    notes: str = Form(""),
):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            organization = OrganizationService(db, context, request).create(name=name, display_name=display_name, organization_type=organization_type, status=status, notes=notes)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/organizations", exc)
    return RedirectResponse(f"/admin/organizations/{organization.id}?notice=Organization+created", status_code=303)


@router.get("/organizations/{organization_id}", response_class=HTMLResponse)
async def organization_detail(request: Request, organization_id: int):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        service = OrganizationService(db, context, request)
        organization = service.get(organization_id)
        return render(
            request,
            "admin/organization_detail.html",
            managed_organization=organization,
            summary=service.summary(organization),
            audit_logs=service.audit_logs(organization.id),
            available_modules=service.available_modules(organization),
            module_assignments=service.module_assignments(organization),
            default_roles=service.available_default_roles(organization),
        )


@router.post("/organizations/{organization_id}/edit")
async def update_organization(
    request: Request,
    organization_id: int,
    name: str = Form(...),
    display_name: str = Form(""),
    organization_type: str = Form("reseller"),
    status: str = Form("active"),
    notes: str = Form(""),
):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).update(organization_id, name=name, display_name=display_name, organization_type=organization_type, status=status, notes=notes)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error(f"/admin/organizations/{organization_id}", exc)
    return RedirectResponse(f"/admin/organizations/{organization_id}?notice=Organization+updated", status_code=303)


@router.post("/organizations/{organization_id}/status")
async def update_organization_status(request: Request, organization_id: int, status: str = Form(...)):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).set_status(organization_id, status)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error(f"/admin/organizations/{organization_id}", exc)
    return RedirectResponse(f"/admin/organizations/{organization_id}?notice=Organization+status+updated", status_code=303)


@router.post("/organizations/{organization_id}/modules")
async def update_organization_modules(
    request: Request,
    organization_id: int,
    module_slugs: list[str] = Form(default=[]),
):
    require_permission(request, "admin.modules")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).update_modules(organization_id, module_slugs)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error(f"/admin/organizations/{organization_id}#modules", exc)
    return RedirectResponse(f"/admin/organizations/{organization_id}?notice=Modules+updated#modules", status_code=303)


@router.post("/organizations/{organization_id}/settings")
async def update_organization_settings(
    request: Request,
    organization_id: int,
    mfa_policy: str = Form("optional"),
    password_expiration_days: int = Form(0),
    session_timeout_minutes: int = Form(480),
    allow_api_access: bool = Form(False),
    timezone_name: str = Form("America/New_York"),
    date_format: str = Form("MM/DD/YYYY"),
    default_role_id: int | None = Form(None),
):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).update_settings(
                organization_id,
                mfa_policy=mfa_policy,
                password_expiration_days=password_expiration_days,
                session_timeout_minutes=session_timeout_minutes,
                allow_api_access=allow_api_access,
                timezone_name=timezone_name,
                date_format=date_format,
                default_role_id=default_role_id,
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error(f"/admin/organizations/{organization_id}#settings", exc)
    return RedirectResponse(f"/admin/organizations/{organization_id}?notice=Settings+updated#settings", status_code=303)


@router.post("/organizations/{organization_id}/delete")
async def delete_organization(
    request: Request,
    organization_id: int,
    delete_confirmation: str = Form(""),
):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    if delete_confirmation.strip() != "delete":
        return _redirect_error(
            f"/admin/organizations/{organization_id}",
            HTTPException(400, "Type delete exactly to confirm organization deletion"),
        )
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).soft_delete(organization_id)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error(f"/admin/organizations/{organization_id}", exc)
    return RedirectResponse("/admin/organizations?notice=Organization+deleted", status_code=303)


@router.post("/organizations/{organization_id}/restore")
async def restore_organization(request: Request, organization_id: int):
    require_permission(request, "admin.organizations")
    context = require_platform_staff(request)
    with SessionLocal() as db:
        try:
            OrganizationService(db, context, request).restore(organization_id)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/organizations", exc)
    return RedirectResponse(f"/admin/organizations/{organization_id}?notice=Organization+restored", status_code=303)


@router.post("/users/{user_id}/mfa-reset")
async def reset_user_mfa(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).reset_mfa(user_id)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/users", exc)
    return RedirectResponse("/admin/users?notice=MFA+enrollment+reset", status_code=303)


@router.post("/users/{user_id}/mfa-required")
async def toggle_user_mfa_required(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).toggle_mfa_required(user_id)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return _redirect_error("/admin/users", exc)
    return RedirectResponse("/admin/users", status_code=303)



@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = UserService(db, context, request)
        user = service.get_user(user_id, include_deleted=True)
        roles = RoleService(db, context).list_visible()
        audit_logs = AuditService(db).list_recent(context, 250)
        user_audit = [log for log in audit_logs if log.resource_type == "user" and log.resource_id == str(user.id)][:20]
        effective_permissions = RoleService.permissions_by_module(user)
        return render(request, "admin/user_edit.html", managed_user=user, organizations=service.visible_organizations(), roles=roles, user_audit=user_audit, effective_permissions=effective_permissions)


@router.post("/users/{user_id}/edit")
async def update_user_admin(request: Request, user_id: int, full_name: str = Form(...), email: str = Form(...), organization_id: int = Form(...), role_ids: list[int] = Form(default=[]), active: bool = Form(False), mfa_required: bool = Form(False)):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).update_user(user_id, full_name, email, organization_id, role_ids, active, mfa_required)
            db.commit()
        except HTTPException as exc:
            db.rollback(); return _redirect_error(f"/admin/users/{user_id}/edit", exc)
    return RedirectResponse(f"/admin/users/{user_id}/edit?notice=User+updated", status_code=303)


@router.post("/users/{user_id}/password-reset")
async def admin_password_reset(request: Request, user_id: int, temporary_password: str = Form(...), force_change: bool = Form(False)):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            UserService(db, context, request).reset_password(user_id, temporary_password, force_change)
            db.commit()
        except HTTPException as exc:
            db.rollback(); return _redirect_error(f"/admin/users/{user_id}/edit", exc)
    return RedirectResponse(f"/admin/users/{user_id}/edit?notice=Password+reset", status_code=303)


@router.post("/users/{user_id}/unlock")
async def unlock_user(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try: UserService(db, context, request).unlock(user_id); db.commit()
        except HTTPException as exc: db.rollback(); return _redirect_error(f"/admin/users/{user_id}/edit", exc)
    return RedirectResponse(f"/admin/users/{user_id}/edit?notice=Account+unlocked", status_code=303)


@router.post("/users/{user_id}/delete")
async def soft_delete_user(
    request: Request,
    user_id: int,
    delete_confirmation: str = Form(""),
):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    if delete_confirmation.strip() != "delete":
        return _redirect_error(
            f"/admin/users/{user_id}/edit",
            HTTPException(400, "Type delete exactly to confirm user deletion"),
        )
    with SessionLocal() as db:
        try: UserService(db, context, request).soft_delete(user_id); db.commit()
        except HTTPException as exc: db.rollback(); return _redirect_error(f"/admin/users/{user_id}/edit", exc)
    return RedirectResponse("/admin/users?notice=User+deleted", status_code=303)


@router.post("/users/{user_id}/restore")
async def restore_user(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try: UserService(db, context, request).restore(user_id); db.commit()
        except HTTPException as exc: db.rollback(); return _redirect_error("/admin/users", exc)
    return RedirectResponse(f"/admin/users/{user_id}/edit?notice=User+restored", status_code=303)


@router.post("/users/{user_id}/invitation", response_class=HTMLResponse)
async def generate_user_invitation(request: Request, user_id: int):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            service = UserService(db, context, request); user = service.get_user(user_id); token = service.create_invitation(user_id); db.commit()
        except HTTPException as exc:
            db.rollback(); return _redirect_error(f"/admin/users/{user_id}/edit", exc)
        invitation_url = str(request.base_url).rstrip("/") + f"/invitation/{token}"
        return render(request, "admin/invitation_created.html", managed_user=user, invitation_url=invitation_url)


@router.post("/users/bulk")
async def bulk_users(
    request: Request,
    user_ids: list[int] = Form(default=[]),
    action: str = Form(...),
    role_id: int | None = Form(None),
    delete_confirmation: str = Form(""),
):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    if action == "delete" and delete_confirmation.strip() != "delete":
        return _redirect_error(
            "/admin/users",
            HTTPException(400, "Type delete exactly to confirm bulk user deletion"),
        )
    with SessionLocal() as db:
        try:
            changed = UserService(db, context, request).bulk_action(user_ids, action, role_id)
            db.commit()
        except HTTPException as exc:
            db.rollback(); return _redirect_error("/admin/users", exc)
    return RedirectResponse(f"/admin/users?notice={quote_plus(str(changed) + ' user records updated')}", status_code=303)


@router.get("/users/export.csv")
async def export_users(request: Request, q: str = "", status_filter: str = "all", mfa: str = "all", organization_id: int | None = None, role_id: int | None = None, sort: str = "name", direction: str = "asc"):
    require_permission(request, "admin.users")
    context = context_from_request(request)
    with SessionLocal() as db:
        rows = UserService(db, context, request).export_rows(query=q, account_status=status_filter, mfa_status=mfa, organization_id=organization_id, role_id=role_id, sort=sort, direction=direction)
        output = StringIO(); writer = csv.writer(output)
        writer.writerow(["Name","Email","Organization","Roles","Active","Deleted","Locked","MFA Enabled","MFA Required","Last Login","Created"] )
        for user in rows:
            writer.writerow([user.full_name,user.email,user.organization.name,"; ".join(r.name for r in user.roles),user.active,bool(user.deleted_at),bool(user.locked_at),user.mfa_enabled,user.mfa_required,user.last_login_at.isoformat() if user.last_login_at else "",user.created_at.isoformat()])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=users.csv"})


@router.get("/roles", response_class=HTMLResponse)
async def roles(request: Request):
    require_permission(request, "admin.roles")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = RoleService(db, context)
        roles = service.list_visible()
        grouped = {role.id: service.role_permissions_by_module(role) for role in roles}
        return render(request, "admin/roles.html", roles=roles, grouped_permissions=grouped)


@router.get("/roles/{role_id}", response_class=HTMLResponse)
async def role_detail(request: Request, role_id: int):
    require_permission(request, "admin.roles")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = RoleService(db, context); role = service.get_visible(role_id)
        return render(request, "admin/role_detail.html", role=role, permissions_by_module=service.role_permissions_by_module(role), role_users=role.users)


@router.get("/audit", response_class=HTMLResponse)
async def audit(request: Request, q: str = "", action: str = "", module: str = "", organization_id: int | None = None, date_from: str = "", date_to: str = "", limit: int = 250):
    require_permission(request, "admin.audit")
    context = context_from_request(request)
    def parse_start(value):
        return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=timezone.utc) if value else None
    def parse_end(value):
        return datetime.combine(datetime.fromisoformat(value).date(), time.max, tzinfo=timezone.utc) if value else None
    with SessionLocal() as db:
        service = AuditService(db); logs = service.search(context, query=q, action=action, module=module, organization_id=organization_id, date_from=parse_start(date_from), date_to=parse_end(date_to), limit=limit)
        actions, modules, organizations = service.filter_options(context)
        return render(request, "admin/audit.html", audit_logs=logs, actions=actions, modules=modules, organizations=organizations, filters={"q":q,"action":action,"module":module,"organization_id":organization_id,"date_from":date_from,"date_to":date_to,"limit":limit})


@router.get("/audit/export.csv")
async def audit_export(request: Request, q: str = "", action: str = "", module: str = "", organization_id: int | None = None):
    require_permission(request, "admin.audit")
    context = context_from_request(request)
    with SessionLocal() as db:
        logs = AuditService(db).search(context, query=q, action=action, module=module, organization_id=organization_id, limit=2000)
        output=StringIO(); writer=csv.writer(output); writer.writerow(["Time","Actor","Email","Organization ID","Module","Action","Resource Type","Resource ID","Detail","IP"] )
        for log in logs: writer.writerow([log.created_at.isoformat(),log.user.full_name if log.user else "System",log.user.email if log.user else "",log.organization_id or "",log.module,log.action,log.resource_type,log.resource_id,log.detail,log.ip_address])
    return Response(output.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=audit-log.csv"})
