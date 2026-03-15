#!/usr/bin/env python3
"""
backfill_commodity_data.py
MacroSnaps — one-time backfill of commodity price history.

Creates a new 'Commodities' tab in MARKET-STATS and populates it with
daily close prices for all 9 commodities from Jan 2000 → yesterday.

Columns: Date | WTI Crude | Brent Crude | Natural Gas | Gold | Silver |
         Copper | Wheat | Corn | Soybeans

Run ONCE from ~/Downloads/macrosnaps/:
    python3 backfill_commodity_data.py

Requires:
    pip3 install yfinance gspread google-auth python-dotenv pandas
    .env must contain MARKET_STATS_SHEET_ID and optionally MARKET_STATS_KEY_FILE
"""

import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("ERROR: pandas not installed. Run: pip3 install pandas")

try:
    import yfinance as yf
except ImportError:
    sys.exit("ERROR: yfinance not installed. Run: pip3 install yfinance")

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("ERROR: gspread / google-auth not installed. Run: pip3 install gspread google-auth")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

MARKET_SHEET_ID = os.getenv("MARKET_STATS_SHEET_ID")
MARKET_KEY_FILE = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)
TAB_NAME   = "Commodities"
START_DATE = "2000-01-01"
END_DATE   = (date.today() - timedelta(days=1)).isoformat()   # yesterday

# Ordered list of (sheet column header, yfinance ticker, decimal places)
COMMODITY_COLS = [
    ("WTI Crude",    "CL=F",  2),
    ("Brent Crude",  "BZ=F",  2),
    ("Natural Gas",  "NG=F",  3),
    ("Gold",         "GC=F",  2),
    ("Silver",       "SI=F",  3),
    ("Copper",       "HG=F",  3),
    ("Wheat",        "ZW=F",  2),
    ("Corn",         "ZC=F",  2),
    ("Soybeans",     "ZS=F",  2),
]

BATCH_SIZE = 500   # rows per gspread update call

# ---------------------------------------------------------------------------
# FETCH HISTORY
# ---------------------------------------------------------------------------

def fetch_all_history():
    """
    Pull daily Close prices for all 9 commodities from yfinance.
    Returns a pandas DataFrame with Date index and one column per commodity.
    Forward-fills gaps (futures rollover / missing days) per column.
    """
    print(f"\nFetching daily history {START_DATE} → {END_DATE} ...\n")
    frames = {}

    for name, ticker, decimals in COMMODITY_COLS:
        print(f"  {name:<16} ({ticker}) ...", end=" ", flush=True)
        try:
            raw = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                auto_adjust=True,
                progress=False,
            )
            if raw.empty:
                print("EMPTY — no data returned")
                frames[name] = pd.Series(dtype=float, name=name)
                continue

            closes = raw["Close"].squeeze()
            closes = closes.round(decimals)
            frames[name] = closes
            print(f"OK  ({len(closes)} rows, {closes.index[0].date()} → {closes.index[-1].date()})")

        except Exception as exc:
            print(f"FAILED: {exc}")
            frames[name] = pd.Series(dtype=float, name=name)

        time.sleep(0.2)   # be polite to Yahoo

    # Combine into single DataFrame aligned on date
    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    # Forward-fill within each column (handles futures rollover gaps, weekends skipped by yf)
    df.ffill(inplace=True)

    print(f"\n  Combined DataFrame: {len(df)} rows × {len(df.columns)} columns")
    print(f"  Date range: {df.index[0].date()} → {df.index[-1].date()}")
    non_null = df.notna().sum()
    for col in df.columns:
        print(f"    {col:<16}: {non_null[col]} non-null values")

    return df

# ---------------------------------------------------------------------------
# WRITE TO SHEET
# ---------------------------------------------------------------------------

def open_sheet():
    """Authenticate and return the MARKET-STATS spreadsheet object."""
    if not MARKET_SHEET_ID:
        sys.exit("ERROR: MARKET_STATS_SHEET_ID not set in .env")
    if not os.path.exists(MARKET_KEY_FILE):
        sys.exit(f"ERROR: service account key not found at {MARKET_KEY_FILE}")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(MARKET_KEY_FILE, scopes=scopes)
    gc    = gspread.authorize(creds)
    return gc.open_by_key(MARKET_SHEET_ID)


def get_or_create_tab(sh):
    """Return the Commodities worksheet, creating it if absent."""
    try:
        ws = sh.worksheet(TAB_NAME)
        print(f"  Tab '{TAB_NAME}' already exists.")
        response = input("  Overwrite it? (yes/no): ").strip().lower()
        if response != "yes":
            sys.exit("Aborted — tab not overwritten.")
        ws.clear()
        print("  Tab cleared.")
        return ws
    except gspread.WorksheetNotFound:
        print(f"  Creating new tab '{TAB_NAME}' ...")
        ws = sh.add_worksheet(title=TAB_NAME, rows=7500, cols=10)
        print(f"  Tab created.")
        return ws


def df_to_rows(df):
    """Convert DataFrame to list of lists suitable for gspread update."""
    header = ["Date"] + list(df.columns)
    rows = [header]
    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d")
        values   = [
            "" if pd.isna(v) else v
            for v in row
        ]
        rows.append([date_str] + values)
    return rows


def write_in_batches(ws, all_rows):
    """Write rows to sheet in batches to avoid payload limits."""
    total = len(all_rows)
    print(f"\n  Writing {total} rows to sheet in batches of {BATCH_SIZE} ...")

    # First row is header, write all at once from A1
    for batch_start in range(0, total, BATCH_SIZE):
        batch = all_rows[batch_start : batch_start + BATCH_SIZE]
        start_row = batch_start + 1   # 1-indexed
        end_row   = start_row + len(batch) - 1
        range_str = f"A{start_row}"

        for attempt in range(4):
            try:
                ws.update(range_str, batch, value_input_option="USER_ENTERED")
                print(f"    Rows {start_row}–{end_row} ... OK")
                break
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 429 and attempt < 3:
                    wait = 15 * (2 ** attempt)
                    print(f"    [429] Quota hit — waiting {wait}s ...")
                    time.sleep(wait)
                else:
                    raise

        time.sleep(1.5)   # stay well under quota between batches

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  MacroSnaps — Commodity Backfill")
    print(f"  Target: {START_DATE} → {END_DATE}")
    print("=" * 60)

    # 1. Fetch from yfinance
    df = fetch_all_history()

    if df.empty:
        sys.exit("ERROR: No data fetched — aborting.")

    # 2. Convert to rows
    all_rows = df_to_rows(df)
    print(f"\n  Total rows to write: {len(all_rows)} (incl. header)")

    # 3. Open sheet
    print("\nOpening MARKET-STATS sheet ...")
    sh = open_sheet()
    ws = get_or_create_tab(sh)

    # 4. Write
    write_in_batches(ws, all_rows)

    print(f"\n  ✓ Backfill complete — {len(all_rows) - 1} data rows written to '{TAB_NAME}' tab.")
    print("  Next: run fetch_market_data.py to append today's row, then sync_commodity_data.py.\n")


if __name__ == "__main__":
    main()
