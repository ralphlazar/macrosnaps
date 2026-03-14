#!/usr/bin/env python3
"""
sync_monthly_historical.py

Reads the MACRO-MONTHLY Google Sheet (Inflation, Unemployment, Policy_Rate tabs)
and writes _frozen_historical arrays into data.json for all 12 countries for
those three metrics, covering all rows from 2020-01-01 onwards.

This replaces refetch_historical.py as the source of truth for these three
monthly metrics. Annual metrics (GDP Growth, Budget Deficit, Current Account)
are unaffected and continue to be owned by sync_sheet.py.

Usage:
    python3 sync_monthly_historical.py             # dry run (preview only)
    python3 sync_monthly_historical.py --apply     # write to data.json

Auth: uses same market-stats-key.json service account as sync_market_sheet.py.
Env:  MACRO_MONTHLY_SHEET_ID must be set in .env
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Missing dependencies. Run: pip3 install gspread google-auth --break-system-packages")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

APPLY = "--apply" in sys.argv
START_DATE = date(2020, 1, 1)

DATA_FILE = Path(__file__).parent / "data.json"
KEY_FILE  = Path(__file__).parent / "market-stats-key.json"

SHEET_ID = os.environ.get("MACRO_MONTHLY_SHEET_ID", "")
if not SHEET_ID:
    print("ERROR: MACRO_MONTHLY_SHEET_ID not set in .env")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Tab name in the sheet -> metric key in _frozen_historical
TAB_TO_METRIC = {
    "Inflation":    "Inflation (CPI)",
    "Unemployment": "Unemployment",
    "Policy_Rate":  "Policy Rate",
}

# Column order in each tab: A=Date, B=USA, C=CAN, ... M=RUS
COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

# Known data gaps: these combos will always be empty in the sheet.
# We write {"v": [], "type": "line"} so the chart shows nothing rather than stale data.
KNOWN_GAPS = {
    ("CHN", "Unemployment"),
    ("IND", "Unemployment"),
    ("BRA", "Unemployment"),
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_sheet_client():
    if not KEY_FILE.exists():
        print(f"ERROR: service account key not found at {KEY_FILE}")
        sys.exit(1)
    creds = Credentials.from_service_account_file(str(KEY_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


# ---------------------------------------------------------------------------
# Read one tab and return {country_code: [value, ...]} from 2020 onwards.
# Values are floats; blank/None cells are skipped.
# ---------------------------------------------------------------------------

def read_tab(worksheet):
    """
    Returns a dict: {country_code: [float, ...]}
    Only rows with date >= START_DATE are included.
    Blank cells produce no value (they are skipped, keeping adjacent months intact).
    """
    all_rows = worksheet.get_all_values()
    if not all_rows:
        return {c: [] for c in COUNTRIES}

    result = {c: [] for c in COUNTRIES}

    for row in all_rows:
        if not row or not row[0]:
            continue
        # Parse date column (format: YYYY-MM-01 or YYYY-MM-DD)
        try:
            row_date = datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
        except ValueError:
            continue  # Skip header or unparseable rows

        if row_date < START_DATE:
            continue

        for i, code in enumerate(COUNTRIES):
            col_idx = i + 1  # Column A=0 is date; B=1 is USA, etc.
            if col_idx >= len(row):
                continue
            cell = row[col_idx].strip()
            if not cell:
                continue
            try:
                result[code].append(float(cell))
            except ValueError:
                continue

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mode = "APPLY" if APPLY else "PREVIEW (dry run)"
    print(f"\nsync_monthly_historical.py [{mode}]")
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Data from: {START_DATE} onwards\n")

    # Load data.json
    with open(DATA_FILE) as f:
        data = json.load(f)

    # Auth
    client = get_sheet_client()
    spreadsheet = client.open_by_key(SHEET_ID)

    # Collect all writes: {country_code: {metric_label: [values]}}
    writes = {c: {} for c in COUNTRIES}

    for tab_name, metric_label in TAB_TO_METRIC.items():
        print(f"Reading tab: {tab_name} -> {metric_label}")
        try:
            ws = spreadsheet.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"  WARNING: tab '{tab_name}' not found in sheet. Skipping.")
            continue

        tab_data = read_tab(ws)

        for code in COUNTRIES:
            values = tab_data[code]
            is_gap = (code, metric_label) in KNOWN_GAPS

            if is_gap:
                writes[code][metric_label] = []
                print(f"  {code}: {metric_label} - known gap, writing empty array")
            elif not values:
                writes[code][metric_label] = []
                print(f"  {code}: {metric_label} - no data found, writing empty array")
            else:
                writes[code][metric_label] = values
                print(f"  {code}: {metric_label} - {len(values)} points "
                      f"({values[0]:.2f} ... {values[-1]:.2f})")

    print()

    # Apply to data.json
    countries_missing = []
    for country_data in data.get("countries", []):
        code = country_data.get("code")
        if code not in writes:
            continue

        frozen = country_data.setdefault("_frozen_historical", {})

        for metric_label, values in writes[code].items():
            entry = {"v": values, "type": "line"}
            # Policy Rate is stepped
            if metric_label == "Policy Rate":
                entry["stepped"] = True

            old_entry = frozen.get(metric_label, {})
            old_count = len(old_entry.get("v", []))
            new_count = len(values)

            if APPLY:
                frozen[metric_label] = entry
                print(f"  WRITE {code} / {metric_label}: {old_count} -> {new_count} points")
            else:
                print(f"  WOULD WRITE {code} / {metric_label}: {old_count} -> {new_count} points")

    if APPLY:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\ndata.json updated. Run: python3 build.py")
    else:
        print(f"\nDry run complete. Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()
