# NOP v1.19.0 — TKT-4D Scheduling Communications

## Automated customer messages

Scheduling a job sends an appointment confirmation by email and SMS when the selected customer contact has valid destinations. Moving the appointment to a different start time sends a reschedule notice and cancels the old reminder. Cancelling or clearing the appointment sends a cancellation notice.

NOP queues a reminder for 24 hours before the appointment. The background scheduling worker checks due reminders every 60 seconds. Appointments created less than 24 hours ahead receive the immediate confirmation without a redundant reminder.

When a technician selects Start Travel in My Work, NOP sends an on-the-way message.

## Profile and consent rules

Scheduling messages resolve the multi-organization communication profile for the `field-service` module, then fall back to the organization's general or support profile. They use the same email and Bandwidth SMS delivery path as customer communications.

SMS is sent only when the contact has a valid mobile number and `consented` SMS status. Scheduling automation never overrides missing consent. Suppressed and failed messages remain visible on the work order.

## Conversation history and safety

Every sent scheduling message is recorded in Customer Communication History and grouped into the existing unified email or SMS conversation. Each work order shows its scheduling communication events and delivery state.

Durable deduplication prevents restarts or repeated processing from resending the same event. Rescheduling cancels queued reminders tied to the prior appointment.

## Configuration

Optional `.env` controls:

```text
JOB_SCHEDULING_COMMUNICATIONS_ENABLED=true
JOB_APPOINTMENT_EMAIL_ENABLED=true
JOB_APPOINTMENT_SMS_ENABLED=true
JOB_REMINDER_HOURS=24
JOB_EN_ROUTE_NOTIFICATION_ENABLED=true
```

## Database

Run `python -m alembic upgrade head`. Expected revision: `20260806_12 (head)`.
