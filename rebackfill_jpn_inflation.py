#!/usr/bin/env python3
"""
rebackfill_jpn_inflation.py
Targeted one-time fix: overwrites column E (JPN) in the Inflation tab of
MACRO-MONTHLY using JPNCPIALLMINMEI (OECD index), with YoY computed as
(current / prior_12_months - 1) * 100.

Fetches from Dec 1999 to provide the base for Jan 2000 YoY.
Reads the date index from column A rows 2+ to align values correctly.
Only column E is written - no other country data is touched.

Run with --dry-run to preview the first 5 and last 5 computed values
without writing to the sheet.
"""

import os
import sys
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
MACRO_MONTHLY_SHEET_ID = os.getenv("MACRO_MONTHLY_SHEET_ID")
KEY_FILE = os.path.join(os.path.dirname(__file__), "market-stats-key.json")

SERIES = "JPNCPIALLMINMEI"
TAB = "Inflation"
JPN_COL = "E"  # Date=A, USA=B, CAN=C, GBR=D, JPN=E


def fred_fetch(series_id, observation_start):
    """Fetch FRED series, return {YYYY-MM-01: float or None}."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": observation_start,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    result = {}
    for obs in resp.json().get("observations", []):
        month_key = obs["date"][:7] + "-01"
        val = obs["value"]
        if val != ".":
            try:
                result[month_key] = float(val)
            except ValueError:
                result[month_key] = None
    return result


def compute_yoy(raw):
    """
    Given {YYYY-MM-01: index_level}, return {YYYY-MM-01: yoy_pct} from Jan 2000.
    Requires Dec 1999 in raw as the base for Jan 2000.
    """
    yoy = {}
    for d in sorted(raw.keys()):
        if d < "2000-01-01":
            continue
        dt = datetime.strptime(d, "%Y-%m-%d")
        prior_key = (dt - relativedelta(months=12)).strftime("%Y-%m-%d")
        if raw.get(d) is not None and raw.get(prior_key) is not None and raw[prior_key] != 0:
            yoy[d] = round((raw[d] / raw[prior_key] - 1) * 100, 2)
        else:
            yoy[d] = None
    return yoy


def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def main():
    dry_run = "--dry-run" in sys.argv

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not found in .env")
        sys.exit(1)
    if not MACRO_MONTHLY_SHEET_ID:
        print("ERROR: MACRO_MONTHLY_SHEET_ID not found in .env")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}rebackfill_jpn_inflation.py")
    print(f"Series: {SERIES} -> column {JPN_COL} of {TAB} tab")
    print()

    # Fetch JPNCPIALLMINMEI from Dec 1999 (base month for Jan 2000 YoY)
    print(f"Fetching {SERIES} from FRED (from 1999-12-01)...")
    raw = fred_fetch(SERIES, "1999-12-01")
    print(f"  {len(raw)} observations fetched")

    # Compute YoY
    yoy = compute_yoy(raw)
    print(f"  {len(yoy)} YoY values computed")
    print()

    service = get_sheets_service()

    # Read date index from column A (rows 2+)
    result = service.spreadsheets().values().get(
        spreadsheetId=MACRO_MONTHLY_SHEET_ID,
        range=f"{TAB}!A:A"
    ).execute()
    date_col = [r[0] for r in result.get("values", [])[1:] if r]
    print(f"Sheet date index: {len(date_col)} rows ({date_col[0]} to {date_col[-1]})")
    print()

    # Build column E values aligned to date index
    col_values = []
    for d in date_col:
        val = yoy.get(d)
        col_values.append([val if val is not None else ""])

    # Preview
    preview_rows = list(zip(date_col, col_values))
    print("First 5 values:")
    for d, v in preview_rows[:5]:
        print(f"  {d}: {v[0]}")
    print("Last 5 values:")
    for d, v in preview_rows[-5:]:
        print(f"  {d}: {v[0]}")
    print()

    if dry_run:
        print(f"[DRY RUN] Would write {len(col_values)} values to {TAB}!{JPN_COL}2:{JPN_COL}{len(col_values)+1}")
        print("No changes made.")
        return

    # Write column E only (row 2 onwards, skipping header in row 1)
    write_range = f"{TAB}!{JPN_COL}2:{JPN_COL}{len(col_values) + 1}"
    body = {"values": col_values}
    service.spreadsheets().values().update(
        spreadsheetId=MACRO_MONTHLY_SHEET_ID,
        range=write_range,
        valueInputOption="RAW",
        body=body,
    ).execute()
    print(f"Written {len(col_values)} values to {write_range}")
    print("Done.")


if __name__ == "__main__":
    main()
