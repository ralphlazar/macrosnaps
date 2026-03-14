#!/usr/bin/env python3
"""
sync_market_historical.py

Reads the MARKET-STATS Google Sheet (one tab per country) and writes
_frozen_historical arrays into data.json for all 12 countries for the four
market metrics: Stock Market YTD, FX Rate, 10Y Bond Yield, Yield Curve.

Data is read from 2020-01-01 onwards. Daily rows are resampled to monthly
end-of-month values (last non-blank row in each calendar month).

Stock Market is written as the raw index level (indexLabel: true).
The _frozen_historical array always contains the full series from Jan 2020.
The chart range buttons (1Y / 2Y / All) handle how much is displayed.

This replaces refetch_historical.py as the source of truth for these four
market metrics.

Usage:
    python3 sync_market_historical.py             # dry run (preview only)
    python3 sync_market_historical.py --apply     # write to data.json

Auth: uses same market-stats-key.json service account as sync_market_sheet.py.
Env:  MARKET_STATS_SHEET_ID must be set in .env
"""

import json
import os
import sys
from collections import defaultdict
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

SHEET_ID = os.environ.get("MARKET_STATS_SHEET_ID", "")
if not SHEET_ID:
    print("ERROR: MARKET_STATS_SHEET_ID not set in .env")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

# Sheet column indices (0-based after splitting each row)
# Date | Stock_Market_Index | FX_Rate | Bond_Yield_10Y | Bond_Yield_3M | Yield_Curve
COL_DATE    = 0
COL_STOCK   = 1
COL_FX      = 2
COL_BOND10Y = 3
# COL_BOND3M = 4  (not used here)
COL_YC      = 5

# Known data gaps: these combos will be empty and written as empty arrays.
KNOWN_GAPS = {
    ("CHN", "10Y Bond Yield"),
    ("CHN", "Yield Curve"),
    ("IND", "10Y Bond Yield"),
    ("IND", "Yield Curve"),
    ("BRA", "10Y Bond Yield"),
    ("BRA", "Yield Curve"),
    ("RUS", "Yield Curve"),   # Blanked - post-sanctions data gap causes misleading date shift
}

# RUS stock market truncates at June 2024 (MOEX delisted on Yahoo post-sanctions).
# We just take whatever the sheet has and don't forward-fill past the last real value.
RUS_STOCK_TRUNCATE_AFTER = date(2024, 7, 1)

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
# Resample daily rows to monthly end-of-month
# Returns: list of (year, month, value) tuples sorted ascending
# ---------------------------------------------------------------------------

def resample_monthly_last(daily_rows):
    """
    daily_rows: list of (date, value) pairs where value may be None.
    Returns list of floats (one per calendar month, last non-None value).
    Months with no data at all are skipped (not interpolated).
    """
    monthly = defaultdict(list)
    for row_date, value in daily_rows:
        if value is None:
            continue
        key = (row_date.year, row_date.month)
        monthly[key].append((row_date, value))

    result = []
    for key in sorted(monthly.keys()):
        # Take the last entry in the month
        entries = sorted(monthly[key], key=lambda x: x[0])
        result.append(entries[-1][1])
    return result


# ---------------------------------------------------------------------------
# Read one country tab
# Returns: {metric_name: [(date, value), ...]}
# ---------------------------------------------------------------------------

def read_country_tab(worksheet, code):
    all_rows = worksheet.get_all_values()
    if not all_rows:
        return {}

    series = {
        "Stock Market YTD": [],
        "FX Rate":          [],
        "10Y Bond Yield":   [],
        "Yield Curve":      [],
    }

    for row in all_rows:
        if not row or not row[0]:
            continue
        try:
            row_date = datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
        except ValueError:
            continue

        if row_date < START_DATE:
            continue

        # RUS stock: skip rows past the truncation date
        if code == "RUS" and row_date >= RUS_STOCK_TRUNCATE_AFTER:
            stock_val = None
        else:
            stock_val = _parse_cell(row, COL_STOCK)

        fx_val     = _parse_cell(row, COL_FX)
        bond_val   = _parse_cell(row, COL_BOND10Y)
        yc_val     = _parse_cell(row, COL_YC)

        series["Stock Market YTD"].append((row_date, stock_val))
        series["FX Rate"].append((row_date, fx_val))
        series["10Y Bond Yield"].append((row_date, bond_val))
        series["Yield Curve"].append((row_date, yc_val))

    return series


def _parse_cell(row, col_idx):
    if col_idx >= len(row):
        return None
    cell = row[col_idx].strip()
    if not cell:
        return None
    try:
        return float(cell)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Build _frozen_historical entry for a metric
# ---------------------------------------------------------------------------

def build_entry(metric_label, values, code):
    if (code, metric_label) in KNOWN_GAPS or not values:
        return {"v": [], "type": "line"}

    entry = {"v": values, "type": "line"}

    if metric_label == "Stock Market YTD":
        entry["indexLabel"] = True

    if metric_label == "Yield Curve":
        entry["zeroLine"] = True

    if metric_label == "Policy Rate":
        entry["stepped"] = True

    return entry


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mode = "APPLY" if APPLY else "PREVIEW (dry run)"
    print(f"\nsync_market_historical.py [{mode}]")
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Data from: {START_DATE} onwards\n")

    with open(DATA_FILE) as f:
        data = json.load(f)

    client = get_sheet_client()
    spreadsheet = client.open_by_key(SHEET_ID)

    # Collect all writes: {code: {metric: entry}}
    all_writes = {}

    for code in COUNTRIES:
        print(f"Reading tab: {code}")
        try:
            ws = spreadsheet.worksheet(code)
        except gspread.exceptions.WorksheetNotFound:
            print(f"  WARNING: tab '{code}' not found. Skipping.")
            continue

        daily_series = read_country_tab(ws, code)

        country_writes = {}
        for metric_label, daily_rows in daily_series.items():
            if (code, metric_label) in KNOWN_GAPS:
                country_writes[metric_label] = {"v": [], "type": "line"}
                print(f"  {metric_label}: known gap, writing empty array")
                continue

            monthly_values = resample_monthly_last(daily_rows)
            entry = build_entry(metric_label, monthly_values, code)

            if monthly_values:
                print(f"  {metric_label}: {len(monthly_values)} months "
                      f"({monthly_values[0]:.2f} ... {monthly_values[-1]:.2f})")
            else:
                print(f"  {metric_label}: no data")

            country_writes[metric_label] = entry

        all_writes[code] = country_writes
        print()

    # Apply to data.json
    print("--- Writes ---")
    for code, country_data in data.get("countries", {}).items():
        if code not in all_writes:
            continue

        frozen = country_data.setdefault("_frozen_historical", {})

        for metric_label, entry in all_writes[code].items():
            old_count = len(frozen.get(metric_label, {}).get("v", []))
            new_count = len(entry["v"])

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
