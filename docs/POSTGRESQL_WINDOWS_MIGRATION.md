# NOP SQLite to PostgreSQL migration on Windows

This release adds PostgreSQL support without modifying the source SQLite file.
Complete the first run against `nop_test`, validate it, and only then repeat
against `nop_development`.

## 1. Preserve the source

Stop NOP and run from the project directory:

```powershell
Copy-Item .\ntiops.db .\ntiops.pre-postgresql.db
```

Keep that copy unchanged until the PostgreSQL cutover is fully accepted.

## 2. Update the Python environment

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3. Configure the test database

Copy the existing `.env` to a safe backup. Change only `DATABASE_URL` initially:

```env
DATABASE_URL=postgresql+psycopg://nop_app:URL_ENCODED_PASSWORD@localhost:5432/nop_test
```

Use the `nop_app` password, not the `postgres` administrator password. If the
password contains reserved URL characters, URL-encode them.

## 4. Create the PostgreSQL schema

```powershell
alembic upgrade head
alembic current
```

`alembic current` must report `20260806_01 (head)`.

## 5. Import into nop_test

The destination must be empty except for the Alembic schema.

```powershell
python .\scripts\migrate_sqlite_to_postgresql.py --sqlite .\ntiops.pre-postgresql.db
```

The import runs as one PostgreSQL transaction. An error rolls back all copied
rows. It does not alter the SQLite file.

## 6. Validate

```powershell
python .\scripts\validate_postgresql_migration.py --sqlite .\ntiops.pre-postgresql.db
```

Every table must report `OK` before proceeding.

## 7. Test NOP against nop_test

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Test platform-admin login, organization and user screens, module visibility,
DigiCloud domains and numbers, LNP records, mobile plans, audit logging, and a
test email. Stop NOP after testing.

## 8. Recreate nop_development if necessary

Only use these commands if `nop_development` is still disposable and contains
no needed PostgreSQL data:

```powershell
psql -U postgres -h localhost -d postgres
```

At the `postgres=#` prompt:

```sql
DROP DATABASE nop_development WITH (FORCE);
CREATE DATABASE nop_development OWNER nop_app;
\q
```

## 9. Final Windows cutover

Change `.env`:

```env
DATABASE_URL=postgresql+psycopg://nop_app:URL_ENCODED_PASSWORD@localhost:5432/nop_development
```

Then run:

```powershell
alembic upgrade head
python .\scripts\migrate_sqlite_to_postgresql.py --sqlite .\ntiops.pre-postgresql.db
python .\scripts\validate_postgresql_migration.py --sqlite .\ntiops.pre-postgresql.db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do not run the application against SQLite and PostgreSQL simultaneously. Keep
the SQLite backup and the pre-migration project archive as the rollback point.

## Resetting a failed test attempt

The migration refuses to copy into populated tables. To repeat a disposable
test migration:

```powershell
psql -U postgres -h localhost -d postgres
```

```sql
DROP DATABASE nop_test WITH (FORCE);
CREATE DATABASE nop_test OWNER nop_app;
\q
```

Then point `DATABASE_URL` to `nop_test` and repeat steps 4 through 6.
