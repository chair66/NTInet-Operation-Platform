from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from math import ceil
import secrets
from fastapi import HTTPException, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session
from app.database.models import Organization, Role, TrustedDevice, User
from app.security.context import SecurityContext
from app.security.passwords import hash_password
from app.services.audit_service import AuditService
from app.services.role_service import RoleService
from app.services.notification_service import NotificationService

@dataclass(slots=True)
class UserPage:
    items:list[User]; page:int; per_page:int; total:int
    @property
    def pages(self): return max(1,ceil(self.total/self.per_page))
    @property
    def first_item(self): return 0 if self.total==0 else ((self.page-1)*self.per_page)+1
    @property
    def last_item(self): return min(self.page*self.per_page,self.total)

@dataclass(slots=True)
class UserService:
    db:Session; context:SecurityContext; request:Request|None=None
    @property
    def audit(self): return AuditService(self.db,self.request,self.context)
    def _scope(self, stmt, include_deleted=False):
        if not (self.context.is_staff and self.context.is_superuser): stmt=stmt.where(User.organization_id==self.context.organization_id)
        if not include_deleted: stmt=stmt.where(User.deleted_at.is_(None))
        return stmt
    def list_users_page(self,query='',account_status='all',mfa_status='all',organization_id=None,role_id=None,sort='name',direction='asc',page=1,per_page=25):
        page=max(1,int(page)); per_page=max(10,min(int(per_page),100)); st=self._scope(select(User))
        q=' '.join(query.strip().split())
        if q:
            term=f'%{q.lower()}%'; st=st.join(User.organization).outerjoin(User.roles).where(or_(func.lower(User.full_name).like(term),func.lower(User.email).like(term),func.lower(Organization.name).like(term),func.lower(Role.name).like(term)))
        if account_status=='active': st=st.where(User.active.is_(True))
        elif account_status=='disabled': st=st.where(User.active.is_(False))
        elif account_status=='deleted': st=self._scope(select(User),True).where(User.deleted_at.is_not(None))
        elif account_status=='locked': st=st.where(User.locked_at.is_not(None))
        if mfa_status=='enabled': st=st.where(User.mfa_enabled.is_(True))
        elif mfa_status=='required': st=st.where(User.mfa_enabled.is_(False),User.mfa_required.is_(True))
        elif mfa_status=='not_enabled': st=st.where(User.mfa_enabled.is_(False))
        if organization_id is not None:
            if not (self.context.is_staff and self.context.is_superuser) and int(organization_id)!=self.context.organization_id: raise HTTPException(403,'Organization is outside your scope')
            st=st.where(User.organization_id==int(organization_id))
        if role_id is not None: st=st.join(User.roles).where(Role.id==int(role_id))
        st=st.distinct(); total=int(self.db.scalar(select(func.count()).select_from(st.order_by(None).subquery())) or 0); pages=max(1,ceil(total/per_page)); page=min(page,pages)
        cols={'name':User.full_name,'email':User.email,'organization':Organization.name,'status':User.active,'last_login':User.last_login_at,'created':User.created_at}; col=cols.get(sort,User.full_name)
        if sort=='organization' and not q: st=st.join(User.organization)
        st=st.order_by(col.desc() if direction=='desc' else col.asc(),User.id.asc()).offset((page-1)*per_page).limit(per_page)
        return UserPage(list(self.db.scalars(st).unique()),page,per_page,total)
    def get_user(self,user_id,include_deleted=False):
        u=self.db.scalar(self._scope(select(User).where(User.id==int(user_id)),include_deleted));
        if not u: raise HTTPException(404,'User not found')
        return u
    def visible_organizations(self):
        return list(self.db.scalars(select(Organization).order_by(Organization.name))) if self.context.is_staff and self.context.is_superuser else [self.context.organization]
    def create_user(self,full_name,email,password,organization_id,role_ids=None):
        oid=int(organization_id) if self.context.is_staff and self.context.is_superuser else self.context.organization_id
        name=self._name(full_name); mail=self._email(email); self._password(password); self._email_free(mail)
        roles=RoleService(self.db,self.context).resolve_assignable(role_ids or [],oid); u=User(full_name=name,email=mail,password_hash=hash_password(password),organization_id=oid,active=True,force_password_change=True,password_changed_at=datetime.now(timezone.utc)); u.roles=roles; self.db.add(u); self.db.flush(); self.audit.record('user.create','user',u.id,f'Created {u.email}',module='identity',event_data={'email':u.email,'role_ids':[r.id for r in roles]}); NotificationService(self.db,self.context).publish('user.created',subject=f'User created: {u.full_name}',payload={'user_id':u.id,'email':u.email},recipient_user_id=u.id,organization_id=u.organization_id); return u
    def update_user(self,user_id,full_name,email,organization_id,role_ids,active,mfa_required):
        u=self.get_user(user_id); oid=int(organization_id) if self.context.is_staff and self.context.is_superuser else self.context.organization_id
        if u.is_superuser and not self.context.is_superuser: raise HTTPException(403,'Only a superuser can edit a superuser')
        u.full_name=self._name(full_name); u.email=self._email(email); self._email_free(u.email,u.id); u.organization_id=oid; u.active=bool(active); u.mfa_required=bool(mfa_required); u.roles=RoleService(self.db,self.context).resolve_assignable(role_ids,oid); self.audit.record('user.update','user',u.id,f'Updated {u.email}'); return u
    def set_active(self,user_id,active):
        u=self.get_user(user_id)
        if u.id==self.context.user_id: raise HTTPException(400,'You cannot disable your own account')
        u.active=bool(active); self.audit.record('user.status','user',u.id,f'Active={u.active}'); return u
    def toggle_active(self,user_id): u=self.get_user(user_id); return self.set_active(u.id,not u.active)
    def reset_password(self,user_id,password,force_change=True):
        self._password(password); u=self.get_user(user_id); u.password_hash=hash_password(password); u.force_password_change=bool(force_change); u.password_changed_at=datetime.now(timezone.utc); u.locked_at=None; self.revoke_devices(u.id); self.audit.record('user.password_reset','user',u.id,f'Force change={u.force_password_change}'); return u
    def unlock(self,user_id):
        u=self.get_user(user_id); u.locked_at=None; self.audit.record('user.unlock','user',u.id,'Account unlocked'); return u
    def soft_delete(self,user_id):
        u=self.get_user(user_id)
        if u.id==self.context.user_id: raise HTTPException(400,'You cannot delete your own account')
        u.deleted_at=datetime.now(timezone.utc); u.deleted_by_user_id=self.context.user_id; u.active=False; self.revoke_devices(u.id); self.audit.record('user.delete','user',u.id,'Soft deleted'); return u
    def restore(self,user_id):
        u=self.get_user(user_id,True); u.deleted_at=None; u.deleted_by_user_id=None; u.active=True; self.audit.record('user.restore','user',u.id,'Restored'); return u
    def create_invitation(self,user_id,hours=48):
        u=self.get_user(user_id); raw=secrets.token_urlsafe(32); u.invitation_token_hash=sha256(raw.encode()).hexdigest(); u.invitation_expires_at=datetime.now(timezone.utc)+timedelta(hours=hours); u.force_password_change=True; self.audit.record('user.invitation','user',u.id,f'Invitation generated; expires in {hours} hours'); return raw
    def reset_mfa(self,user_id):
        u=self.get_user(user_id); u.mfa_enabled=False; u.mfa_secret_encrypted=None; u.mfa_recovery_hashes='[]'; u.mfa_enrolled_at=None; self.revoke_devices(u.id); self.audit.record('user.mfa_reset','user',u.id,'MFA reset'); return u
    def toggle_mfa_required(self,user_id): u=self.get_user(user_id); u.mfa_required=not u.mfa_required; self.audit.record('user.mfa_required','user',u.id,f'MFA required={u.mfa_required}'); return u
    def revoke_devices(self,user_id): self.db.execute(update(TrustedDevice).where(TrustedDevice.user_id==user_id,TrustedDevice.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    def bulk_action(self, user_ids, action, role_id=None):
        ids = sorted({int(v) for v in user_ids})
        if not ids:
            raise HTTPException(400, 'Select at least one user')
        users = [self.get_user(user_id, include_deleted=True) for user_id in ids]
        if any(user.id == self.context.user_id for user in users) and action in {'disable','delete'}:
            raise HTTPException(400, 'You cannot disable or delete your own account')
        changed = 0
        for user in users:
            if action == 'enable':
                if user.deleted_at is None: user.active = True; changed += 1
            elif action == 'disable':
                if user.deleted_at is None: user.active = False; changed += 1
            elif action == 'force_password_change':
                user.force_password_change = True; changed += 1
            elif action == 'assign_role':
                if role_id is None: raise HTTPException(400, 'Choose a role')
                role = RoleService(self.db,self.context).resolve_assignable([role_id], user.organization_id)[0]
                if role not in user.roles: user.roles.append(role); changed += 1
            elif action == 'remove_role':
                if role_id is None: raise HTTPException(400, 'Choose a role')
                before = len(user.roles); user.roles = [r for r in user.roles if r.id != int(role_id)]; changed += int(len(user.roles) != before)
            elif action == 'delete':
                if user.deleted_at is None:
                    user.deleted_at=datetime.now(timezone.utc); user.deleted_by_user_id=self.context.user_id; user.active=False; self.revoke_devices(user.id); changed += 1
            elif action == 'restore':
                if user.deleted_at is not None: user.deleted_at=None; user.deleted_by_user_id=None; user.active=True; changed += 1
            else:
                raise HTTPException(400, 'Unsupported bulk action')
        self.audit.record('user.bulk_action','user',','.join(str(v) for v in ids),f'{action}: {changed} changed',module='identity',event_data={'action':action,'user_ids':ids,'role_id':role_id,'changed':changed})
        NotificationService(self.db,self.context).publish('user.bulk_action',subject=f'Bulk user action: {action}',payload={'user_ids':ids,'changed':changed,'role_id':role_id})
        return changed

    def export_rows(self, **filters):
        page = self.list_users_page(page=1, per_page=100, **filters)
        rows = list(page.items)
        current_page = 2
        while len(rows) < page.total and current_page <= 100:
            rows.extend(self.list_users_page(page=current_page, per_page=100, **filters).items)
            current_page += 1
        return rows

    def _email_free(self,email,exclude=None):
        st=select(User.id).where(func.lower(User.email)==email)
        if exclude: st=st.where(User.id!=exclude)
        if self.db.scalar(st) is not None: raise HTTPException(409,'Email already exists')
    @staticmethod
    def _name(v):
        v=' '.join(v.strip().split())
        if not 2<=len(v)<=120: raise HTTPException(400,'Full name must be between 2 and 120 characters')
        return v
    @staticmethod
    def _email(v):
        v=v.strip().lower()
        if len(v)>255 or '@' not in v or v.startswith('@') or v.endswith('@'): raise HTTPException(400,'Enter a valid email address')
        return v
    @staticmethod
    def _password(v):
        if len(v)<12: raise HTTPException(400,'Password must be at least 12 characters')
