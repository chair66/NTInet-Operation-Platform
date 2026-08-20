import base64
import hashlib
import io
import secrets
from datetime import datetime, timedelta, timezone

import hmac
import struct
import time
from urllib.parse import quote
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import get_settings
from app.security.passwords import hash_password, verify_password

settings = get_settings()


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.app_secret_key.encode()).digest())
    return Fernet(key)


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt MFA secret. Check APP_SECRET_KEY.") from exc


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def provisioning_uri(secret: str, email: str, issuer: str = "DigiCloud") -> str:
    label = quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def _totp_code(secret: str, counter: int) -> str:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def qr_data_uri(uri: str) -> str:
    image = qrcode.make(uri)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    normalized = "".join(ch for ch in code if ch.isdigit())
    if len(normalized) != 6:
        return False
    counter = int(time.time()) // 30
    return any(hmac.compare_digest(normalized, _totp_code(secret, counter + drift)) for drift in (-1, 0, 1))


def generate_recovery_codes(count: int = 10) -> tuple[list[str], list[str]]:
    plain = [f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" for _ in range(count)]
    return plain, [hash_password(code) for code in plain]


def verify_recovery_code(code: str, hashes: list[str]) -> int | None:
    normalized = code.strip().upper()
    for index, value in enumerate(hashes):
        if verify_password(normalized, value):
            return index
    return None


def trusted_cookie_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.app_secret_key, salt="digicloud-trusted-device")


def sign_trusted_cookie(device_id: int, raw_token: str) -> str:
    return trusted_cookie_serializer().dumps({"device_id": device_id, "token": raw_token})


def unsign_trusted_cookie(value: str, max_age_days: int) -> dict | None:
    try:
        return trusted_cookie_serializer().loads(value, max_age=max_age_days * 86400)
    except (BadSignature, SignatureExpired):
        return None


def token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def trusted_expiration(days: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)
