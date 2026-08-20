# PLAT-004B.1 — Bootstrap Tabs Hotfix and Organization Template Refactor

## Purpose

This hotfix restores Bootstrap-powered tabs on the organization detail page and separates the page into focused Jinja partials.

## Root cause

Bootstrap 5 CSS was loaded, but the Bootstrap JavaScript bundle was not. Tabs rendered correctly but could not respond to clicks.

## Changes

- Loads `bootstrap.bundle.min.js` before the closing `body` tag.
- Adds a `scripts` template block for page-specific JavaScript.
- Keeps the organization page behavior unchanged while splitting it into:
  - `_general.html`
  - `_modules.html`
  - `_settings.html`
  - `_activity.html`
- Adds complete Bootstrap tab roles and ARIA attributes.
- Preserves the selected tab in the URL hash.
- Opens a tab named in the URL hash after page load.

## Database changes

None.

## Validation

1. Open an organization detail page.
2. Click General, Modules, Security & Defaults, and Activity.
3. Confirm each pane becomes visible.
4. Refresh while the URL ends in `#modules` or `#settings` and confirm that tab remains selected.
5. Verify dropdowns and modals elsewhere in the application continue to work.

## Rollback

Restore the previous versions of:

- `app/templates/base.html`
- `app/templates/admin/organization_detail.html`

The new partial directory may then be removed.
