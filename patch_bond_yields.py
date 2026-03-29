#!/usr/bin/env python3
"""
patch_bond_yields.py
MacroSnaps - patch missing bond yield columns for the Mar 16-27 backfill.

For each affected country, fetches the most recent FRED value prior to the
target date range (carry-forward), then writes into any empty Bond_Yield_10Y,
Bond_Yield_3M, and Yield_Curve cells in the target rows.

Usage:
  python3 patch_bond_yields.py --from 2026-03-16 --to 2026-03-27

Dry run:
  python3 patch_bond_yields.py --from 2026-03-16 --to 2026-03-27 --dry-run
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("ERROR: gspread not installed. Run: pip3 install gspread google-auth")

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

FRED_BASE    = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

MARKET_SHEET_ID = os.environ.get("MARKET_STATS_SHEET_ID", "")
MARKET_KEY_FILE = os.path.expanduser(
    os.environ.get("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)

# Column positions (1-based): Date|Stock_Market_Index|FX_Rate|Bond_Yield_10Y|Bond_Yield_3M|Yield_Curve|Stock_Market_YTD_USD
COL_DATE        = 1
COL_BOND_10Y    = 4
COL_BOND_3M     = 5
COL_YIELD_CURVE = 6

# What each country needs patched: (bond_10y_series, short_rate_series)
# None means that series is not needed / already present
PATCH_CONFIG = {
    "USA": {
        "bond_10y":   None,               # already present from first backfill run
        "short_rate": "TB3MS",            # monthly — was missing
    },
    "CAN": {
        "bond_10y":   "IRLTLT01CAM156N",  # monthly
        "short_rate": "IR3TIB01CAM156N",  # monthly
    },
    "GBR": {
        "bond_10y":   "IRLTLT01GBM156N",
        "short_rate": "IR3TIB01GBM156N",
    },
    "JPN": {
        "bond_10y":   "IRLTLT01JPM156N",
        "short_rate": "IR3TIB01JPM156N",
    },
    "DEU": {
        "bond_10y":   "IRLTLT01DEM156N",
        "short_rate": None,               # ECBDFR already present
    },
    "FRA": {
        "bond_10y":   "IRLTLT01FRM156N",
        "short_rate": None,               # ECBDFR already present
    },
    "ITA": {
        "bond_10y":   "IRLTLT01ITM156N",
        "short_rate": None,               # ECBDFR already present
    },
    "ZAF": {
        "bond_10y":   "IRLTLT01ZAM156N",
        "short_rate": "IRSTCI01ZAM156N",
    },
}

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FRED HELPER
# ---------------------------------------------------------------------------

def fred_latest_prior(series_id, before_date):
    """
    Return the most recent FRED observation on or before before_date.
    Looks back up to 6 months. Returns float or None.
    """
    if not series_id:
        return None
    start = (datetime.strptime(before_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
    params = {
        "series_id":         series_id,
        "api_key":           FRED_API_KEY,
        "file_type":         "json",
        "observation_start": start,
        "observation_end":   before_date,
        "sort_order":        "desc",
        "limit":             5,
    }
    try:
        r = requests.get(f"{FRED_BASE}/series/observations", params=params, timeout=20)
        time.sleep(0.2)
        if r.status_code != 200:
            log.warning(f"  FRED {series_id}: HTTP {r.status_code}")
            return None
        obs = r.json().get("observations", [])
        for o in obs:
            if o["value"] not in (".", "", None):
                log.info(f"  FRED {series_id}: {o['value']} (as of {o['date']})")
                return round(float(o["value"]), 4)
        log.warning(f"  FRED {series_id}: no usable observations")
        return None
    except Exception as exc:
        log.warning(f"  FRED {series_id}: {exc}")
        return None

# ---------------------------------------------------------------------------
# SHEET HELPERS
# ---------------------------------------------------------------------------

def get_target_rows(ws, start_date, end_date):
    """
    Find all rows in the worksheet whose date falls within [start_date, end_date].
    Returns list of (row_index_1based, current_row_values).
    """
    all_values = ws.get_all_values()
    results = []
    for i, row in enumerate(all_values[1:], start=2):  # skip header, 1-based
        if not row or not row[0].strip():
            continue
        d = row[0].strip()
        if start_date <= d <= end_date:
            results.append((i, row))
    return results

def patch_row(ws, row_idx, row_values, bond_10y, short_rate, dry_run):
    """
    Write bond_10y, short_rate, and derived yield_curve into the appropriate
    columns for a single row, but only where the cell is currently empty.
    Uses batch update for efficiency.
    """
    updates = []

    # Pad row_values to at least 6 columns
    vals = list(row_values) + [""] * max(0, 6 - len(row_values))

    current_10y   = vals[COL_BOND_10Y - 1].strip()    # col D
    current_3m    = vals[COL_BOND_3M - 1].strip()     # col E
    current_curve = vals[COL_YIELD_CURVE - 1].strip() # col F

    new_10y   = bond_10y
    new_3m    = short_rate

    # Resolve 10Y: use existing if already present
    effective_10y = float(current_10y) if current_10y else new_10y

    # Resolve 3M: use existing if already present
    effective_3m = float(current_3m) if current_3m else new_3m

    # Compute yield curve if we now have both legs
    new_curve = None
    if effective_10y is not None and effective_3m is not None:
        new_curve = round((effective_10y - effective_3m) * 100)

    date_str = vals[0]

    # Only write cells that are currently empty
    if new_10y is not None and not current_10y:
        updates.append((row_idx, COL_BOND_10Y, new_10y))
    if new_3m is not None and not current_3m:
        updates.append((row_idx, COL_BOND_3M, new_3m))
    if new_curve is not None and not current_curve:
        updates.append((row_idx, COL_YIELD_CURVE, new_curve))

    if not updates:
        log.info(f"    {date_str}: nothing to patch")
        return

    if dry_run:
        for _, col, val in updates:
            col_letter = chr(ord('A') + col - 1)
            log.info(f"    [DRY RUN] {date_str}: {col_letter} = {val}")
        return

    # Batch update all cells for this row
    cell_list = []
    for r, c, v in updates:
        cell = gspread.Cell(r, c, v)
        cell_list.append(cell)
    ws.update_cells(cell_list, value_input_option="USER_ENTERED")
    time.sleep(1.2)  # stay under write quota

    for _, col, val in updates:
        col_letter = chr(ord('A') + col - 1)
        log.info(f"    {date_str}: col {col_letter} = {val} ✓")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Patch missing bond yield columns in MARKET-STATS")
    parser.add_argument("--from", dest="start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to",   dest="end",   required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no sheet writes")
    args = parser.parse_args()

    if not FRED_API_KEY:
        sys.exit("ERROR: FRED_API_KEY not set in .env")
    if not MARKET_SHEET_ID:
        sys.exit("ERROR: MARKET_STATS_SHEET_ID not set in .env")
    if not os.path.exists(MARKET_KEY_FILE):
        sys.exit(f"ERROR: key file not found at {MARKET_KEY_FILE}")

    start   = args.start
    end     = args.end
    dry_run = args.dry_run

    if dry_run:
        log.info("DRY RUN — no changes will be written\n")

    # --- Fetch all FRED values before connecting to sheet ---
    log.info(f"Fetching FRED carry-forward values (lookback before {start}) ...\n")
    fred_values = {}  # country -> {bond_10y: float|None, short_rate: float|None}

    for country, cfg in PATCH_CONFIG.items():
        b10y_series = cfg["bond_10y"]
        sr_series   = cfg["short_rate"]
        log.info(f"[{country}]")
        b10y = fred_latest_prior(b10y_series, start) if b10y_series else None
        sr   = fred_latest_prior(sr_series,   start) if sr_series   else None
        fred_values[country] = {"bond_10y": b10y, "short_rate": sr}
        if not b10y_series:
            log.info(f"  bond_10y: already present in sheet — skipping fetch")
        if not sr_series:
            log.info(f"  short_rate: already present in sheet — skipping fetch")
        log.info("")

    # --- Connect to sheet ---
    log.info("Connecting to MARKET-STATS sheet ...")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(MARKET_KEY_FILE, scopes=scopes)
    gc    = gspread.authorize(creds)
    sh    = gc.open_by_key(MARKET_SHEET_ID)
    log.info("Connected.\n")

    # --- Patch each country tab ---
    for country, vals in fred_values.items():
        bond_10y   = vals["bond_10y"]
        short_rate = vals["short_rate"]

        if bond_10y is None and short_rate is None:
            log.info(f"[{country}] nothing to patch — skipping\n")
            continue

        log.info(f"[{country}] bond_10y={bond_10y}  short_rate={short_rate}")
        try:
            ws = sh.worksheet(country)
        except gspread.WorksheetNotFound:
            log.warning(f"  Tab '{country}' not found — skipping\n")
            continue

        target_rows = get_target_rows(ws, start, end)
        if not target_rows:
            log.warning(f"  No rows found in range {start}–{end}\n")
            continue

        for row_idx, row_values in target_rows:
            patch_row(ws, row_idx, row_values, bond_10y, short_rate, dry_run)

        log.info(f"  Done.\n")
        time.sleep(3)  # pause between countries

    log.info("Patch complete.")


if __name__ == "__main__":
    main()
