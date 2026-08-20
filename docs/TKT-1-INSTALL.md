# TKT-1 Customer Foundation installation

This release assumes NOP is already running on PostgreSQL and the current
database is at Alembic revision `20260806_01`.

## 1. Stop NOP

In the PowerShell window running Uvicorn, press `Ctrl+C`.

## 2. Back up PostgreSQL and configuration

From the current project directory:

```powershell
New-Item -ItemType Directory -Force .\backups
pg_dump -Fc -U nop_app -h localhost -d nop_development -f .\backups\nop-before-tkt1.backup
Copy-Item .\.env .\backups\.env.before-tkt1
```

Enter the `nop_app` database password when prompted.

## 3. Install the release files

Extract the TKT-1 ZIP over the existing project directory. The release does
not contain a live `.env`, so the configured PostgreSQL URL is preserved.

Activate the existing virtual environment and refresh dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 4. Apply the database migration

```powershell
python -m alembic upgrade head
python -m alembic current
```

Expected current revision:

```text
20260806_02 (head)
```

This creates six new tables and does not change or remove existing NOP data.

## 5. Start NOP

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The first startup adds customer permissions, enables Customer Management for
the NTInet staff organization, and creates the six fictional demo scenarios.

Open `http://127.0.0.1:8000/customers` and verify:

- Six demo customer accounts appear.
- Pine Ridge has a contact, location, and Managed IT service.
- Carolina Demo Manufacturing has two service locations.
- Demo Wholesale Technology Partner is related to two reseller customers.
- Regional Support Account has a simulated, read-only Platypus link.
- Creating a customer assigns a `CUST-######` customer number.

## Demo data control

The default is:

```env
SEED_DEMO_CUSTOMERS=true
```

Set it to `false` before the first TKT-1 startup if demo accounts are not
wanted. Setting it to false later prevents future seeding but does not delete
records that already exist.

## Rollback

Application rollback should use the pre-TKT-1 project copy. Database rollback
should use the PostgreSQL backup created in step 2. Do not run the Alembic
downgrade against a database containing customer information you intend to
keep, because the TKT-1 downgrade removes all six customer tables.
