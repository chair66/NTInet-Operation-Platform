from app.security.passwords import hash_password, verify_password
from app.security.auth import (
    current_user_from_request,
    require_permission,
    write_audit,
)

from app.security.context import SecurityContext
from app.security.dependencies import (
    get_authenticated_user,
    get_security_context,
    require_active_organization,
    require_active_user,
    require_all_permissions,
    require_any_permission,
    require_module,
    require_organization_type,
    require_permission as require_route_permission,
    require_reseller,
    require_staff,
)

__all__ = [
    # Existing security functions
    "hash_password",
    "verify_password",
    "current_user_from_request",
    "require_permission",
    "write_audit",

    # PLAT-002A security framework
    "SecurityContext",
    "get_authenticated_user",
    "get_security_context",
    "require_active_organization",
    "require_active_user",
    "require_all_permissions",
    "require_any_permission",
    "require_module",
    "require_organization_type",
    "require_route_permission",
    "require_reseller",
    "require_staff",
]

from app.security.scopes import (
    allowed_bandwidth_site_ids,
    context_from_request,
    filter_bandwidth_records,
    require_bandwidth_site,
    require_platform_staff,
    require_same_organization,
    scope_audit_logs,
    scope_roles,
    scope_users,
    validate_role_assignment,
    visible_bandwidth_sites,
)

__all__ += [
    "allowed_bandwidth_site_ids", "context_from_request", "filter_bandwidth_records",
    "require_bandwidth_site", "require_platform_staff", "require_same_organization",
    "scope_audit_logs", "scope_roles", "scope_users", "validate_role_assignment",
    "visible_bandwidth_sites",
]
