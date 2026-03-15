#!/usr/bin/env python3
"""
sync_commodity_data.py
MacroSnaps — sync commodity prices from MARKET-STATS sheet into data.json.

Reads the 'Commodities' tab from the MARKET-STATS Google Sheet and writes
three fields per commodity into data.json:
  price  — latest daily close (last row)
  change — % change vs previous day (last two rows)
  spark  — monthly last-close array, last 120 months (10 years)

Usage:
    python3 sync_commodity_data.py              # preview only
    python3 sync_commodity_data.py --apply      # write to data.json

Run from ~/Downloads/macrosnaps/
Runs AFTER fetch_market_data.py (which appends today's row to the sheet).
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

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

DATA_FILE       = Path(__file__).parent / "data.json"
MARKET_SHEET_ID = os.getenv("MARKET_STATS_SHEET_ID")
MARKET_KEY_FILE = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)
TAB_NAME        = "Commodities"
SPARK_MONTHS    = 120    # 10 years of monthly last-close values
TODAY           = date.today().isoformat()

DRY_RUN = "--dry-run" in sys.argv
APPLY   = "--apply"   in sys.argv

# Decimal precision per commodity name (matches backfill / fetch scripts)
COMMODITY_DECIMALS = {
    "WTI Crude":    2,
    "Brent Crude":  2,
    "Natural Gas":  3,
    "Gold":         2,
    "Silver":       3,
    "Copper":       3,
    "Wheat":        2,
    "Corn":         2,
    "Soybeans":     2,
}

# ---------------------------------------------------------------------------
# SHEET ACCESS
# ---------------------------------------------------------------------------

def open_sheet():
    if not MARKET_SHEET_ID:
        sys.exit("ERROR: MARKET_STATS_SHEET_ID not set in .env")
    if not os.path.exists(MARKET_KEY_FILE):
        sys.exit(f"ERROR: service account key not found at {MARKET_KEY_FILE}")

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds  = Credentials.from_service_account_file(MARKET_KEY_FILE, scopes=scopes)
    gc     = gspread.authorize(creds)
    return gc.open_by_key(MARKET_SHEET_ID)


def fetch_commodity_tab(sh):
    """
    Read the Commodities tab and return (header, rows) where:
      header — list of column names e.g. ['Date', 'WTI Crude', ...]
      rows   — list of dicts {col_name: value} sorted by date ascending
    """
    for attempt in range(4):
        try:
            ws = sh.worksheet(TAB_NAME)
            break
        except gspread.WorksheetNotFound:
            sys.exit(f"ERROR: Tab '{TAB_NAME}' not found in MARKET-STATS sheet. Run backfill first.")
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < 3:
                wait = 15 * (2 ** attempt)
                print(f"  [429] Quota hit — waiting {wait}s ...")
                time.sleep(wait)
            else:
                raise

    all_rows = _get_all_values_with_retry(ws)
    if len(all_rows) < 3:
        sys.exit(f"ERROR: '{TAB_NAME}' tab has fewer than 3 rows — run backfill.")

    header   = all_rows[0]
    data_rows = []
    for raw_row in all_rows[1:]:
        if not raw_row or not raw_row[0].strip():
            continue
        row_dict = {}
        for col, cell in zip(header, raw_row):
            row_dict[col] = cell.strip()
        data_rows.append(row_dict)

    # Sort by date ascending (should already be, but be safe)
    def parse_date(r):
        try:
            return datetime.strptime(r.get("Date", ""), "%Y-%m-%d").date()
        except ValueError:
            return date.min

    data_rows.sort(key=parse_date)
    return header, data_rows


def _get_all_values_with_retry(ws, max_retries=4, base_wait=15):
    for attempt in range(max_retries):
        try:
            return ws.get_all_values()
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                print(f"  [429] Quota hit — waiting {wait}s before retry ({attempt+1}/{max_retries-1})...")
                time.sleep(wait)
            else:
                raise

# ---------------------------------------------------------------------------
# DERIVE METRICS
# ---------------------------------------------------------------------------

def safe_float(val):
    """Parse a sheet cell to float, returning None on failure."""
    if val in ("", None, "n/a", "N/A", "-"):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def derive_price(rows, col):
    """Latest non-null close price."""
    for row in reversed(rows):
        val = safe_float(row.get(col))
        if val is not None:
            return val
    return None


def derive_change(rows, col):
    """
    % change between the two most recent non-null close prices.
    Returns float rounded to 1 dp, or None.
    """
    values = [safe_float(r.get(col)) for r in rows]
    non_null = [v for v in values if v is not None]
    if len(non_null) < 2:
        return None
    prev, curr = non_null[-2], non_null[-1]
    if prev == 0:
        return None
    return round((curr / prev - 1) * 100, 1)


def derive_spark(rows, col):
    """
    Monthly last-close array for the last SPARK_MONTHS months.
    For each calendar month, takes the last non-null trading day close.
    Returns a list of floats (or None for months with no data).
    """
    # Group by YYYY-MM
    monthly = defaultdict(list)
    for row in rows:
        date_str = row.get("Date", "")
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        val = safe_float(row.get(col))
        if val is not None:
            monthly[d.strftime("%Y-%m")].append(val)

    # Sort month keys and take last value per month
    sorted_months = sorted(monthly.keys())
    last_closes   = [monthly[m][-1] for m in sorted_months]

    # Return last SPARK_MONTHS values
    return last_closes[-SPARK_MONTHS:]

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    mode_label = "DRY RUN" if DRY_RUN else ("APPLY" if APPLY else "PREVIEW")
    print(f"\n{'='*60}")
    print(f"  sync_commodity_data.py  [{mode_label}]")
    print(f"{'='*60}\n")

    # Load data.json
    if not DATA_FILE.exists():
        sys.exit(f"ERROR: data.json not found at {DATA_FILE}")
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("commodities", {}).get("items", [])
    if not items:
        sys.exit("ERROR: no commodities items found in data.json")

    # Fetch sheet
    print(f"Connecting to MARKET-STATS sheet ...")
    sh = open_sheet()
    print(f"Reading '{TAB_NAME}' tab ...")
    header, rows = fetch_commodity_tab(sh)
    print(f"  {len(rows)} data rows loaded (header: {header})\n")

    # Commodity names from sheet (all columns except Date)
    sheet_cols = [c for c in header if c != "Date"]

    changes = []

    for item in items:
        name = item.get("name")
        if name not in sheet_cols:
            print(f"  WARNING: '{name}' not found as a column in sheet — skipping")
            continue

        decimals = COMMODITY_DECIMALS.get(name, 2)

        new_price  = derive_price(rows, name)
        new_change = derive_change(rows, name)
        new_spark  = derive_spark(rows, name)

        if new_price is None:
            print(f"  {name:<16} FAILED — no price data in sheet")
            continue

        new_price = round(new_price, decimals)

        old_price  = item.get("price")
        old_change = item.get("change")
        old_spark  = item.get("spark", [])

        # Report changes
        price_changed  = old_price  != new_price
        change_changed = old_change != new_change
        spark_changed  = old_spark  != new_spark

        spark_label = f"{len(new_spark)} pts (was {len(old_spark)})" if spark_changed else f"{len(new_spark)} pts unchanged"

        print(f"  {name:<16}  price: {old_price} → {new_price}  "
              f"change: {old_change} → {new_change}  spark: {spark_label}")

        if price_changed or change_changed or spark_changed:
            changes.append((name, new_price, new_change, new_spark))

        if APPLY and not DRY_RUN:
            item["price"]  = new_price
            item["change"] = new_change
            item["spark"]  = new_spark

    # Update asOf date
    new_as_of = datetime.today().strftime("%b %-d, %Y")
    if APPLY and not DRY_RUN:
        data["commodities"]["asOf"] = new_as_of

    print(f"\n{'─'*60}")
    print(f"  {len(changes)} commodity/ies changed out of {len(items)}")

    if not APPLY or DRY_RUN:
        print("\n  Run with --apply to write changes to data.json.")
    else:
        if changes:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n  ✓ data.json updated. Run build.py to rebuild the site.")
        else:
            print("\n  No changes — data.json not touched.")

    print()


if __name__ == "__main__":
    main()
