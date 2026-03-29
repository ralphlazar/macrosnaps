#!/usr/bin/env python3
"""
backfill_commodity_data.py
Backfills the Commodities tab in MARKET-STATS with daily price data.

Two operations:
  1. Insert missing rows BEFORE the current earliest date (default: 2000-01-01
     up to the day before the sheet's first row).
  2. Fill empty cells in EXISTING rows (e.g. Brent Crude gaps before ~2007).

Both operations are idempotent — existing data is never overwritten.

Usage:
  python3 backfill_commodity_data.py --dry-run   # preview only
  python3 backfill_commodity_data.py             # write to sheet

Requires:
  MARKET_STATS_SHEET_ID and MARKET_STATS_KEY_FILE in .env
  pip3 install yfinance gspread google-auth python-dotenv
"""

import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    sys.exit("ERROR: yfinance not installed. Run: pip3 install yfinance")

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
BACKFILL_FROM = "2000-01-01"
RATE_LIMIT_S  = 1.2   # seconds between cell writes to avoid Sheets quota

SHEET_ID  = os.environ.get("MARKET_STATS_SHEET_ID", "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI")
KEY_FILE  = os.path.expanduser(
    os.environ.get("MARKET_STATS_KEY_FILE", "~/macrosnaps/market-stats-key.json")
)
TAB_NAME  = "Commodities"

# Column order must match sheet header exactly
COL_ORDER = [
    "WTI Crude", "Brent Crude", "Natural Gas",
    "Gold", "Silver", "Copper",
    "Wheat", "Corn", "Soybeans",
]

# Yahoo Finance tickers
TICKERS = {
    "WTI Crude":   "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Gold":        "GC=F",
    "Silver":      "SI=F",
    "Copper":      "HG=F",
    "Wheat":       "ZW=F",
    "Corn":        "ZC=F",
    "Soybeans":    "ZS=F",
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def fetch_yahoo(ticker, start, end):
    """
    Fetch daily close prices for a Yahoo Finance ticker.
    Returns dict of {date_str: price_float}.
    """
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(start=start, end=end)
        if hist.empty:
            return {}
        result = {}
        for idx, row in hist.iterrows():
            d = idx.date().isoformat()
            result[d] = round(float(row["Close"]), 2)
        return result
    except Exception as e:
        print(f"  Yahoo {ticker}: {e}")
        return {}


def col_letter(col_idx):
    """Convert 0-based column index to sheet letter (A, B, ... Z, AA...)."""
    result = ""
    col_idx += 1
    while col_idx:
        col_idx, rem = divmod(col_idx - 1, 26)
        result = chr(65 + rem) + result
    return result


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if DRY_RUN:
        print("DRY RUN — no changes will be written\n")

    # ── Connect to sheet ──────────────────────────────────────────────────
    print("Connecting to MARKET-STATS sheet ...")
    sh = get_sheet()
    ws = sh.worksheet(TAB_NAME)
    print("Connected.\n")

    rows = ws.get_all_values()
    header = rows[0]
    data_rows = rows[1:]

    # Build index: date_str -> row_number (1-based, header=1, first data=2)
    existing_dates = {}
    for i, row in enumerate(data_rows):
        if row and row[0]:
            existing_dates[row[0].strip()] = i + 2  # 1-based sheet row

    first_date = min(existing_dates.keys()) if existing_dates else date.today().isoformat()
    print(f"Sheet has {len(data_rows)} data rows.")
    print(f"Earliest date: {first_date}")
    print(f"Backfill range for new rows: {BACKFILL_FROM} → {first_date}\n")

    # ── Fetch Yahoo data ──────────────────────────────────────────────────
    print("Fetching Yahoo Finance data ...")
    all_prices = {}  # {commodity_name: {date_str: price}}
    for name in COL_ORDER:
        ticker = TICKERS[name]
        prices = fetch_yahoo(ticker, BACKFILL_FROM, date.today().isoformat())
        all_prices[name] = prices
        print(f"  {name:<16} {ticker:<10} {len(prices)} pts")
    print()

    # ── Part 1: Insert missing rows before first_date ─────────────────────
    # Collect all trading dates in the range that aren't in the sheet
    all_new_dates = set()
    for name, prices in all_prices.items():
        for d in prices:
            if d < first_date and d not in existing_dates:
                all_new_dates.add(d)

    new_dates_sorted = sorted(all_new_dates)
    print(f"New rows to insert before {first_date}: {len(new_dates_sorted)}")

    if new_dates_sorted and not DRY_RUN:
        # Build rows to insert
        new_rows = []
        for d in new_dates_sorted:
            row = [d]
            for name in COL_ORDER:
                val = all_prices[name].get(d, "")
                row.append(str(val) if val != "" else "")
            new_rows.append(row)

        # Insert after header (row 1) — gspread insert_rows inserts BEFORE the given index
        # We want to insert at row 2 (just after header), in ascending date order
        print(f"Inserting {len(new_rows)} rows after header ...")
        ws.insert_rows(new_rows, row=2, value_input_option="USER_ENTERED")
        print("  Done.\n")
        time.sleep(3)  # let Sheets settle before re-reading

        # Re-read sheet after insert
        rows = ws.get_all_values()
        data_rows = rows[1:]
        existing_dates = {}
        for i, row in enumerate(data_rows):
            if row and row[0]:
                existing_dates[row[0].strip()] = i + 2
    elif new_dates_sorted and DRY_RUN:
        print(f"  [DRY RUN] Would insert {len(new_dates_sorted)} rows.")
        for d in new_dates_sorted[:5]:
            print(f"    {d}: ", end="")
            vals = [str(all_prices[name].get(d, "")) for name in COL_ORDER]
            print(", ".join(vals))
        if len(new_dates_sorted) > 5:
            print(f"    ... and {len(new_dates_sorted) - 5} more")
        print()

    # ── Part 2: Fill empty cells in existing rows ─────────────────────────
    print("Scanning for empty cells in existing rows ...")

    # Re-read fresh after any inserts
    rows = ws.get_all_values()
    data_rows = rows[1:]
    existing_dates = {}
    for i, row in enumerate(data_rows):
        if row and row[0]:
            existing_dates[row[0].strip()] = i + 2

    # Pad all rows to header length
    n_cols = len(header)

    cells_to_write = []  # list of (row_1based, col_1based, value)

    for date_str, sheet_row in sorted(existing_dates.items()):
        row_idx = sheet_row - 2  # 0-based into data_rows
        row = data_rows[row_idx] if row_idx < len(data_rows) else []
        # Pad row to full width
        row = row + [""] * (n_cols - len(row))

        for col_idx, name in enumerate(COL_ORDER):
            sheet_col = col_idx + 2  # 1-based (col A=Date, col B=first commodity)
            current_val = row[sheet_col - 1].strip() if sheet_col - 1 < len(row) else ""
            if current_val == "":
                new_val = all_prices[name].get(date_str, "")
                if new_val != "":
                    cells_to_write.append((sheet_row, sheet_col, str(new_val)))

    print(f"  {len(cells_to_write)} empty cells to fill.\n")

    if cells_to_write and not DRY_RUN:
        print(f"Writing {len(cells_to_write)} cells ...")
        for i, (r, c, v) in enumerate(cells_to_write, 1):
            letter = col_letter(c - 1)
            ws.update_cell(r, c, v)
            time.sleep(RATE_LIMIT_S)
            if i % 50 == 0 or i == len(cells_to_write):
                print(f"  {i}/{len(cells_to_write)} written ...")
        print("Done.\n")
    elif cells_to_write and DRY_RUN:
        print(f"[DRY RUN] Would fill {len(cells_to_write)} cells.")
        for r, c, v in cells_to_write[:10]:
            letter = col_letter(c - 1)
            print(f"  Row {r}, col {letter} = {v}")
        if len(cells_to_write) > 10:
            print(f"  ... and {len(cells_to_write) - 10} more")
        print()
    else:
        print("Nothing to fill — all cells already populated.\n")

    print("Backfill complete.")


if __name__ == "__main__":
    main()
