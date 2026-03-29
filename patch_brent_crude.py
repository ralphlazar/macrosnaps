#!/usr/bin/env python3
"""
patch_brent_crude.py
Fills empty Brent Crude cells in the Commodities tab using FRED DCOILBRENTEU.

DCOILBRENTEU is a daily series (weekdays only) going back to 1987-05-20.
It is carry-forward filled for weekends/holidays to match the sheet's daily rows.

Usage:
  python3 patch_brent_crude.py --dry-run   # preview only
  python3 patch_brent_crude.py             # write to sheet
"""

import os
import sys
import time
import requests
from datetime import date, datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("ERROR: gspread not installed. Run: pip3 install gspread google-auth")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

DRY_RUN      = "--dry-run" in sys.argv
RATE_LIMIT_S = 1.2

SHEET_ID  = os.environ.get("MARKET_STATS_SHEET_ID", "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI")
KEY_FILE  = os.path.expanduser(
    os.environ.get("MARKET_STATS_KEY_FILE", "~/macrosnaps/market-stats-key.json")
)
TAB_NAME     = "Commodities"
BRENT_COL    = "Brent Crude"
FRED_SERIES  = "DCOILBRENTEU"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ---------------------------------------------------------------------------
# FRED FETCH
# ---------------------------------------------------------------------------

def fetch_fred_brent():
    """
    Fetch all daily Brent Crude observations from FRED DCOILBRENTEU.
    Returns dict of {date_str: price_float}, missing values excluded.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":  FRED_SERIES,
        "api_key":    FRED_API_KEY,
        "file_type":  "json",
        "sort_order": "asc",
        "limit":      100000,
    }
    print(f"Fetching FRED {FRED_SERIES} ...")
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        sys.exit(f"FRED error: HTTP {r.status_code}")
    obs = r.json().get("observations", [])
    result = {}
    for o in obs:
        if o["value"] not in (".", "", None):
            result[o["date"]] = round(float(o["value"]), 2)
    print(f"  {len(result)} observations fetched")
    return result


def carry_forward(prices_by_date, all_dates):
    """
    For dates without a FRED observation (weekends, holidays),
    carry forward the last known price.
    """
    filled = {}
    last = None
    for d in sorted(all_dates):
        if d in prices_by_date:
            last = prices_by_date[d]
        if last is not None:
            filled[d] = last
    return filled


# ---------------------------------------------------------------------------
# SHEET HELPERS
# ---------------------------------------------------------------------------

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if DRY_RUN:
        print("DRY RUN — no changes will be written\n")

    if not FRED_API_KEY:
        sys.exit("ERROR: FRED_API_KEY not set in .env")

    # Fetch FRED data
    fred_prices = fetch_fred_brent()

    # Connect to sheet
    print("\nConnecting to MARKET-STATS sheet ...")
    sh  = get_sheet()
    ws  = sh.worksheet(TAB_NAME)
    print("Connected.")

    rows   = ws.get_all_values()
    header = rows[0]
    data   = rows[1:]

    # Find Brent Crude column index (1-based for gspread)
    if BRENT_COL not in header:
        sys.exit(f"ERROR: '{BRENT_COL}' column not found in sheet header")
    brent_col_idx = header.index(BRENT_COL)  # 0-based
    brent_col_1based = brent_col_idx + 1      # 1-based for gspread

    print(f"'{BRENT_COL}' is column {brent_col_1based} ('{header[brent_col_idx]}')")

    # Build carry-forward prices for all dates in the sheet
    all_sheet_dates = [row[0].strip() for row in data if row and row[0].strip()]
    cf_prices = carry_forward(fred_prices, all_sheet_dates)

    # Find empty cells
    cells_to_write = []
    for i, row in enumerate(data):
        if not row or not row[0].strip():
            continue
        date_str = row[0].strip()
        current  = row[brent_col_idx].strip() if brent_col_idx < len(row) else ""
        if current == "" and date_str in cf_prices:
            sheet_row = i + 2  # 1-based (header=1)
            cells_to_write.append((sheet_row, brent_col_1based, str(cf_prices[date_str])))

    print(f"\nEmpty Brent Crude cells to fill: {len(cells_to_write)}")

    if not cells_to_write:
        print("Nothing to do.")
        return

    if DRY_RUN:
        print("\nSample of cells that would be written:")
        for r, c, v in cells_to_write[:10]:
            print(f"  Row {r}: {v}")
        if len(cells_to_write) > 10:
            print(f"  ... and {len(cells_to_write) - 10} more")
        return

    print(f"\nWriting {len(cells_to_write)} cells (rate-limited) ...")
    for i, (r, c, v) in enumerate(cells_to_write, 1):
        ws.update_cell(r, c, v)
        time.sleep(RATE_LIMIT_S)
        if i % 50 == 0 or i == len(cells_to_write):
            print(f"  {i}/{len(cells_to_write)} written ...")

    print("\nDone.")


if __name__ == "__main__":
    main()
