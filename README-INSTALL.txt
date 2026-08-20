NTIM-002A — Mobile Data Foundation

This package adds:
- Seven NTI Mobile database tables
- Real database counts on the NTI Mobile dashboard
- Database-backed list pages
- A starter plan seeding command
- Staff-only checks inside every mobile route

Files
-----
app\database\mobile_models.py
app\database\install_mobile_schema.py
app\database\seed_mobile.py
app\routers\mobile.py
app\templates\mobile\dashboard.html
app\templates\mobile\list.html

Installation
------------
1. Stop Uvicorn.

2. Back up the database:
   $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
   Copy-Item .\ntiops.db ".\backups\ntiops-before-NTIM-002A-$stamp.db"

3. Extract this ZIP into:
   C:\Users\chair\Documents\ntinet-operations-platform

4. Allow it to merge with the existing app folder and replace app\routers\mobile.py
   and app\templates\mobile\dashboard.html.

5. Create the tables:
   python -m app.database.install_mobile_schema

6. Add the starter plan records:
   python -m app.database.seed_mobile

7. Restart:
   uvicorn app.main:app --reload

8. Test:
   http://127.0.0.1:8000/mobile
   http://127.0.0.1:8000/mobile/plans
   http://127.0.0.1:8000/mobile/orders
   http://127.0.0.1:8000/mobile/customers
   http://127.0.0.1:8000/mobile/lines
   http://127.0.0.1:8000/mobile/sims
   http://127.0.0.1:8000/mobile/ports
   http://127.0.0.1:8000/mobile/exceptions

Notes
-----
- No provider API calls are made.
- Monthly plan prices are seeded as $0.00 placeholders.
- All mobile routes explicitly require NTInet platform staff.
- New Order and Add SIM pages remain foundation placeholders until NTIM-002B.
