# NTInet Operations Platform (NOP) — Codex Handoff

Last updated: 2026-08-20  
Current working baseline discussed in ChatGPT: NOP77 / application version `v1.7.96`

## Purpose of this file

This document transfers the important architectural decisions, implementation history, provider behavior, current defects, and next steps from the long-running ChatGPT NOP project into Codex.

Before changing code, Codex must inspect the actual repository and treat it as the source of truth. The user's active repository is normally:

```text
C:\Users\chair\Documents\ntinet-operations-platform
```

Do not assume every patch described below was installed successfully. Confirm the current application version, routes, models, migrations, templates, and Git status first. Preserve unrelated local changes.

## Start-here instructions for Codex

1. Read this entire file.
2. Inspect `AGENTS.md` and any repository-specific instructions.
3. Inspect Git status and the current branch before editing.
4. Locate the DigiCloud user-creation routes, NetSapiens providers, Platypus billing service, customer-rate workflow, models, and templates.
5. Compare the installed code with the NOP77 behavior documented here.
6. Run existing tests before modifying anything.
7. Add focused tests for every provider request and partial-failure recovery path.
8. Never perform a live destructive provider call without explicit authorization.

## Company and product context

NOP is the internal operations platform for NTInet Inc and related services:

- NTInet Inc: ISP and direct billing organization.
- DigiCloud PBX: hosted voice platform built on NetSapiens SiPBx.
- NTI Mobile: planned MVNO integration.
- Platypus 7: billing platform.
- Bandwidth: telephone-number, messaging, and porting carrier.
- Plume: managed Wi-Fi platform.

Primary users include NTInet staff, referral partners, third-party support users, and wholesale/white-label DigiCloud resellers.

## Core NOP architecture

- Backend: FastAPI and Uvicorn.
- Development workstation: Windows with PowerShell and a Python virtual environment.
- Database: PostgreSQL for current development; older builds used SQLite.
- Common development database: `nop_development`.
- Platypus is accessed through its API.
- DigiCloud is accessed through NetSapiens APIs.
- NOP is intended to become the authoritative operational system; Platypus is downstream for billing.

## System-of-record decisions

### Customers and operational services

NOP is the authoritative system for new customers, services, and operational relationships.

### Billing

Platypus remains the billing engine. NOP creates or updates the corresponding Platypus customer rates and service instances.

### DigiCloud

NetSapiens/DigiCloud remains authoritative for live domains, subscribers, numbers, devices, call features, and emergency-number configuration. NOP stores durable links and workflow state so partial provisioning is visible and repairable.

## Security and access rules

- Staff may manage direct NTInet customers and provider integrations according to permissions.
- Resellers must only see their own organization and allowed DigiCloud domains.
- Wholesale resellers must never select or override another Platypus billing account.
- Third-party support must not receive staff-only service-addition or billing controls.
- SIP passwords must never be stored in NOP or written to audit logs.
- A newly generated or reset SIP password may be displayed once on a protected completion page.
- Live deletion must identify the exact linked provider objects before acting.

## DigiCloud billing models

NOP supports three organization labels but two provisioning workflows.

| Billing model | Provisioning begins from | Platypus billing account |
|---|---|---|
| Direct | Customer profile → Manage Rates | Individual customer's Platypus account |
| Referral | Customer profile → Manage Rates | Individual customer's Platypus account |
| Wholesale / white label | DigiCloud → Users → Add User | Reseller's locked parent Platypus account |

### Direct and referral workflow

1. Open the NOP customer.
2. Open Manage Rates.
3. Select a DigiCloud voice rate.
4. Route to the DigiCloud Add User form with the customer and rate locked.
5. Provision the DigiCloud subscriber, DID, device/manual credentials, voicemail settings, billing rate, Digital Phone service, and Legacy 911.
6. Store a durable NOP relationship linking the customer, DigiCloud subscriber, and Platypus objects.

Known residential DigiCloud RGIDs discussed during implementation:

```text
249
98
99
```

### Wholesale workflow

1. A reseller parent customer must already exist in Platypus.
2. The reseller organization is configured in NOP with:
   - Billing model `wholesale`.
   - Parent Platypus customer ID.
   - Allowed DigiCloud domains.
   - Permitted wholesale RGIDs.
   - Default wholesale RGID.
3. The reseller creates a subscriber from DigiCloud → Users.
4. NOP resolves the billing target server-side from the organization/domain.
5. Each subscriber receives its own Platypus rate and service instance beneath the reseller parent account.

The reseller parent billing account must be read-only in the UI and ignored if a different value is posted by a client.

## DigiCloud subscriber identity

For residential and business voice service, the same 10-digit DID is used consistently:

```text
Phone number:        8035551212
DigiCloud extension: 8035551212
DigiCloud username:  8035551212
Billing reference:   8035551212
```

Do not substitute a short-extension fallback for these billed voice products.

## Platypus rate and service requirements

Each billed DigiCloud subscriber requires:

1. One Platypus customer rate with a real CRID.
2. One service instance associated with that specific CRID.
3. The service-tree entry named **Digital Phone**.

Important correction discovered during testing:

- Service `264` was initially assumed to be the target, but on the tested live rate it represented **ATA**.
- The correct live service-tree entry was **Digital Phone**, observed as SVC `300` for CRID `13078`.
- Code must select by the live service-tree identity/name and must not fall back to the first writable service definition.
- Do not hard-code SVC `300` globally without verifying the assigned rate's live service tree.

The service mapping includes subscriber-specific values such as the 10-digit number and, when applicable, device MAC address.

### CRID lookup behavior

Testing found that Platypus service definitions may not be available using CRID `0`. The correct order is:

1. Create or reuse the real customer rate.
2. Obtain its real CRID.
3. Query the assigned-rate service definition using the real CRID.
4. Prefer a CRID-only lookup (`RGID 0` plus the actual CRID) when required by the Platypus API behavior.
5. Discover the Digital Phone service from the live service tree.
6. Add the service instance and populate its fields.

Retries must reuse an incomplete CRID rather than create duplicate monthly rates.

## Device provisioning requirements

The Add User form supports distinct device modes:

### Manual provisioning credentials

- MAC address is optional.
- NOP creates or retrieves the necessary SIP device credentials.
- SIP username and password are displayed once.
- Password is not stored in NOP or audit logs.
- If credentials are later needed, the user must explicitly reset the SIP password; the new password is displayed once and the old password stops working.

### Assign available phone hardware

- MAC address is required.
- MAC must be normalized and validated as 12 hexadecimal characters.
- Hardware is selected from available inventory and linked to the subscriber.

### No device yet

- MAC address is optional.
- This mode is useful for repairing billing or completing other provisioning steps without duplicating a device.

## DID selection and assignment

The intended user-creation workflow begins with a DID already present in the selected DigiCloud domain.

The Add User screen should:

- Search or list DIDs assigned to the selected domain.
- Combine live DigiCloud information with NOP's synced phone-number inventory.
- Include active and inactive numbers.
- Exclude numbers already used as an existing subscriber extension.
- Label each number with its synced status.
- Re-enable an inactive DID when assigning it to a new user.

NOP must not create duplicate inventory records. A stale local domain association may be repaired only after live reseller/domain authorization is verified.

## Local NOP relationship and workflow state

NOP must create a local subscriber/service relationship as soon as the DigiCloud user and DID assignment succeed—before billing and 911 are complete.

The relationship should retain enough identity to repair or reverse the workflow:

```text
NOP customer ID, when direct/referral
NOP reseller organization ID, when wholesale
DigiCloud domain
DigiCloud subscriber/extension
Phone number
Device MAC, if present
Billing model
Platypus billing customer ID
RGID
CRID
Live service ID/name
Platypus service instance/data ID
Legacy 911 status
Overall provisioning status
```

Useful states include:

```text
pending
billing_pending
legacy_911_pending
complete
billing_cleanup_required
provider_cleanup_required
```

A downstream failure must leave a visible, repairable record rather than making the subscriber disappear from NOP.

## Coordinated deletion requirements

Deletion must use the stored relationship and proceed carefully:

1. Confirm the exact DigiCloud subscriber, DID, device, CRID, service instance, and 911 record.
2. Deactivate/remove Legacy 911.
3. Unassign/remove the device as appropriate.
4. Delete or disable the DigiCloud subscriber according to business policy.
5. Delete the correct Digital Phone service instance.
6. Delete the associated Platypus rate.
7. Mark the NOP relationship cancelled and write an audit event.

If a downstream delete fails, preserve the remaining identifiers and mark cleanup required. Never report full success when external cleanup is incomplete.

## Legacy 911: current findings

This is the highest-priority unresolved integration.

### What NOP77 currently attempted

NOP77 contains a provider based on the newer NetSapiens address API:

```text
POST /domains/{domain}/addresses/validate
POST /domains/{domain}/addresses
PUT  /domains/{domain}/users/{user}/addresses/{address_id}
```

That implementation expects or generates an emergency address ID and requires a returned PIDF-LO value. This appears to be the wrong workflow for the residential **Legacy 911** product used by `ntinet.com`.

Do not treat an HTTP `200` alone as successful validation. Inspect the returned object and reject login HTML or other unexpected responses.

### Emergency DID inventory operation confirmed from API log

The DigiCloud Manager Portal used the legacy ns-api v1 `callidemgr` object.

First it checked whether the emergency DID existed:

```text
object=callidemgr
action=count
callid=18038130007
domain=ntinet.com
```

The response was:

```text
total=0
```

It then created the emergency-number record:

```text
object=callidemgr
action=create
callid=18038130007
domain=ntinet.com
tag=
```

The provider stored the Legacy 911 DID with a leading country-code `1`:

```text
18038130007
```

The subscriber itself continues to use the 10-digit extension:

```text
8038130007
```

### Address-validation portal request confirmed from DevTools

Legacy address validation is performed by a separate Manager Portal controller:

```http
POST https://sb1geo.ntinet.com/portal/inventory/validateAddress
Content-Type: application/x-www-form-urlencoded
```

Confirmed form fields:

```text
_method=POST
data[Phonenumber][callername]=charlie bravo
data[Phonenumber][address1]=246 Pandanus Rd
data[Phonenumber][address2]=
data[Phonenumber][country]=US
data[Phonenumber][state]=SC
data[Phonenumber][community]=ORANGEBURG
data[Phonenumber][postalcode]=29115
```

Important observations:

- Validation does not include the DID.
- `community` is the city.
- The body is form-encoded, not JSON.
- This request is outside `/ns-api`.
- The `netsapiens-api/tmp/logs/debug.log` does not capture it.
- One captured HTTP `200` response was actually the full Manager Portal login page, meaning the request was unauthenticated or the session had expired. That was not a successful validation result.
- Do not implement NOP by replaying a human portal session cookie or refresh token.

### Missing Legacy 911 evidence

Before completing this integration, capture a genuinely authenticated successful validation response and the final Save request that associates the validated address with emergency DID `18038130007`.

Needed evidence:

1. Successful `/portal/inventory/validateAddress` response body.
2. Save request URL and method.
3. Save request form body.
4. Save response body.
5. Supported machine-authentication mechanism, or the underlying carrier/ns-api operation called by the portal.
6. Deactivation/delete request and response for coordinated subscriber deletion.

The portal application log must be inspected rather than only the ns-api log. Useful server-side discovery commands include:

```bash
sudo find /usr/local/NetSapiens -type f \
  \( -name "debug.log" -o -name "error.log" \) \
  -mmin -5 -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort

sudo grep -R "validateAddress" /var/log/apache2 /var/log/httpd 2>/dev/null | tail -20
```

### Correct intended Legacy 911 workflow

Once the supported provider operations are known:

1. Normalize the selected subscriber DID to both 10-digit and `1`-prefixed forms.
2. Ensure the `callidemgr` record exists for the `1`-prefixed DID and domain.
3. Validate the submitted civic address.
4. Save/activate the address against that emergency DID.
5. Set the subscriber's emergency caller ID to the 10-digit DID if required by the subscriber API.
6. Verify by reading the provider state.
7. Mark Legacy 911 active only after verification.
8. On deletion, deactivate/remove the exact Legacy 911 record and verify removal.

Do not mark the overall subscriber workflow complete while 911 is merely pending.

## NOP77 behavior discussed before handoff

NOP77 / `v1.7.96` was intended to include:

- Reset-and-show-new-password action on the phone edit page.
- Credentials displayed once.
- Required 911 form directly on the credentials page.
- Local pending subscriber record created before billing/911 completion.
- Deferred **911 Setup** button for failed or unfinished provisioning.

Verify these behaviors in the installed repository. They may have been distributed as overlay ZIP patches and are not guaranteed to be present in the user's current checkout.

## Relevant PostgreSQL migration history

The wholesale billing work introduced fields on `digicloud_organization_settings`, including:

```text
billing_model
platypus_parent_customer_id
wholesale_rate_group_ids
default_wholesale_rate_group_id
```

An older field named `platypus_billing_model` may also exist. The newer workflow was intended to use `billing_model`.

Migration discussed:

```text
migrations/v1.7.87_digicloud_wholesale_billing_postgresql.sql
```

The user confirmed the new columns existed in PostgreSQL. Codex should still inspect the live migration history and model/schema parity.

## DigiCloud user and feature requirements already established

- Residential domain: `ntinet.com`.
- Legacy 911 is required for residential voice; Dynamic 911 is not required for this workflow.
- First name, last name, email, time zone, and emergency caller ID are managed.
- Directory listing defaults off.
- Audio directory defaults off.
- Voicemail storage default: 50 MB.
- “Receive an email for new voicemail” defaults disabled on user creation.
- Device setup belongs at the bottom of the Add User form.
- Answering rules support DND, screening, forwarding states, simultaneous ring, ring duration, ring-all-phones, and answer confirmation for off-net destinations.
- Simultaneous Ring and Forward Always are mutually exclusive.
- Residential DigiCloud user deletion should not delete an unrelated NOP platform login user.

## Customer selection UI requirement

The billing customer list is too large for a full dropdown. Direct/referral Add User must use an on-demand searchable customer lookup.

Search should support:

- Customer name.
- NOP customer number.
- Platypus customer number.
- Email.
- Phone.

Return a small bounded result set, previously discussed as no more than 20 active Platypus-linked matches.

## Plume integration summary

NOP also contains a substantial Plume managed-Wi-Fi integration. Preserve it while modifying shared customer/rate code.

Implemented or discussed capabilities include:

- Customer/location/pod lookup.
- Pod health and connected/unconnected devices.
- Device detail, signal, QoE, link rate, band steering, and history.
- Speed-test initiation and history.
- Staff-only onboarding and pod management.
- Gateway vs extender classification.
- Extender billing rate reference RGID `298`.
- Customer information card with SSID/email.
- Email Wi-Fi details action.
- Coordinated pod and billing cleanup.

Known test customers:

- Charlie Bravo: residential/device/911 testing.
- Santee General Store: business Plume onboarding testing.

Do not regress Plume customer profile links or rate/service behavior while changing shared billing code.

## Customer and Platypus integration summary

- NOP customer names link to profiles.
- Customer information includes contact and service/billing addresses.
- Rates and services appear on the customer profile.
- Customer notes from Platypus should appear in a dismissible modal titled **Customer Notes**.
- Completed notes should not reappear as active popups.
- Staff-only customer merge/delete behavior exists or is under development.
- The project previously imported roughly 5,500 Platypus customers and included rules for older inactive accounts.

Treat the uploaded Platypus 7 API documentation in the project as the primary reference for Platypus operations.

## Safe testing strategy

### Local/static tests

- Python compilation and import checks.
- Route registration checks.
- Template rendering checks.
- Provider request-shape unit tests using mocked HTTP responses.
- Platypus retry/idempotency tests.
- Validation of manual/no-device versus assigned-hardware MAC rules.
- Tests that reseller-posted billing-account overrides are ignored.
- Tests that HTML login pages cannot be treated as provider success.

### Live non-destructive tests

- Read domains and subscribers.
- Read/sync phone-number inventory.
- Read `callidemgr` records.
- Read Platypus customer rates and service trees.
- Verify current local relationship records.

### Live write tests

Require the user's explicit approval and an identified test customer/DID. Before writing, show the exact systems and objects that will be changed. Never use production deletion as a diagnostic step.

## Immediate next milestone

Complete and test an idempotent two-model DigiCloud provisioning workflow with a supported Legacy 911 integration.

Acceptance criteria:

1. Direct/referral starts from Customer → Manage Rates.
2. Wholesale starts from DigiCloud → Users and automatically bills the locked reseller parent.
3. Only an eligible DID already in the domain can be selected.
4. Ten-digit subscriber identity is enforced.
5. Manual provisioning does not require a MAC and displays credentials once.
6. Assigned inventory hardware requires a valid MAC.
7. One real Platypus rate and one live **Digital Phone** service are created per subscriber.
8. Retries reuse incomplete external objects and do not duplicate billing.
9. NOP stores a pending relationship before downstream work.
10. Legacy 911 is validated, activated, associated, and verified through a supported machine API.
11. The workflow is complete only after billing and 911 verification.
12. Deletion removes/deactivates the exact 911, DigiCloud, device, service, and rate objects or clearly marks cleanup required.

## Suggested first prompt in Codex

```text
Read NOP_CODEX_HANDOFF.md completely. Inspect AGENTS.md, Git status, the current
application version, and the installed DigiCloud/Platypus implementation before
editing. Determine which NOP77 behaviors are actually present. Then report the
current code paths for DigiCloud user creation, DID selection/assignment,
manual SIP credentials, Platypus rate plus Digital Phone service creation,
local pending-state persistence, Legacy 911 setup, and coordinated deletion.
Do not make live provider calls or modify code yet. Identify discrepancies
between the repository and the handoff, then propose the smallest safe next
patch and focused tests.
```

## Files to place beside this handoff

Create the following repository directory if it does not already exist:

```text
docs/investigation/legacy-911/
```

Place the captured logs there with descriptive names, for example:

```text
docs/investigation/legacy-911/callidemgr-create-8038130007.log
docs/investigation/legacy-911/portal-validate-attempt.log
```

Never commit raw authentication cookies, JWTs, passwords, SIP credentials, or refresh tokens.
