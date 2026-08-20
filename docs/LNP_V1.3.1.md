# LNP v1.3.1 — Port-Type-Aware FOC Compliance

## Release date
July 28, 2026

## Changes
- Preserves Bandwidth `portType` and `phoneNumberType` from portability checking through draft, review, and submission.
- Manual and legacy NSR ports submit `requestedFocDate` as `YYYY-MM-DD` only.
- Manual ports display a fixed 11:30 AM ET activation time.
- Automated ports submit a complete ISO 8601 timestamp with the correct Eastern daylight/standard-time offset.
- Automated wireline ports include `triggered: true` only when requesting a time other than 11:30 AM ET.
- Automated wireless ports omit `triggered`.
- Replaces the combined datetime control with separate FOC date and activation-time controls.
- Adds tests covering manual, wireline, wireless, EDT, and EST payload behavior.

## Database changes
None.

## Upgrade notes
Replace the application files and restart the service. Existing drafts remain compatible; older drafts without port metadata default to automated wireline behavior.
