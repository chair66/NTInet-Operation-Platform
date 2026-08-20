from pathlib import Path

path = Path("app/templates/base.html")
text = path.read_text(encoding="utf-8")

old = '>SIM Inventory</a>'
new = '>SIM Management</a>'

if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("Updated sidebar label: SIM Inventory -> SIM Management")
elif new in text:
    print("Sidebar label is already updated.")
else:
    print("Sidebar SIM label was not found. No change made.")
