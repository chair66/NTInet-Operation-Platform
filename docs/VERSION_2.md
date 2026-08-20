# DigiCloud Bandwidth Portal 2.0

## Milestone 1 — API foundation

Version 2 begins by separating Bandwidth capabilities into focused services and matching the current Bandwidth App behavior where verified against the live account.

### Implemented in this milestone

- Added a dedicated `MessagingService`.
- Campaign dropdown now uses:
  - `GET /api/v2/accounts/{accountId}/products/messaging/a2pCampaigns/`
- Only active campaigns are offered for assignment.
- Campaign ID, description, message class, created date, imported flag, and status are normalized.
- TN SMS parsing prioritizes the nested `A2pSettings` object instead of accepting the first `CampaignId` found anywhere in TN details.
- Bandwidth client now supports endpoint-specific `Accept` headers.
- Existing number, routing, ordering, CSR, port-in, and port-out features remain available during the migration.

### Next milestone

- Authentication and session management.
- Staff/admin/reseller roles.
- Database-backed tenant, site, location, and TN assignments.
- Audit log for every mutating action.
- Capability-aware navigation and permissions enforced in backend services.


## Milestone 2 — authoritative TN messaging state

- Reads SMS/A2P values directly from `TelephoneNumberDetails/MessagingSettings`.
- Shows the provisioned campaign, message class, provisioning status, A2P state, and assigned NN route.
- Treats an empty campaign-list response as an API-credential limitation rather than a permissions failure.
- Disables campaign reassignment when Bandwidth does not return available campaign choices.

## Milestone 3 — User Experience and Error Handling

- Added a centralized Bandwidth error translator with friendly, actionable messages.
- Raw HTTP status, request URL, latency, and provider payload are now placed under Technical Details.
- Number-search HTTP 400 responses no longer appear as unexplained API failures.
- Added Area Code, City, Rate Center, and Advanced search modes.
- Added dynamic city and rate-center suggestions based on the selected area code/state.
- Added clearer empty-result guidance.
