# NOP 1.26.2 — Role-aware dashboards and module navigation

NOP now presents different workspaces to NTInet staff and reseller users.

## NTInet operations workspace

The NTInet dashboard prioritizes active customers, open and urgent tickets,
unscheduled jobs, unread communications, recent tickets, and recent jobs.

The primary menus are:

- **Customers:** all customers, add customer, communications
- **Tickets:** all tickets, new ticket, new queue, waiting on customer,
  communication settings
- **Jobs:** all jobs, new job, technician work, estimates, products and
  services, catalog categories
- **Dispatch:** dispatch board, calendar, unscheduled jobs

Less frequently used telecom and administrative areas remain under **Modules**.

## Reseller workspace

The reseller dashboard is assembled from the organization's enabled module
assignments. A reseller sees only module cards, desktop menus, contextual
submenus, mobile drawer links, and routes allowed by both its enabled modules
and assigned permissions.

Supported dashboard cards include Numbers & LNP, DigiCloud, DigiCloud Users,
NTI Mobile, Customers, and Support Tickets.

The existing third-party support portal remains separate at `/partner`.

## LNP dashboard status

Organizations with the LNP module and port-read permission see organization-
scoped counts for drafts, open ports, FOC, exceptions, and completed ports,
plus recent port activity. A provider outage does not prevent dashboard access;
the panel retains the local draft count and reports that live status is
temporarily unavailable.

The NTInet dashboard places Recent Tickets and Recent Jobs above the LNP status
panel. Its top metrics are Open Tickets, Unscheduled Jobs, and Unread Messages;
the Active Customers metric is intentionally omitted.

No database migration is required.
