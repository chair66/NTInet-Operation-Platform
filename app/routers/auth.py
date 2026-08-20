import json
import secrets
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.config import get_settings
from app.database.core import SessionLocal
from app.database.models import User, AuditLog, TrustedDevice
from app.security.passwords import hash_password, verify_password
from app.security.mfa import (
    decrypt_secret, encrypt_secret, generate_recovery_codes, new_totp_secret,
    provisioning_uri, qr_data_uri, sign_trusted_cookie, token_hash,
    trusted_expiration, unsign_trusted_cookie, verify_recovery_code, verify_totp,
)
from app.web import render

router = APIRouter()
settings = get_settings()


def _audit(db, request, action, user=None, detail=""):
    db.add(AuditLog(user_id=getattr(user, "id", None), organization_id=getattr(user, "organization_id", None),
                    action=action, resource_type="user", resource_id=str(getattr(user, "id", "")), detail=detail,
                    ip_address=request.client.host if request.client else ""))


def _mfa_required(user: User) -> bool:
    return user.mfa_required or user.organization.mfa_policy == "required"


def _trusted_device_valid(request: Request, db, user: User) -> bool:
    cookie = request.cookies.get(settings.mfa_trusted_cookie_name)
    if not cookie:
        return False
    payload = unsign_trusted_cookie(cookie, settings.mfa_trusted_days)
    if not payload:
        return False
    device = db.get(TrustedDevice, payload.get("device_id"))
    now = datetime.now(timezone.utc)
    expires_at = device.expires_at if device else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not device or device.user_id != user.id or device.revoked_at or not expires_at or expires_at < now:
        return False
    if device.token_hash != token_hash(payload.get("token", "")):
        return False
    device.last_used_at = now
    _audit(db, request, "auth.mfa_trusted_device", user, f"Trusted device accepted: {device.device_name}")
    db.commit()
    return True


def _complete_login(request: Request, db, user: User, method: str):
    request.session.clear()
    request.session["user_id"] = user.id
    user.last_login_at = datetime.now(timezone.utc)
    _audit(db, request, "auth.login", user, f"Successful login ({method})")
    db.commit()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    if getattr(request.state, "user", None):
        return RedirectResponse("/", status_code=303)
    return render(request, "auth/login.html", next=next, public_page=True)


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/")):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email.strip().lower(), User.active.is_(True), User.deleted_at.is_(None), User.locked_at.is_(None)))
        if not user or not verify_password(password, user.password_hash):
            _audit(db, request, "auth.login_failed", detail=f"Invalid credentials for {email.strip().lower()}")
            db.commit()
            return render(request, "auth/login.html", error_message="Invalid email or password.", email=email, next=next, public_page=True, status_code=401)

        safe_next = next if next.startswith("/") and not next.startswith("//") else "/"
        if user.mfa_enabled:
            if _trusted_device_valid(request, db, user):
                _complete_login(request, db, user, "trusted device")
                return RedirectResponse(safe_next, status_code=303)
            request.session.clear()
            request.session.update({"mfa_pending_user_id": user.id, "mfa_next": safe_next})
            return RedirectResponse("/mfa/challenge", status_code=303)

        if _mfa_required(user):
            request.session.clear()
            request.session.update({"mfa_pending_user_id": user.id, "mfa_next": safe_next, "mfa_enrollment_required": True})
            return RedirectResponse("/mfa/setup", status_code=303)

        _complete_login(request, db, user, "password")
        if user.force_password_change:
            return RedirectResponse("/account/security?notice=Change+your+password+to+continue", status_code=303)
        return RedirectResponse(safe_next, status_code=303)


@router.get("/mfa/setup", response_class=HTMLResponse)
async def mfa_setup(request: Request):
    user_id = request.session.get("mfa_pending_user_id") or request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    with SessionLocal() as db:
        user = db.get(User, int(user_id))
        if not user:
            request.session.clear(); return RedirectResponse("/login", status_code=303)
        secret = request.session.get("mfa_setup_secret") or new_totp_secret()
        request.session["mfa_setup_secret"] = secret
        uri = provisioning_uri(secret, user.email, settings.mfa_issuer)
        return render(request, "auth/mfa_setup.html", enrollment_user=user, qr_code=qr_data_uri(uri), manual_secret=secret,
                      required=bool(request.session.get("mfa_enrollment_required")), public_page=not bool(request.session.get("user_id")))


@router.post("/mfa/setup")
async def mfa_setup_confirm(request: Request, code: str = Form(...)):
    user_id = request.session.get("mfa_pending_user_id") or request.session.get("user_id")
    secret = request.session.get("mfa_setup_secret")
    if not user_id or not secret:
        return RedirectResponse("/login", status_code=303)
    if not verify_totp(secret, code):
        with SessionLocal() as db:
            user = db.get(User, int(user_id)); uri = provisioning_uri(secret, user.email, settings.mfa_issuer)
            return render(request, "auth/mfa_setup.html", enrollment_user=user, qr_code=qr_data_uri(uri), manual_secret=secret,
                          error_message="The verification code was not accepted. Wait for a new code and try again.",
                          required=bool(request.session.get("mfa_enrollment_required")), public_page=not bool(request.session.get("user_id")), status_code=400)
    with SessionLocal() as db:
        user = db.get(User, int(user_id))
        codes, hashes = generate_recovery_codes()
        user.mfa_secret_encrypted = encrypt_secret(secret)
        user.mfa_recovery_hashes = json.dumps(hashes)
        user.mfa_enabled = True
        user.mfa_enrolled_at = datetime.now(timezone.utc)
        _audit(db, request, "auth.mfa_enabled", user, "TOTP MFA enrolled and recovery codes generated")
        db.commit()
        was_pending = bool(request.session.get("mfa_pending_user_id"))
        next_path = request.session.get("mfa_next", "/")
        if was_pending:
            _complete_login(request, db, user, "new MFA enrollment")
        else:
            request.session.pop("mfa_setup_secret", None)
        request.session["mfa_recovery_display"] = codes
        request.session["mfa_recovery_next"] = next_path
    return RedirectResponse("/mfa/recovery-codes", status_code=303)


@router.get("/mfa/challenge", response_class=HTMLResponse)
async def mfa_challenge_page(request: Request):
    if not request.session.get("mfa_pending_user_id"):
        return RedirectResponse("/login", status_code=303)
    return render(request, "auth/mfa_challenge.html", public_page=True)


@router.post("/mfa/challenge")
async def mfa_challenge(request: Request, code: str = Form(...), trust_device: bool = Form(False)):
    user_id = request.session.get("mfa_pending_user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    with SessionLocal() as db:
        user = db.get(User, int(user_id))
        accepted = False
        method = "TOTP"
        if user and user.mfa_secret_encrypted:
            accepted = verify_totp(decrypt_secret(user.mfa_secret_encrypted), code)
        if not accepted and user:
            hashes = json.loads(user.mfa_recovery_hashes or "[]")
            index = verify_recovery_code(code, hashes)
            if index is not None:
                hashes.pop(index); user.mfa_recovery_hashes = json.dumps(hashes)
                accepted = True; method = "recovery code"
                _audit(db, request, "auth.mfa_recovery_used", user, f"Recovery code used; {len(hashes)} remaining")
        if not accepted:
            if user: _audit(db, request, "auth.mfa_failed", user, "Invalid MFA challenge")
            db.commit()
            return render(request, "auth/mfa_challenge.html", error_message="Invalid verification or recovery code.", public_page=True, status_code=401)
        next_path = request.session.get("mfa_next", "/")
        _complete_login(request, db, user, method)
        response = RedirectResponse(next_path, status_code=303)
        if trust_device:
            raw = secrets.token_urlsafe(32)
            ua = request.headers.get("user-agent", "")[:255]
            device = TrustedDevice(user_id=user.id, token_hash=token_hash(raw), device_name=ua[:80] or "Trusted browser",
                                   expires_at=trusted_expiration(settings.mfa_trusted_days),
                                   ip_address=request.client.host if request.client else "", user_agent=ua)
            db.add(device); db.flush(); _audit(db, request, "auth.mfa_device_added", user, device.device_name); db.commit()
            response.set_cookie(settings.mfa_trusted_cookie_name, sign_trusted_cookie(device.id, raw),
                                max_age=settings.mfa_trusted_days * 86400, httponly=True, secure=settings.app_env.lower()=="production", samesite="lax")
        return response


@router.get("/mfa/recovery-codes", response_class=HTMLResponse)
async def recovery_codes(request: Request):
    codes = request.session.pop("mfa_recovery_display", None)
    if not codes:
        return RedirectResponse("/account/security", status_code=303)
    return render(request, "auth/mfa_recovery_codes.html", recovery_codes=codes,
                  next_path=request.session.pop("mfa_recovery_next", "/"))


@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    user = request.state.user
    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        recent_activity = list(
            db.scalars(
                select(AuditLog)
                .where(AuditLog.user_id == user.id)
                .order_by(AuditLog.created_at.desc())
                .limit(10)
            )
        )
        active_devices = list(
            db.scalars(
                select(TrustedDevice).where(
                    TrustedDevice.user_id == user.id,
                    TrustedDevice.revoked_at.is_(None),
                )
            )
        )
        return render(
            request,
            "auth/account.html",
            account_user=fresh,
            recent_activity=recent_activity,
            active_device_count=len(active_devices),
        )


@router.post("/account/profile")
async def update_account_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
):
    user = request.state.user
    normalized_name = " ".join(full_name.strip().split())
    normalized_email = email.strip().lower()

    if len(normalized_name) < 2:
        return RedirectResponse(
            "/account?error=Please+enter+your+full+name", status_code=303
        )
    if "@" not in normalized_email or len(normalized_email) > 255:
        return RedirectResponse(
            "/account?error=Please+enter+a+valid+email+address", status_code=303
        )

    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        existing = db.scalar(
            select(User).where(User.email == normalized_email, User.id != user.id)
        )
        if existing:
            return RedirectResponse(
                "/account?error=That+email+address+is+already+in+use", status_code=303
            )

        changes = []
        if fresh.full_name != normalized_name:
            changes.append("name")
            fresh.full_name = normalized_name
        if fresh.email != normalized_email:
            changes.append("email")
            fresh.email = normalized_email

        if changes:
            _audit(
                db, request, "account.profile_updated", fresh,
                f"Updated {', '.join(changes)}",
            )
            db.commit()

    return RedirectResponse(
        "/account?success=Profile+updated+successfully", status_code=303
    )


@router.post("/account/signature")
async def update_account_signature(
    request: Request,
    email_signature: str = Form(""),
    signature_photo: UploadFile | None = File(None),
    remove_photo: str | None = Form(None),
):
    user = request.state.user
    settings = get_settings()
    signature_text = email_signature.strip()
    if len(signature_text) > 2000:
        return RedirectResponse("/account?error=Email+signature+must+be+2000+characters+or+less", status_code=303)

    allowed_types = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        if not fresh:
            raise HTTPException(status_code=404, detail="User not found")

        old_filename = (fresh.signature_photo_filename or "").strip()
        fresh.email_signature = signature_text
        changed = ["email signature"]

        if remove_photo:
            if old_filename:
                old_path = Path(settings.user_signature_photo_dir) / old_filename
                try:
                    old_path.unlink(missing_ok=True)
                except OSError:
                    pass
            fresh.signature_photo_filename = ""
            fresh.signature_photo_content_type = ""
            changed.append("signature photo removed")

        if signature_photo and signature_photo.filename:
            content_type = (signature_photo.content_type or "").lower()
            if content_type not in allowed_types:
                return RedirectResponse("/account?error=Signature+photo+must+be+JPG,+PNG,+or+WEBP", status_code=303)
            data = await signature_photo.read(settings.user_signature_photo_max_bytes + 1)
            if len(data) > settings.user_signature_photo_max_bytes:
                return RedirectResponse("/account?error=Signature+photo+must+be+2+MB+or+smaller", status_code=303)
            if not data:
                return RedirectResponse("/account?error=The+selected+signature+photo+was+empty", status_code=303)
            directory = Path(settings.user_signature_photo_dir)
            directory.mkdir(parents=True, exist_ok=True)
            filename = f"user-{fresh.id}-{uuid.uuid4().hex}{allowed_types[content_type]}"
            (directory / filename).write_bytes(data)
            if old_filename and old_filename != filename:
                try:
                    (directory / old_filename).unlink(missing_ok=True)
                except OSError:
                    pass
            fresh.signature_photo_filename = filename
            fresh.signature_photo_content_type = content_type
            changed.append("signature photo")

        _audit(db, request, "account.email_signature_updated", fresh, f"Updated {', '.join(changed)}")
        db.commit()

    return RedirectResponse("/account?success=Email+signature+updated", status_code=303)


@router.get("/user-signatures/{user_id}/photo")
async def public_signature_photo(user_id: int):
    settings = get_settings()
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.active or not user.signature_photo_filename:
            raise HTTPException(status_code=404, detail="Signature photo not found")
        path = Path(settings.user_signature_photo_dir) / user.signature_photo_filename
        content_type = user.signature_photo_content_type or "application/octet-stream"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Signature photo not found")
    return FileResponse(path, media_type=content_type, headers={"Cache-Control": "public, max-age=3600"})


@router.post("/account/password")
async def change_account_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    user = request.state.user

    if new_password != confirm_password:
        return RedirectResponse(
            "/account?error=The+new+passwords+do+not+match#password", status_code=303
        )
    if len(new_password) < 12:
        return RedirectResponse(
            "/account?error=The+new+password+must+be+at+least+12+characters#password",
            status_code=303,
        )
    if current_password == new_password:
        return RedirectResponse(
            "/account?error=The+new+password+must+be+different#password", status_code=303
        )

    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        if not verify_password(current_password, fresh.password_hash):
            _audit(db, request, "account.password_change_failed", fresh, "Incorrect current password")
            db.commit()
            return RedirectResponse(
                "/account?error=Your+current+password+was+not+accepted#password",
                status_code=303,
            )

        fresh.password_hash = hash_password(new_password)
        fresh.force_password_change = False
        fresh.password_changed_at = datetime.now(timezone.utc)
        _audit(db, request, "account.password_changed", fresh, "Password changed by user")
        db.commit()

    return RedirectResponse(
        "/account?success=Password+changed+successfully#password", status_code=303
    )


@router.get("/account/security", response_class=HTMLResponse)
async def account_security(request: Request):
    user = request.state.user
    with SessionLocal() as db:
        devices = list(db.scalars(select(TrustedDevice).where(TrustedDevice.user_id == user.id, TrustedDevice.revoked_at.is_(None)).order_by(TrustedDevice.created_at.desc())))
        fresh = db.get(User, user.id)
        recovery_count = len(json.loads(fresh.mfa_recovery_hashes or "[]"))
        return render(request, "auth/security.html", security_user=fresh, trusted_devices=devices, recovery_count=recovery_count)


@router.post("/account/security/recovery-codes")
async def regenerate_recovery_codes(request: Request):
    user = request.state.user
    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        if not fresh.mfa_enabled:
            return RedirectResponse("/account/security?error=MFA+is+not+enabled", status_code=303)
        codes, hashes = generate_recovery_codes(); fresh.mfa_recovery_hashes = json.dumps(hashes)
        _audit(db, request, "auth.mfa_recovery_regenerated", fresh, "Recovery codes regenerated"); db.commit()
    request.session["mfa_recovery_display"] = codes; request.session["mfa_recovery_next"] = "/account/security"
    return RedirectResponse("/mfa/recovery-codes", status_code=303)


@router.post("/account/security/devices/{device_id}/revoke")
async def revoke_device(request: Request, device_id: int):
    with SessionLocal() as db:
        device = db.get(TrustedDevice, device_id)
        if device and device.user_id == request.state.user.id:
            device.revoked_at = datetime.now(timezone.utc); _audit(db, request, "auth.mfa_device_revoked", request.state.user, device.device_name); db.commit()
    return RedirectResponse("/account/security", status_code=303)


@router.post("/account/security/mfa/disable")
async def disable_mfa(request: Request, password: str = Form(...)):
    user = request.state.user
    with SessionLocal() as db:
        fresh = db.get(User, user.id)
        if _mfa_required(fresh):
            return RedirectResponse(
                "/account/security?error=MFA+is+required+by+your+organization",
                status_code=303,
            )
        if not verify_password(password, fresh.password_hash):
            _audit(db, request, "auth.mfa_disable_failed", fresh, "Incorrect password")
            db.commit()
            return RedirectResponse(
                "/account/security?error=Your+password+was+not+accepted", status_code=303
            )

        fresh.mfa_enabled = False
        fresh.mfa_secret_encrypted = None
        fresh.mfa_recovery_hashes = "[]"
        fresh.mfa_enrolled_at = None
        now = datetime.now(timezone.utc)
        devices = list(
            db.scalars(
                select(TrustedDevice).where(
                    TrustedDevice.user_id == fresh.id,
                    TrustedDevice.revoked_at.is_(None),
                )
            )
        )
        for device in devices:
            device.revoked_at = now
        _audit(db, request, "auth.mfa_disabled", fresh, "MFA disabled and trusted devices revoked")
        db.commit()

    response = RedirectResponse(
        "/account/security?success=MFA+disabled", status_code=303
    )
    response.delete_cookie(settings.mfa_trusted_cookie_name)
    return response


@router.post("/logout")
async def logout(request: Request):
    user = getattr(request.state, "user", None)
    if user:
        with SessionLocal() as db:
            _audit(db, request, "auth.logout", user, "User logged out"); db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@router.get("/invitation/{token}", response_class=HTMLResponse)
async def invitation_page(request: Request, token: str):
    from hashlib import sha256
    token_digest = sha256(token.encode()).hexdigest()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.invitation_token_hash == token_digest, User.deleted_at.is_(None)))
        now = datetime.now(timezone.utc)
        expires = user.invitation_expires_at if user else None
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if not user or not expires or expires < now:
            return render(request, "auth/invitation.html", error_message="This invitation is invalid or has expired.", public_page=True, status_code=400)
        return render(request, "auth/invitation.html", invitation_user=user, token=token, public_page=True)


@router.post("/invitation/{token}")
async def accept_invitation(request: Request, token: str, password: str = Form(...), confirm_password: str = Form(...)):
    from hashlib import sha256
    if password != confirm_password:
        return render(request, "auth/invitation.html", token=token, error_message="Passwords do not match.", public_page=True, status_code=400)
    if len(password) < 12:
        return render(request, "auth/invitation.html", token=token, error_message="Password must be at least 12 characters.", public_page=True, status_code=400)
    token_digest = sha256(token.encode()).hexdigest()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.invitation_token_hash == token_digest, User.deleted_at.is_(None)))
        now = datetime.now(timezone.utc)
        expires = user.invitation_expires_at if user else None
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if not user or not expires or expires < now:
            return render(request, "auth/invitation.html", error_message="This invitation is invalid or has expired.", public_page=True, status_code=400)
        user.password_hash = hash_password(password)
        user.password_changed_at = now
        user.force_password_change = False
        user.invitation_token_hash = None
        user.invitation_expires_at = None
        user.active = True
        _audit(db, request, "user.invitation_accepted", user, "Invitation accepted and password set")
        db.commit()
    return RedirectResponse("/login?notice=Account+activated", status_code=303)
