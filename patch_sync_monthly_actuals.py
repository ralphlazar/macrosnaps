#!/usr/bin/env python3
"""
patch_sync_monthly_actuals.py
==============================
Fixes the date truncation bug in sync_monthly_actuals.py.

Root cause: line 78 does `date_str[:7]` assuming YYYY-MM-DD format,
but the sheet stores dates as DD/MM/YYYY. So '01/02/2026'[:7] = '01/02/2'.

Fix: parse the date string properly and reformat as YYYY-MM.

Run from the macrosnaps repo directory:
    python3 ~/Downloads/patch_sync_monthly_actuals.py
"""

import sys, os

TARGET = "sync_monthly_actuals.py"

if not os.path.exists(TARGET):
    print(f"FATAL: {TARGET} not found. Run from the macrosnaps repo directory.")
    sys.exit(1)

with open(TARGET, "r", encoding="utf-8") as f:
    src = f.read()

OLD = (
    "        date_str = row[0] if row else None\n"
    "        if not date_str:\n"
    "            continue\n"
    "        month_str = date_str[:7]  # YYYY-MM"
)

NEW = (
    "        date_str = row[0] if row else None\n"
    "        if not date_str:\n"
    "            continue\n"
    "        # Sheet stores dates as DD/MM/YYYY — parse and reformat as YYYY-MM\n"
    "        try:\n"
    "            from datetime import datetime as _dt\n"
    "            month_str = _dt.strptime(date_str.strip(), '%d/%m/%Y').strftime('%Y-%m')\n"
    "        except ValueError:\n"
    "            month_str = date_str[:7]  # fallback for unexpected formats"
)

if OLD not in src:
    print("WARN: target block not found — already patched or source changed.")
    sys.exit(0)

src = src.replace(OLD, NEW, 1)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(src)

print(f"  Patched: {TARGET}")
print("  month_str now parsed correctly from DD/MM/YYYY → YYYY-MM.")
print()
print("  Next: run sync_monthly_actuals.py --apply to rewrite monthly_actuals in data.json,")
print("  then run build.py.\n")
