# NTInet Operations Platform LNP v1.5.2

## Port-In Account Credential Fix

- Removes `accountNumber` and `pinNumber` from the Subscriber payload.
- Adds `wirelessInfo` only when OnePort identifies the number type as wireless/mobile.
- Keeps account and PIN values in saved drafts for operator reference.
- Omits those values from geographic/wireline port-in requests.
