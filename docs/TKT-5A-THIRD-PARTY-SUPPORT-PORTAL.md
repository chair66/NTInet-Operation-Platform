# TKT-5A — Third-Party Support Portal Foundation

NOP 1.25.2 adds a portal-only experience for outside support companies.

## Included

- Dedicated responsive portal at `/partner`
- Portal-only organization type and system role
- Search across active customers by name, number, email, phone, or address
- Limited search results that do not expose billing, rates, notes, estimates, or unrelated communications
- Customer contact, service location, and active service selection
- Ticket submission with priority, type, problem description, and partner reference
- Ticket list limited to tickets submitted by the logged-in partner organization
- Customer-visible ticket conversation, replies, and attachments
- Staff in-app notifications for partner-created tickets and replies
- Partner in-app and email notification when NTInet posts a public reply
- Audit records for portal ticket creation, replies, and attachments
- Middleware enforcement preventing portal users from accessing normal NOP modules
- Portal-branded first-login password change without exposing account or NOP navigation
- Ticket types for No Internet (All Devices or Single Device), Billing, Phone, Service Request, and Other
- Ticket conversations remain available and receive customer-visible job status history after a linked job is created

## Setup

1. In **Administration → Organizations**, create an organization with type
   **Third-Party Support**.
2. In **Administration → Users**, create the outside user's account under that
   organization.
3. Assign only the built-in **Third-Party Support Portal** role.
4. The user signs in through the normal login page and is sent directly to
   `/partner`.

Partner organizations require no NOP module assignments. Existing staff and
reseller roles should not be assigned to portal users.

## Security model

Customer search returns only the minimum identifying data needed to choose the
correct account. A partner can view only tickets with source
`third_party_portal` that were created by a user in its own organization.
Changing a ticket ID in the URL returns 404 for tickets owned by another
partner organization.

No database migration is required for TKT-5A because ticket ownership is based
on the existing ticket creator and organization relationships.
