from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from string import Template
from typing import Iterable

from app.config import get_settings

logger = logging.getLogger("digicloud.notifications")


EMAIL_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "email_templates"


def render_email_template(template_name: str, **context: object) -> str:
    """Render an email template from app/email_templates."""
    template_path = EMAIL_TEMPLATE_DIR / template_name
    if not template_path.is_file():
        raise FileNotFoundError(f"Email template not found: {template_path}")
    template = Template(template_path.read_text(encoding="utf-8"))
    values = {key: "" if value is None else str(value) for key, value in context.items()}
    return template.substitute(values)


@dataclass(slots=True)
class EmailResult:
    ok: bool
    message: str
    recipients: list[str]


def _clean_recipients(recipients: Iterable[str]) -> list[str]:
    return sorted({str(value).strip() for value in recipients if str(value or "").strip()})


def _connect_smtp():
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not configured.")
    if not settings.smtp_from:
        raise RuntimeError("SMTP_FROM is not configured.")

    context = ssl.create_default_context()
    if settings.smtp_use_ssl:
        server = smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
            context=context,
        )
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()

    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
    return server


def test_smtp_connection() -> EmailResult:
    """Verify connection, TLS and authentication without sending a message."""
    try:
        with _connect_smtp() as server:
            server.noop()
        return EmailResult(True, "SMTP connection and authentication succeeded.", [])
    except Exception as exc:
        logger.exception("SMTP diagnostic failed")
        return EmailResult(False, str(exc), [])


def send_email(subject: str, body: str, recipients: Iterable[str]) -> EmailResult:
    settings = get_settings()
    cleaned = _clean_recipients(recipients)
    if not cleaned:
        return EmailResult(False, "No recipient email address was provided.", [])

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(cleaned)
    if "<html" in body.lower() or "<!doctype html" in body.lower():
        plain_body = re.sub(r"<[^>]+>", " ", body)
        plain_body = re.sub(r"[ \t]+", " ", plain_body)
        plain_body = re.sub(r"\n\s*\n+", "\n\n", plain_body).strip()
        message.set_content(plain_body)
        message.add_alternative(body, subtype="html")
    else:
        message.set_content(body)

    try:
        with _connect_smtp() as server:
            server.send_message(message)
        return EmailResult(True, "Email sent successfully.", cleaned)
    except Exception as exc:
        logger.exception("Unable to send notification email")
        return EmailResult(False, str(exc), cleaned)


def send_test_email(recipients: Iterable[str], *, app_version: str) -> EmailResult:
    settings = get_settings()
    sent_at = datetime.now().astimezone().strftime("%B %d, %Y at %I:%M %p %Z")
    sent_at = sent_at.replace(" 0", " ")
    body = render_email_template(
        "test_email.txt",
        environment=settings.app_env,
        app_version=app_version,
        sent_at=sent_at,
    )
    return send_email(
        "NTInet Operations Platform - Test Notification",
        body,
        recipients,
    )


def send_port_email(subject: str, body: str, recipients: Iterable[str]) -> bool:
    """Backward-compatible notification function used by the port workflow."""
    result = send_email(subject, body, recipients)
    if not result.ok:
        logger.info("Port email was not sent: %s", result.message)
    return result.ok
