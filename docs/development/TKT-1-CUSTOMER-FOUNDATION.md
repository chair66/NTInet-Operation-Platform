# TKT-1 Customer Foundation

## Scope

TKT-1 establishes the operational customer directory required by Support
Tickets, Dispatch, Estimates, Inventory, and the future read-only Platypus
connector.

## Data ownership

- NOP owns operational customer, contact, location, relationship, service, and
  communication-preference information.
- Platypus will remain authoritative for synchronized billing fields.
- NOP external links contain the durable Platypus ID and a source snapshot.
- No TKT-1 workflow writes to Platypus.

## Tables

- `customers`
- `customer_contacts`
- `customer_locations`
- `customer_relationships`
- `customer_services`
- `external_record_links`

## Access rules

- NTInet staff may see all customer accounts allowed by their role.
- Non-staff organizations see customers they own or service.
- Customer creation by a non-staff user forcibly uses that user's organization.
- Direct URL access to an out-of-scope customer returns not found.
- External-link management requires the separate
  `customers.external_links` permission.

## Future dependencies

TKT-2 tickets should reference `customers.id`, with an optional
`customer_location_id`, `customer_contact_id`, and `customer_service_id`.
