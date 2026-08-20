# NTInet Operations Platform LNP v1.4.0 — OnePort Edition

## Summary

LNP v1.4.0 replaces the legacy XML LNP Checker request with Bandwidth's JSON OnePort Portability Checker.

## Portability endpoint

`POST /accounts/{accountId}/porting/portability/phoneNumbers`

Request body:

```json
{
  "phoneNumbers": ["+18038549608"]
}
```

## OnePort data used by the application

The existing portability-normalization layer consumes OnePort's `data.portablePhoneNumbers` and `data.nonPortablePhoneNumbers` collections and exposes:

- Losing carrier name and SPID
- Port type
- Phone-number type
- Earliest estimate
- Rate center
- Portable telephone-number grouping
- Non-portable reasons
- Raw response under Technical Details

## Scheduling workflow

- **Use earliest available** remains the default. The application displays OnePort's `earliestEstimate` but omits `requestedFocDate` from the port-in payload so Bandwidth selects the earliest FOC.
- **Choose another date** allows a later date and prevents selecting a date before OnePort's earliest estimate.

## Deployment

After replacing the application files, restart the server:

```powershell
python -m uvicorn app.main:app --reload
```

If `.env` contains `APP_VERSION`, update it to `1.4.0` so the footer reflects this release.
