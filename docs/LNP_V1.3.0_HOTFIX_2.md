# LNP v1.3.0 Hotfix 2

## Port workflow and earliest estimate

- BTN verification now defaults to a partial port.
- The full-port checkbox is never selected automatically.
- When the BTN is included in the port, the Replacement BTN field is shown and required unless Full Port is explicitly selected.
- Selecting Full Port hides and disables Replacement BTN without losing the user's prior entry; switching back restores it.
- BTN-not-in-port results now display a warning rather than silently changing the workflow.
- Earliest-estimate discovery now supports nested and alternate Bandwidth response keys.
- A single carrier group's earliest estimate is carried into the customer form and used as the initial Requested FOC.
- Earliest estimate and requested FOC are both preserved in drafts and shown on review.

No database migration is required.
