#!/usr/bin/env python3
"""
backfill_rus_index.py
One-off script to fill blank Stock_Market_Index cells in the RUS tab
of the MARKET-STATS Google Sheet using MOEX daily candle data.

Usage:
    python3 backfill_rus_index.py --dry-run   # preview only
    python3 backfill_rus_index.py             # write to sheet

Environment variables (.env):
    MARKET_STATS_SHEET_ID
    MARKET_STATS_KEY_FILE  (optional, default ~/Downloads/macrosnaps/market-stats-key.json)
"""

import os, sys, time, argparse
from datetime import date, datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("MARKET_STATS_SHEET_ID")
KEY_FILE  = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)

# MOEX daily candle interval code
MOEX_INTERVAL = 24   # 1 day
PAGE_SIZE      = 500

# ── Fetch all IMOEX daily candles from MOEX ───────────────────────────────────

def fetch_moex_daily(from_date="2000-01-01") -> dict:
    """
    Fetch all daily IMOEX candles from MOEX ISS API.
    Returns { "YYYY-MM-DD": close_price } for every trading day available.
    Handles pagination automatically.
    """
    prices = {}
    start  = 0
    till   = date.today().isoformat()

    print(f"Fetching MOEX daily candles from {from_date} to {till}...")

    while True:
        url = (
            f"https://iss.moex.com/iss/engines/stock/markets/index/securities/"
            f"IMOEX/candles.json"
            f"?from={from_date}&till={till}&interval={MOEX_INTERVAL}&start={start}"
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data    = resp.json()
            candles = data.get("candles", {})
            columns = candles.get("columns", [])
            rows    = candles.get("data",    [])
        except Exception as exc:
            print(f"  [ERROR] MOEX fetch at start={start}: {exc}")
            break

        if not rows:
            break  # No more pages

        try:
            close_idx = columns.index("close")
            begin_idx = columns.index("begin")
        except ValueError as e:
            print(f"  [ERROR] Unexpected column layout: {e}")
            break

        for row in rows:
            raw_date  = row[begin_idx]          # e.g. "2024-03-15 00:00:00"
            raw_close = row[close_idx]
            if raw_close is None:
                continue
            day_str = raw_date[:10]             # trim to YYYY-MM-DD
            prices[day_str] = round(float(raw_close), 4)

        print(f"  Fetched {len(rows)} candles (start={start}), total so far: {len(prices)}")

        if len(rows) < PAGE_SIZE:
            break   # Last page
        start += PAGE_SIZE
        time.sleep(0.3)  # Be polite to MOEX API

    print(f"Total MOEX daily prices fetched: {len(prices)}")
    return prices

# ── Google Sheets helpers ─────────────────────────────────────────────────────

def get_ws():
    if not SHEET_ID:
        print("ERROR: MARKET_STATS_SHEET_ID not set in .env"); sys.exit(1)
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: key not found at {KEY_FILE}"); sys.exit(1)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    gc     = gspread.authorize(creds)
    sh     = gc.open_by_key(SHEET_ID)
    return sh.worksheet("RUS")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "LIVE WRITE"
    print(f"\nRUS Stock_Market_Index backfill | {mode}")
    print("=" * 60)

    # 1. Fetch MOEX prices
    moex_prices = fetch_moex_daily()
    if not moex_prices:
        print("No MOEX data fetched. Aborting."); sys.exit(1)

    # 2. Open sheet
    print("\nOpening RUS tab...")
    ws = get_ws()

    # 3. Read all values once
    print("Reading sheet...")
    all_rows = ws.get_all_values()
    if not all_rows:
        print("Sheet is empty. Aborting."); sys.exit(1)

    header = all_rows[0]
    try:
        date_col  = header.index("Date")
        index_col = header.index("Stock_Market_Index")
    except ValueError as e:
        print(f"ERROR: column not found: {e}"); sys.exit(1)

    # 4. Build batch update: only rows where Stock_Market_Index is blank
    #    and MOEX has a price for that date.
    updates = []   # list of { "range": "B123", "values": [[val]] }
    filled  = 0
    missing = 0    # dates in sheet with no MOEX data

    for row_idx, row in enumerate(all_rows[1:], start=2):  # row 2 = first data row
        date_str  = row[date_col].strip()  if date_col  < len(row) else ""
        index_val = row[index_col].strip() if index_col < len(row) else ""

        if not date_str:
            continue
        if index_val:
            continue  # already populated, skip

        if date_str in moex_prices:
            col_letter = chr(ord("A") + index_col)   # e.g. "B"
            cell_ref   = f"{col_letter}{row_idx}"
            updates.append({
                "range":  cell_ref,
                "values": [[moex_prices[date_str]]]
            })
            filled += 1
        else:
            missing += 1

    print(f"\nBlank rows found:        {filled + missing}")
    print(f"MOEX prices available:   {filled}")
    print(f"No MOEX data (stays blank): {missing}")

    if not updates:
        print("\nNothing to update.")
        return

    if args.dry_run:
        print(f"\nDRY RUN: would write {filled} cells.")
        print("Sample (first 5):")
        for u in updates[:5]:
            print(f"  {u['range']} = {u['values'][0][0]}")
        return

    # 5. Batch update in chunks of 1000 to avoid quota limits
    CHUNK = 1000
    total_chunks = (len(updates) + CHUNK - 1) // CHUNK
    print(f"\nWriting {filled} cells in {total_chunks} batch(es)...")

    for i in range(0, len(updates), CHUNK):
        chunk = updates[i:i + CHUNK]
        ws.batch_update(chunk, value_input_option="RAW")
        print(f"  Chunk {i // CHUNK + 1}/{total_chunks} written ({len(chunk)} cells)")
        if i + CHUNK < len(updates):
            time.sleep(1.5)  # Respect Sheets API quota

    print(f"\nDone. {filled} cells written to RUS tab.")

if __name__ == "__main__":
    main()
