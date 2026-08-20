# Customer detail incomplete-record hotfix

Version 1.24.1 prevents the customer detail page from failing when an older or
externally-created customer references an organization record that is no longer
available.

The customer service now loads the detail page's organization and collection
relationships before the database session is detached. The page also displays
safe fallback labels when owner, source, status, or customer-type data is
missing.

No database migration is required for this hotfix.

