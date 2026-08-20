from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, lazyload, selectinload

from app.config import get_settings
from app.database.catalog_models import Estimate, EstimateDelivery, EstimateOption
from app.database.customer_communication_models import CustomerCommunication
from app.services.customer_communication_service import CustomerCommunicationService
from app.web import templates


FIRST_REMINDER_PREFIX = "Estimate Reminder:"
FINAL_REMINDER_PREFIX = "Final Estimate Reminder:"
SUCCESS_STATUSES = {"sent", "delivered"}


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _option_ids(delivery: EstimateDelivery, estimate: Estimate) -> list[int]:
    try:
        values = json.loads(delivery.option_ids_json or "[]")
    except (TypeError, ValueError):
        values = []
    selected = {int(value) for value in values if str(value).isdigit()}
    available = {option.id for option in estimate.options}
    return sorted(selected & available) or sorted(available)


@dataclass(slots=True)
class EstimateReminderService:
    db: Session

    def _latest_stage(
        self, deliveries: list[EstimateDelivery], prefix: str, after: datetime,
        contact_id: int | None,
    ) -> EstimateDelivery | None:
        matches = [
            item for item in deliveries
            if item.contact_id == contact_id
            and item.subject.startswith(prefix)
            and _aware(item.created_at) >= after
        ]
        return max(matches, key=lambda item: _aware(item.created_at), default=None)

    def _channel(self, delivery: EstimateDelivery) -> str:
        contact = delivery.contact
        if (
            contact
            and contact.preferred_channel == "sms"
            and contact.mobile_phone
            and contact.sms_consent_status == "consented"
        ):
            return "sms"
        return "email"

    def _send(
        self,
        estimate: Estimate,
        initial: EstimateDelivery,
        *,
        final: bool,
        now: datetime,
    ) -> EstimateDelivery | None:
        contact = initial.contact
        actor_user_id = initial.sent_by_user_id or estimate.created_by_user_id
        if not contact or not contact.active or not actor_user_id:
            return None
        option_ids = _option_ids(initial, estimate)
        token = initial.acceptance_token
        if not token or not option_ids:
            return None
        settings = get_settings()
        acceptance_url = f"{settings.ticket_public_base_url.rstrip('/')}/estimate/accept/{token}"
        prefix = FINAL_REMINDER_PREFIX if final else FIRST_REMINDER_PREFIX
        subject = f"{prefix} {estimate.estimate_number} · {estimate.title}"
        greeting = f"Hello {contact.first_name or contact.full_name},"
        reminder_text = (
            f"This is a final reminder that estimate {estimate.estimate_number} is awaiting your review and signature."
            if final
            else f"This is a friendly reminder that estimate {estimate.estimate_number} is awaiting your review and signature."
        )
        channel = self._channel(initial)
        if channel == "sms":
            body = (
                f"NTInet final reminder: Estimate {estimate.estimate_number} is awaiting your review. "
                f"It expires in 48 hours. View and accept: {acceptance_url} "
                "Questions? We would be happy to review it with you."
                if final
                else f"NTInet reminder: Estimate {estimate.estimate_number} is awaiting your review. "
                f"View and accept: {acceptance_url} Questions? We would be happy to review it with you."
            )
            html = None
        else:
            body = "\n\n".join((
                greeting,
                reminder_text,
                "If you have any questions, we would be happy to review the estimate with you.",
                "This estimate will expire in 48 hours if it has not been accepted." if final else "",
                f"View and accept the estimate: {acceptance_url}",
                "Thank you,\nNTInet",
            )).replace("\n\n\n\n", "\n\n")
            html = templates.env.get_template("documents/estimate_reminder_email.html").render(
                estimate=estimate,
                heading="Final Estimate Reminder" if final else "Estimate Reminder",
                greeting=greeting,
                reminder_text=reminder_text,
                final_reminder=final,
                acceptance_url=acceptance_url,
            )
        record = CustomerCommunicationService(self.db).send(
            estimate.customer,
            contact_id=contact.id,
            channel=channel,
            subject=subject if channel == "email" else "",
            body=body,
            profile_id=None,
            ticket_id=None,
            consent_override=False,
            override_reason="",
            actor_user_id=actor_user_id,
            module_slug="estimates",
            html_body=html,
            estimate_id=estimate.id,
        )
        delivery = EstimateDelivery(
            estimate_id=estimate.id,
            contact_id=contact.id,
            recipient_email=contact.mobile_phone if channel == "sms" else contact.email,
            subject=subject,
            message_body=body,
            option_ids_json=json.dumps(option_ids),
            document_ids_json="[]",
            pdf_attached=False,
            acceptance_token=token,
            status=record.status,
            error_message=record.error_message,
            sent_by_user_id=actor_user_id,
            created_at=now,
        )
        self.db.add(delivery)
        self.db.flush()
        return delivery

    def _should_retry(self, delivery: EstimateDelivery, now: datetime) -> bool:
        if delivery.status in SUCCESS_STATUSES:
            return False
        retry_at = _aware(delivery.created_at) + timedelta(
            hours=max(1, get_settings().estimate_reminder_retry_hours)
        )
        return now >= retry_at

    def process_due(self, now: datetime | None = None) -> dict[str, int]:
        settings = get_settings()
        result = {"first_sent": 0, "final_sent": 0, "failed": 0, "expired": 0}
        if not settings.estimate_reminders_enabled:
            return result
        now = _aware(now or datetime.now(timezone.utc))
        estimates = list(self.db.scalars(
            select(Estimate).options(
                lazyload("*"),
                joinedload(Estimate.customer),
                selectinload(Estimate.options).selectinload(EstimateOption.lines),
                selectinload(Estimate.deliveries).joinedload(EstimateDelivery.contact),
            ).where(Estimate.status == "sent", Estimate.accepted_at.is_(None))
        ).unique())
        for estimate in estimates:
            deliveries = list(estimate.deliveries)
            initial_by_recipient: dict[tuple[int | None, str], EstimateDelivery] = {}
            for delivery in deliveries:
                if delivery.status not in SUCCESS_STATUSES or delivery.subject.startswith(
                    (FIRST_REMINDER_PREFIX, FINAL_REMINDER_PREFIX)
                ):
                    continue
                key = (delivery.contact_id, delivery.recipient_email.lower())
                previous = initial_by_recipient.get(key)
                if previous is None or _aware(delivery.created_at) > _aware(previous.created_at):
                    initial_by_recipient[key] = delivery
            final_successes: list[EstimateDelivery] = []
            for initial in initial_by_recipient.values():
                initial_at = _aware(initial.created_at)
                first = self._latest_stage(
                    deliveries, FIRST_REMINDER_PREFIX, initial_at, initial.contact_id
                )
                first_due = initial_at + timedelta(hours=max(1, settings.estimate_first_reminder_hours))
                if now >= first_due and (first is None or self._should_retry(first, now)):
                    first = self._send(estimate, initial, final=False, now=now)
                    if first:
                        deliveries.append(first)
                        result["first_sent" if first.status in SUCCESS_STATUSES else "failed"] += 1
                if not first or first.status not in SUCCESS_STATUSES:
                    continue
                first_at = _aware(first.created_at)
                final = self._latest_stage(
                    deliveries, FINAL_REMINDER_PREFIX, first_at, initial.contact_id
                )
                final_due = first_at + timedelta(hours=max(1, settings.estimate_second_reminder_hours))
                if now >= final_due and (final is None or self._should_retry(final, now)):
                    final = self._send(estimate, initial, final=True, now=now)
                    if final:
                        deliveries.append(final)
                        result["final_sent" if final.status in SUCCESS_STATUSES else "failed"] += 1
                if final and final.status in SUCCESS_STATUSES:
                    final_successes.append(final)
            if initial_by_recipient and len(final_successes) == len(initial_by_recipient):
                expiration_at = max(_aware(item.created_at) for item in final_successes) + timedelta(
                    hours=max(1, settings.estimate_expiration_after_final_hours)
                )
                if now >= expiration_at:
                    estimate.status = "expired"
                    result["expired"] += 1
        return result
