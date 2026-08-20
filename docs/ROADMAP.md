# NTInet Operations Platform Roadmap

## Status Key

- **Stable** — Working foundation; only fixes or necessary refinements expected
- **Review** — Present in the current project but needs simplification, correction, or validation
- **In Progress** — Current development work
- **Planned** — Approved scope but not yet built
- **Deferred** — Retained as a future idea and not part of the current release

## Current Focus

**Core stabilization and alignment**

The next coding work should correct known issues, simplify the organization and module structure, and confirm that tenant boundaries and permissions are enforced consistently before adding more DigiCloud functions.

## Core Platform

| Area | Status | Current Decision |
|---|---|---|
| Application framework | Stable | Keep FastAPI, Jinja2, Bootstrap, SQLAlchemy, routers, and services |
| Authentication | Stable | Keep session-based authentication and current security structure |
| Password management | Stable | Keep password change, reset, invitation, and forced-change support |
| MFA and trusted devices | Stable | Keep |
| Organizations | Review | Keep staff/reseller hierarchy; simplify fields and screens where practical |
| Users | Review | Keep; fix current UI issues and verify organization isolation |
| Roles and permissions | Review | Keep; verify reseller admins can only manage roles and users in their organization |
| Organization module access | Stable | Keep as a core requirement |
| Audit logging | Stable | Keep and use for administrative and security actions |
| Notifications | Review | Existing event/outbox foundation is present; email, SMS, and templates still need completion |
| Navigation and templates | Review | Simplify around DigiCloud, Support, and Administration |

## DigiCloud Module

| Area | Status | Objective |
|---|---|---|
| Module structure | Review | Present DigiCloud as one parent menu with Domains and LNP Management |
| Domains | Planned | Create and manage DigiCloud domains and domain users through NetSapiens |
| Number inventory | Review | Existing Bandwidth/LNP code needs alignment with reseller access rules |
| Number ordering | Review | Existing workflow needs validation and integration into DigiCloud navigation |
| Number management | Review | Validate move, feature, and location-management functions |
| Port orders | Review | Existing porting pages and services need functional and permission review |
| Provider settings | Planned | Store API/provider configuration outside the basic organization identity fields |

## Support Module

| Area | Status | Objective |
|---|---|---|
| Reseller ticket submission | Planned | Create tickets, replies, and attachments |
| NTInet ticket management | Planned | Assignment, status, escalation, internal handling, and reseller communication |
| Ticket notifications | Planned | Email notifications using core templates |
| Ticket history | Planned | Maintain a complete audit trail of replies and status changes |

## Deferred

| Item | Status | Reason |
|---|---|---|
| Provisioning engine expansion | Deferred | Keep dormant until asynchronous multi-step jobs are clearly needed |
| NTI Mobile | Deferred | Future module |
| Reporting dashboards | Deferred | Add only after operational data and clear reporting needs exist |
| Billing integrations | Deferred | Outside current release |
| White-label branding | Deferred | Not required for initial reseller deployment |
| Advanced organization health scoring | Deferred | Does not support the current operational objective |
| Enterprise policy/workflow features | Deferred | Unnecessary for the expected size of the platform |

## Immediate Coding Sequence

1. Fix the Users-page action menu and verify Bootstrap interactive components.
2. Run a tenant-boundary and permission review for organizations, users, and roles.
3. Simplify organization screens and remove or hide nonessential health/statistics features.
4. Simplify navigation to:
   - Dashboard
   - DigiCloud
     - Domains
     - LNP Management
   - Support
     - Tickets
   - Administration
5. Complete the core notification service, email delivery, SMS interface, and templates.
6. Build and validate DigiCloud Domains.
7. Consolidate and complete LNP Management.
8. Build reseller and staff ticketing.

## Completion Target for Core v1.0

Core v1.0 is complete when:

- NTInet can create and manage reseller organizations.
- NTInet can enable modules for each reseller.
- NTInet and reseller admins can manage users and roles within their permitted scope.
- Authentication, password reset, MFA, trusted devices, and audit logging operate reliably.
- Tenant isolation and permission enforcement are verified.
- Email/SMS notifications and reusable templates are available to modules.
- The navigation and user interface are stable and focused on the approved project scope.
