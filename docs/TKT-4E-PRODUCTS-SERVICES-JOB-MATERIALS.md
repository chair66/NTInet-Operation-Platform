# TKT-4E — Products, Services, and Job Materials

Version 1.20.0 adds an NTInet-only pricing catalog for products, services, materials, labor, fees, and discounts. It intentionally does not maintain stock-on-hand quantities, serial numbers, or MAC addresses.

## Included

- Organization-scoped catalog with SKU, category, unit, internal cost, selling price, taxability, and active status.
- Customer estimates with dated pricing snapshots, discounts, tax, estimated cost, gross profit, and margin.
- Estimate line items can be copied to a matching customer's job without creating duplicates.
- Job line items track estimated versus actual usage and estimated versus actual cost.
- Job financial summary includes estimated cost, actual cost, cost variance, revenue, gross profit, and margin.
- Separate permissions protect catalog maintenance, estimates, technician material entry, and financial visibility.

## Database

Run `python -m alembic upgrade head`. The expected revision is `20260807_13 (head)`.

The migration creates `catalog_items`, `estimates`, `estimate_line_items`, and `job_line_items`.
