from fastapi import Request, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import User, AuditLog

def current_user_from_request(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.scalar(select(User).where(User.id == int(user_id), User.active.is_(True), User.deleted_at.is_(None), User.locked_at.is_(None)))

def require_permission(request: Request, permission: str) -> User:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not user.can(permission):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    return user

def write_audit(db: Session, request: Request, action: str, resource_type: str = "", resource_id: str = "", detail: str = "") -> None:
    user = getattr(request.state, "user", None)
    db.add(AuditLog(user_id=getattr(user, "id", None), organization_id=getattr(user, "organization_id", None), action=action,
                    resource_type=resource_type, resource_id=str(resource_id or ""), detail=detail,
                    ip_address=request.client.host if request.client else ""))
    db.commit()
