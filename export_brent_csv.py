#!/usr/bin/env python3
"""
export_brent_csv.py
Downloads FRED DCOILBRENTEU and exports a CSV of Brent Crude prices
for all dates currently blank in the Commodities sheet.

The CSV can be copy-pasted into the sheet manually.

Usage:
  python3 export_brent_csv.py
  Output: brent_backfill.csv
"""

import os
import sys
import csv
import time
import requests

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("ERROR: pip3 install gspread google-auth")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SHEET_ID     = os.environ.get("MARKET_STATS_SHEET_ID", "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI")
KEY_FILE     = os.path.expanduser(os.environ.get("MARKET_STATS_KEY_FILE", ""))
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
FRED_SERIES  = "DCOILBRENTEU"
OUTPUT_FILE  = "brent_backfill.csv"


def fetch_fred():
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
    print(f"  {len(result)} observations")
    return result


def carry_forward(prices, dates):
    filled = {}
    last = None
    for d in sorted(dates):
        if d in prices:
            last = prices[d]
        if last is not None:
            filled[d] = last
    return filled


def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
              "https://www.googleapis.com/auth/drive.readonly"]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds).open_by_key(SHEET_ID)


def main():
    if not FRED_API_KEY:
        sys.exit("ERROR: FRED_API_KEY not set in .env")

    fred = fetch_fred()

    print("Connecting to sheet ...")
    ws   = get_sheet().worksheet("Commodities")
    rows = ws.get_all_values()
    header = rows[0]
    data   = rows[1:]

    brent_idx = header.index("Brent Crude")

    # Find rows where Brent is blank
    missing_dates = []
    for row in data:
        if not row or not row[0].strip():
            continue
        d   = row[0].strip()
        val = row[brent_idx].strip() if brent_idx < len(row) else ""
        if val == "":
            missing_dates.append(d)

    print(f"Blank Brent rows: {len(missing_dates)}")

    cf = carry_forward(fred, missing_dates)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Brent Crude"])
        for d in sorted(missing_dates):
            price = cf.get(d, "")
            writer.writerow([d, price])

    print(f"Written: {OUTPUT_FILE}  ({len(missing_dates)} rows)")
    print("\nTo apply: sort the CSV by date, then paste the Brent Crude column")
    print("into column C of the Commodities tab for the matching dates.")


if __name__ == "__main__":
    main()
