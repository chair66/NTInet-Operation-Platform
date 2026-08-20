# v1.10.0 — TKT-3A Outbound Communications

- Added safe test-mode and live outbound email/SMS ticket communications.
- Added branded ticket email and compact SMS templates.
- Added new-ticket, status-change, and resolved-ticket automatic notices.
- Added assigned-technician notices and deduplicated overdue-SLA alerts.
- Added customer channel selection, preferred-channel handling, and SMS-consent enforcement.
- Added delivery status, provider IDs, errors, attempts, exponential retry scheduling, and deduplication.
- Added authorized SMS-consent override, manual retry, startup processing of due messages, and audit events.
- Added NOP-native communication readiness and ticket delivery-history screens.
- Added PostgreSQL migration `20260806_04`.

# v1.9.0 — TKT-2 Core Ticket Management

- Added standalone Support Tickets module with organization assignments and permissions.
- Added `TKT-######` tickets linked to customers, contacts, locations, and services.
- Added priorities, statuses, ticket types, assignment, due dates, and SLA targets.
- Added customer-visible replies, private internal notes, and chronological activity history.
- Added controlled file/image attachments with authorized downloads and a 10 MB limit.
- Added ticket search, filters, metrics, customer ticket history, audit events, and demo tickets.
- Added PostgreSQL migration `20260806_03`.

# v1.8.2 — NOP-Native Customer Layout

- Rebuilt the customer detail screen with NOP's standard Bootstrap components.
- Replaced custom card layout dependencies with cards, list groups, grid utilities, and badges.
- Standardized responsive spacing for contacts, locations, services, and account panels.

# v1.8.1 — Customer Card UI Hotfix

- Repaired malformed newline escapes in the shared stylesheet.
- Added versioned stylesheet loading to prevent stale browser CSS.
- Improved customer card typography, inner margins, row spacing, and mobile layout.
- Fixed demo-customer seeding against PostgreSQL `VARCHAR(32)` limits.

# v1.8.0 — TKT-1 Customer Foundation

- Added standalone Customer Management module and organization-module assignment.
- Added operational customer accounts with `CUST-######` identifiers.
- Added contacts with support authorization, communication preference, and SMS-consent status.
- Added multi-location customer records with dispatch and access information.
- Added customer services, customer relationships, and bill-to customer handling.
- Added generic read-only external record links for the future Platypus synchronization.
- Added search, filters, customer detail/edit screens, and contact/location editing.
- Added organization-scoped customer access for reseller and partner users.
- Added audit events and six fictional customer scenarios for development testing.

# v1.6.28 — PostgreSQL Migration Foundation

- Added PostgreSQL 18-compatible application configuration and driver support.
- Added Alembic-managed initial schema for all 28 existing NOP tables.
- Added transactional, read-only SQLite-to-PostgreSQL data migration tooling.
- Added row-count and primary-key validation for every migrated table.
- Preserved SQLite startup compatibility while requiring Alembic for PostgreSQL.
- Added a step-by-step Windows test and cutover guide.

# v1.5.3 — Provider Draft Submission Fix

- Fixed successful API responses with `ProcessingStatus: DRAFT` being incorrectly labeled Submitted.
- Added the required draft-to-submitted PUT transition.
- Added recovery of provider drafts from prior submission history.
- Corrected nested order ID and processing-status parsing.

# v1.5.2 — Port-In Account Credential Fix

- Fixed Bandwidth error 7481 by removing account number and PIN from Subscriber.
- Sends those credentials only in WirelessInfo for wireless/mobile ports.
- Geographic and wireline port requests omit account credentials from the API payload.

# v1.5.1 — Lean Draft Verification

- Simplified draft refresh to ready, changed, or failed.
- Removed contradictory alerts and false changes caused by missing legacy draft metadata.
- Added concise change details and verification time.
- No schema changes.

# v1.5.0 — Intelligent Draft Management & Port Order Timeline

- Added automatic OnePort refresh for existing drafts and pre-submission verification.
- Added change detection, portability snapshots, revision history, timeline events, and draft health.
- Added submission safeguards for stale, changed, or unavailable portability information.

## LNP v1.4.3 — FOC Context Fix

- Fixed loss of OnePort earliest-estimate metadata between portability check and customer information.
- Added signed-session fallback for portability context.
- Improved earliest-date scheduling copy and date-picker defaults.

## LNP v1.4.2 — Polish Release

- Fixed earliest FOC metadata loss between portability check and customer-information steps.
- Removed provider branding from normal LNP screens.
- Added friendly port-submission errors with retained technical diagnostics.

## LNP v1.4.1 — OnePort Carrier Group Hotfix

- Fixed a duplicate **Carrier unavailable** card produced when the OnePort parser treated the nested `losingCarrier` metadata object as a second carrier group.
- Carrier groups without telephone numbers are now suppressed when their SPID is already represented by a complete numbered group.
- Corrected the portability summary count and multiple-carrier warning for single-carrier OnePort responses.

# Changelog

## LNP v1.4.0 — OnePort Edition

- Replaced the legacy XML `/lnpchecker` portability request with Bandwidth OnePort.
- Added JSON requests to `/accounts/{accountId}/porting/portability/phoneNumbers`.
- Uses Bandwidth-provided `earliestEstimate`, carrier, SPID, port type, phone-number type, rate center, and portable grouping data.
- Retains the earliest-available scheduling workflow and raw Technical Details response.

## 1.3.1 — Port-Type-Aware FOC Compliance
- Manual/NSR ports send date-only RequestedFocDate values.
- Automated ports send ISO 8601 timestamps with Eastern offsets.
- Wireline Triggered behavior and wireless handling now follow Bandwidth port rules.
- Added separate FOC date and activation-time controls.

## 1.3.0.2 - Port Workflow and Earliest Estimate Hotfix

- Default partial-port behavior after BTN verification.
- Replacement BTN visibility and validation corrected.
- Nested earliest-estimate parsing and FOC prefill added.


## 1.3.0.1 - Portability Multi-Number Hotfix

- Fixed portability checks treating space-separated telephone numbers as one value.
- Added a centralized free-form telephone-number parser.
- Supports spaces, commas, semicolons, tabs, and new lines between numbers.
- Preserves support for formatted entries such as `(803) 854-2105`.
- Normalizes each number independently to E.164 before Bandwidth API requests.
- Removes duplicate numbers while preserving entry order.
- Rejects unrecognized non-separator text with a clear validation message.

## 1.5.5
- Added lean System Diagnostics page for database, provider API, and SMTP health.
- Added safe test-email delivery using the production notification service.
- Renamed API Diagnostics navigation item to API Log.
# v1.11.0 — TKT-3A.1 Multi-Organization Communication Profiles

- Added multiple encrypted SMTP and Bandwidth SMS profiles per organization.
- Added organization-wide and module-specific defaults with deterministic routing.
- Added optional sharing of NTInet-owned profiles with reseller organizations.
- Added reseller-scoped profile management, readiness tests, and audit events.
- Added ticket-level email and SMS profile overrides.
- Snapshots the profile name and sender identity on every outbound delivery record.
- Added optional per-profile daily sending limits while preserving safe test mode.
- Added PostgreSQL migration `20260806_05`.
# v1.12.0 — TKT-3B Customer Communications Inbox

- Added direct email and SMS actions to customer accounts and individual contacts.
- Added contact, sending-profile, and optional open-ticket selection.
- Added customer communication history with sender, destination, delivery status, and provider IDs.
- Enforced SMS consent and required a written reason for authorized overrides.
- Added customer conversation linking to existing tickets.
- Added one-click ticket creation from an unlinked conversation.
- Applied TKT-3A.1 organization routing and daily profile limits to customer messages.
- Added inbound-ready direction, thread, source, destination, and received-time fields.
- Added PostgreSQL migration `20260806_06`.

# v1.12.1 — Bandwidth Messaging OAuth Hotfix

- Replaced the customer and ticket SMS Basic-auth path with Bandwidth OAuth bearer tokens.
- Existing NTInet SMS profiles now reuse the working system Bandwidth credentials from `.env`.
- Added encrypted per-profile OAuth credentials for reseller-owned messaging profiles.
- Corrected Messaging URL construction and prevents duplicate `/users/.../messages` paths.
- Added a no-message OAuth authentication test on the communication profile page.
- Added sanitized Bandwidth Messaging token and send requests to the API Log.
- Added PostgreSQL migration `20260806_07`.

# v1.13.0 — TKT-3B.1 Bandwidth Messaging Production Integration

- Added separate public HTTPS callback endpoints for inbound SMS and outbound delivery receipts.
- Added durable, idempotent webhook event processing for Bandwidth's at-least-once delivery model.
- Updates customer and ticket messages through sending, sent, delivered, and failed states.
- Records provider error codes, descriptions, and delivery/failure timestamps.
- Matches inbound replies to the most recent customer or ticket conversation.
- Adds inbound messages to customer communication history and linked ticket timelines.
- Applies SMS STOP and START keywords to contact consent automatically.
- Added visible consent badges and clearer contact action buttons on customer profiles.
- Added PostgreSQL migration `20260806_08`.

# v1.13.1 — PostgreSQL Migration Hotfix

- Shortened TKT-3B.1 webhook index identifiers to remain within PostgreSQL's 63-character limit.
- No schema cleanup is required when v1.13.0 failed and `alembic current` still reports `20260806_07`.

# v1.19.0 — TKT-4D Scheduling Communications

- Added automatic email and consent-aware SMS appointment confirmations.
- Added automatic reschedule and cancellation notices.
- Added queued 24-hour appointment reminders processed by the NOP background worker.
- Added email and SMS technician-en-route notifications from the TKT-4C workflow.
- Reused multi-organization communication profiles and unified customer conversation threads.
- Added durable event deduplication, superseded-reminder cancellation, delivery status, and error history on each work order.

# v1.18.0 — TKT-4C Technician Workflow

- Added a mobile-first My Work dashboard restricted to each technician's assigned jobs.
- Added guided Start Travel, Arrived, Start/Resume Work, Pause, Follow-Up, and Complete actions.
- Added controlled workflow transitions that prevent invalid or accidental status jumps.
- Added required notes for paused and follow-up work and a required completion summary.
- Added one-touch directions, customer calling, and work-order access.
- Recorded technician activity, milestone timestamps, audit events, and linked-ticket completion/follow-up notes.

# v1.17.1 — Scheduling Persistence and Time Zone Hotfix

- Fixed work-order appointment values being interpreted as UTC instead of the service location's time zone.
- Appointment times are stored in UTC and displayed in the service location's local time.
- Fixed day and week dispatch-board placement and labels for local appointment times.
- Added a prominent Save/Update Schedule button beside the appointment fields.
- Prevented the separate Manage Job form from clearing or overwriting a saved schedule and crew assignment.

# v1.17.0 — TKT-4B Calendar and Dispatch Board

- Added a Service Fusion-style daily technician timeline with an Unassigned lane.
- Added a persistent unscheduled-job queue beside the dispatch board.
- Added drag-and-drop scheduling, rescheduling, and primary-technician reassignment.
- Added 15-minute drop rounding and duration-based appointment sizing.
- Added technician overlap detection with explicit override confirmation.
- Added priority and status color coding, direct job links, date navigation, and technician filtering.
- Added a weekly technician-by-day calendar overview.
- Added dispatch-board activity and audit records for every move.

# v1.16.2 — Schedule Time Validation Hotfix

- Added immediate start/end time validation to the job scheduling card.
- When both times are entered, NOP now displays the calculated duration and updates the duration field automatically.
- Prevents submission and highlights the end-time field when it is not later than the start.
- Clarified that duration calculates the end only when the end field is blank.

# v1.16.1 — Job Scheduling Workflow UI

- Moved job scheduling into a prominent card directly below the job heading.
- Added an unmistakable amber Needs Scheduling state for unscheduled work.
- Grouped appointment start, expected end, duration, primary technician, and crew into one workflow.
- Automatically changes an Unscheduled job to Scheduled when an appointment is saved.
- Added a green scheduled state and dedicated schedule activity entries.

# v1.16.0 — TKT-4A Job Foundation

- Added the staff-only Scheduling & Dispatch module.
- Added NTInet-owned jobs with customer, active service location, contact, and optional ticket linkage.
- Added automatic `JOB-000001` numbering, job types, priorities, operational statuses, schedules, instructions, customer notes, and completion summaries.
- Added primary-technician and multi-person crew assignments.
- Added permanent job activity history and operational status timestamps.
- Added a restricted Field Technician role that can access only assigned jobs.
- Added job list, create, detail, management, filtering, quick status updates, and ticket-to-job workflows.
- Added migration `20260806_11`.

# v1.15.1 — Unread Communications Header Alert

- Added a prominent unread customer-message alert beside the logged-in user's name.
- Displays the total unread message count with separate email and SMS counts.
- Links directly to the Unified Communications Inbox filtered to unread conversations.
- Preserves organization scoping for reseller users while allowing NTInet staff to see platform-wide unread communications.

# v1.15.0 — TKT-3C.1 GreenGeeks Inbound Email

- Added encrypted, organization-scoped GreenGeeks IMAP settings to Email Communication Profiles.
- Added read-only incremental mailbox polling with UID and Message-ID deduplication.
- Added reply threading, linked ticket timeline notes, in-app alerts, and staff/reseller email notifications.
- Added the Notifications page, unread badge, connection testing, and manual inbox sync.
- Added migration `20260806_10`.

# v1.14.0 — TKT-3C Unified Communications Inbox

- Added a shared Communications Inbox for customer email and SMS conversations.
- Groups individual communication records into expandable chronological threads.
- Backfills existing TKT-3B communication history without deleting or rewriting messages.
- Added unread counts, mark-read actions, assignment, open/waiting/closed statuses, and search filters.
- Added direct replies from a conversation with existing communication-profile routing and SMS consent enforcement.
- Added ticket linking and one-click ticket creation from complete conversations.
- Added expandable conversation cards to customer profiles and customer communication history.
- Groups SMS by customer/contact and email by normalized subject, including Re/Fwd prefixes.
- Added email Message-ID, In-Reply-To, and References storage for the upcoming mailbox connector.
- Added PostgreSQL migration `20260806_09`.
