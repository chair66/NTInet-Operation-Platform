# NTInet Operations Platform

## Project Objective

Build a secure, browser-based operations portal for NTInet staff and authorized resellers to manage DigiCloud services from one place.

The platform is intended for a small business environment with approximately 10 resellers. It should remain simple, reliable, easy to maintain, and easy to expand through self-contained modules.

## Primary Users

### NTInet Super Admin
- Full access to all organizations, users, roles, modules, settings, and audit records
- Controls which modules each reseller organization can access

### NTInet Staff
- Manages DigiCloud services
- Supports reseller organizations
- Manages tickets according to assigned permissions

### Reseller Admin
- Manages users and roles within their own organization
- Accesses only the modules enabled by NTInet

### Reseller User
- Uses only the modules and functions assigned through their role

## Core Platform

The core platform provides the shared framework used by every module.

- Authentication and secure sessions
- Password management and password reset
- Multi-factor authentication and trusted devices
- Organization management
- User management
- Role and permission management
- Organization-level module access
- Audit logging
- Email and SMS notification framework
- Reusable communication templates

The core should remain stable and contain no DigiCloud-specific, Bandwidth-specific, or ticketing-specific business logic.

## Initial Modules

### DigiCloud

#### Domains
- View domains
- Create domains
- Edit supported domain settings
- Suspend or restore domains where supported
- Add and manage domain users

#### LNP Management
- View number inventory
- Search and order numbers
- Move and manage numbers
- View and manage port orders
- Create port orders
- View port status and completed ports
- Manage supported line features

### Support

#### Ticketing
- Resellers submit tickets to NTInet
- NTInet staff review, assign, escalate, and update tickets
- Replies and communication remain attached to the ticket
- Ticket status and history are recorded
- Email notifications are sent for important ticket activity
- Attachments are supported

## Module Access

- NTInet controls which modules are available to each reseller organization.
- Roles control which actions a user may perform inside an enabled module.
- A user must have both organization module access and the required permission.

## Technical Direction

- FastAPI backend
- SQLAlchemy data layer
- Jinja2 templates
- Bootstrap interface
- HTMX or small vanilla JavaScript only where useful
- Service layer for business rules
- Provider adapters for external APIs such as NetSapiens and Bandwidth
- SQLite for local development and PostgreSQL for production when deployed

## Design Principles

- Keep the interface simple and browser compatible.
- Prefer proven server-rendered pages over heavy front-end frameworks.
- Build only what NTInet and its resellers need.
- Keep modules independent from one another.
- Keep provider API logic outside the core platform.
- Favor maintainability over unnecessary abstraction.
- Security and auditability are required throughout the platform.

## Current Scope

The current development focus is:

1. Stabilize and simplify the existing core platform.
2. Complete organization, user, role, permission, and module-access management.
3. Complete the notification and template framework.
4. Build DigiCloud Domains.
5. Build DigiCloud LNP Management.
6. Build reseller ticketing and the NTInet ticket-management backend.

## Future Modules

These are intentionally outside the current build:

- NTI Mobile
- Billing integrations
- Reporting and analytics
- Additional carrier integrations
- White-label branding
- Mobile applications

## Out of Scope

The platform is not intended to become a:

- CRM
- PSA
- ERP
- Accounting system
- Marketing automation system
- General-purpose enterprise workflow platform

## Project Filter

Before adding a feature, ask:

> Does this directly help NTInet staff or an authorized reseller manage DigiCloud services, users, module access, communications, or support tickets?

If not, the feature should be deferred unless the project scope is intentionally expanded.
