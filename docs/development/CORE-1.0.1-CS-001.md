# Core v1.0.1 — CS-001 UI Stabilization

## Completed

- Confirmed the Users action dropdown works when the application is opened through FastAPI rather than as a local `file://` template.
- Removed the duplicate Bootstrap JavaScript include from the Users template.
- Centralized page-specific scripts in the existing Jinja `scripts` block.
- Improved bulk-selection behavior with a correct indeterminate Select All state.
- Added explicit button types and accessible labels to interactive controls.
- Improved modal accessibility attributes.
- Added a local favicon to eliminate the harmless `/favicon.ico` development-console error.
- Corrected spacing on organization summary and filter panels.

## Scope

No business functionality or database behavior was changed.
