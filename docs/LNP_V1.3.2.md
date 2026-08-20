# LNP v1.3.2 — Conservative FOC Classification and Timezone Portability

## Changes

- Added a reusable Eastern timezone helper with a Windows-safe fallback.
- Explicitly classifies `NSR`, `LSR`, and `MANUAL` port types as manual/legacy ports.
- Only explicitly identified automated wireline or wireless ports receive an ISO-8601 timestamp.
- Missing or unrecognized port types now default to a date-only manual FOC instead of being treated as automated wireline.
- Added focused diagnostic logging for the detected port type, phone-number type, FOC profile, submitted FOC value, and `triggered` state.
- Diagnostic logging intentionally excludes subscriber names, addresses, account numbers, PINs, and telephone-number lists.

## Expected behavior

For an NSR/LSR/manual or unrecognized port, a selected date such as August 4, 2026 is submitted as:

```text
2026-08-04
```

For explicitly automated wireline or wireless ports, the application retains the timestamp behavior required by that profile.

## Windows note

Install `tzdata` in the virtual environment for daylight-saving-aware Eastern time:

```powershell
.\.venv\Scripts\python -m pip install tzdata
```
