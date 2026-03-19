#!/usr/bin/env python3
"""
sync_market_sheet.py
Reads the latest values from the MARKET-STATS Google Sheet and writes
them into data.json for the 4 market metrics per country.

Replaces fetch_market_data.py for these 4 series:
    - Stock Market YTD  (computed from index levels: latest vs first trading day of year)
    - FX Rate           (latest non-blank FX_Rate value)
    - 10Y Bond Yield    (latest non-blank Bond_Yield_10Y value)
    - Yield Curve       (latest non-blank Yield_Curve value, in bps)

Usage:
    python3 sync_market_sheet.py --preview    # show changes, do not write
    python3 sync_market_sheet.py --apply      # write changes to data.json

Requirements:
    pip3 install gspread google-auth pandas python-dotenv

Environment variables (.env):
    MARKET_STATS_SHEET_ID=your_sheet_id
    MARKET_STATS_KEY_FILE=~/Downloads/macrosnaps/market-stats-key.json  (optional default)
"""

import os, sys, json, argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

SHEET_ID = os.getenv("MARKET_STATS_SHEET_ID")
KEY_FILE = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)
DATA_JSON = Path(__file__).parent / "data.json"

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

# Maps country code to the metric key name used in data.json
# These must match the keys in data.json countries[code].metrics.market
METRIC_KEYS = {
    "stock_ytd":  "Stock Market YTD",
    "fx":         "FX",
    "yield_10y":  "10Y Bond Yield",
    "yield_curve":"Yield Curve",
}

TODAY = date.today().isoformat()

# ── Google Sheets ─────────────────────────────────────────────────────────────

def get_gc():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: service account key not found at {KEY_FILE}")
        sys.exit(1)
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds)

def read_tab(sh, code: str) -> pd.DataFrame | None:
    """Read all rows from one country tab. Returns a DataFrame or None if tab missing."""
    try:
        ws = sh.worksheet(code)
        rows = ws.get_all_values()
        if len(rows) < 2:
            return None
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        for col in ["Stock_Market_Index", "FX_Rate", "Bond_Yield_10Y", "Bond_Yield_3M", "Yield_Curve", "Stock_Market_YTD_USD"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].replace("", float("nan")), errors="coerce")
        return df.dropna(subset=["Date"])
    except gspread.WorksheetNotFound:
        print(f"  [{code}] WARNING: tab not found in sheet")
        return None

# ── Compute values from DataFrame ─────────────────────────────────────────────

def compute_ytd(df: pd.DataFrame) -> tuple[float | None, str | None]:
    """
    Compute Stock Market YTD % from index levels.
    Returns (ytd_pct rounded to 2dp, date_of_latest_value) or (None, None).
    """
    current_year = date.today().year
    this_year = df[df["Date"].dt.year == current_year].dropna(subset=["Stock_Market_Index"])
    if this_year.empty:
        return None, None

    first_row = this_year.iloc[0]
    latest_row = this_year.iloc[-1]

    base  = first_row["Stock_Market_Index"]
    latest = latest_row["Stock_Market_Index"]
    latest_date = latest_row["Date"].date().isoformat()

    if base == 0 or pd.isna(base) or pd.isna(latest):
        return None, None

    ytd = round((latest - base) / base * 100, 2)
    return ytd, latest_date

def latest_value(df: pd.DataFrame, col: str) -> tuple[float | None, str | None]:
    """Return (latest non-null value, date) for a given column."""
    sub = df.dropna(subset=[col])
    if sub.empty:
        return None, None
    row = sub.iloc[-1]
    return row[col], row["Date"].date().isoformat()

# ── Find metric key in data.json ──────────────────────────────────────────────

def find_market_metric(country_data: dict, label: str) -> str | None:
    """
    Search country_data["metrics"]["market"] for a key whose value dict
    contains a label matching the given string (case-insensitive partial match).
    Returns the metric key string or None.
    """
    market = country_data.get("metrics", {}).get("market", {})
    for key in market:
        if label.lower() in key.lower():
            return key
    return None

def find_fx_key(country_data: dict) -> str | None:
    """FX metric key varies by country (e.g. GBP/USD, USD/JPY). Find it by exclusion."""
    market = country_data.get("metrics", {}).get("market", {})
    known = {"stock market ytd", "stock market ytd (usd)", "10y bond yield", "yield curve"}
    for key in market:
        if key.lower() not in known:
            return key
    return None


def find_or_create_ytd_usd_key(country_data: dict) -> str:
    """
    Return the key for 'Stock Market YTD (USD)' in market metrics.
    Creates it by cloning 'Stock Market YTD' if absent.
    Also backfills any missing fields (e.g. story) if the key exists
    but was created bare by a previous run.
    """
    import copy
    market = country_data.get("metrics", {}).get("market", {})
    target = "Stock Market YTD (USD)"
    source = market.get("Stock Market YTD", {})
    if target not in market:
        new_entry = copy.deepcopy(source)
        new_entry["value"] = None
        new_entry["last_updated"] = None
        market[target] = new_entry
    else:
        # Backfill any fields present in source but missing from existing entry
        existing = market[target]
        for field, val in source.items():
            if field not in existing:
                existing[field] = copy.deepcopy(val)
    return target

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sync MARKET-STATS sheet to data.json")
    parser.add_argument("--preview", action="store_true",
                        help="Show what would change without writing")
    parser.add_argument("--apply",   action="store_true",
                        help="Write changes to data.json")
    parser.add_argument("--country", metavar="CODE",
                        help="Run for a single country only (e.g. --country USA)")
    args = parser.parse_args()

    if not args.preview and not args.apply:
        print("Specify --preview or --apply")
        sys.exit(1)

    if not SHEET_ID:
        print("ERROR: MARKET_STATS_SHEET_ID not set in .env"); sys.exit(1)

    mode = "PREVIEW" if args.preview else "APPLY"
    print(f"\nsync_market_sheet.py | {mode} | {TODAY}")
    print("=" * 64)

    # Load data.json
    if not DATA_JSON.exists():
        print(f"ERROR: data.json not found at {DATA_JSON}"); sys.exit(1)
    with open(DATA_JSON) as f:
        data = json.load(f)

    # Connect to sheet
    print("Connecting to MARKET-STATS sheet...")
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    print("Connected.\n")

    countries = [args.country.upper()] if args.country else COUNTRIES
    changes = []  # list of (code, metric_key, old_val, new_val, as_of)

    for code in countries:
        print(f"  [{code}]")

        df = read_tab(sh, code)
        if df is None or df.empty:
            print(f"    No data -- skipping")
            continue

        country_data = data.get("countries", {}).get(code)
        if not country_data:
            print(f"    Not found in data.json -- skipping")
            continue

        # ── Stock Market YTD ──────────────────────────────────────────────────
        ytd, ytd_date = compute_ytd(df)
        # Use exact match to avoid picking up 'Stock Market YTD (USD)'
        market = country_data.get("metrics", {}).get("market", {})
        stock_key = "Stock Market YTD" if "Stock Market YTD" in market else None
        if stock_key and ytd is not None:
            old = country_data["metrics"]["market"][stock_key].get("value")
            changes.append((code, stock_key, old, ytd, ytd_date))
            print(f"    Stock Market YTD: {old} -> {ytd}%  (as of {ytd_date})")
        elif stock_key:
            print(f"    Stock Market YTD: no data in sheet")

        # ── FX Rate ───────────────────────────────────────────────────────────
        fx_val, fx_date = latest_value(df, "FX_Rate")
        fx_key = find_fx_key(country_data)
        if fx_key and fx_val is not None:
            old = country_data["metrics"]["market"][fx_key].get("value")
            changes.append((code, fx_key, old, round(fx_val, 4), fx_date))
            print(f"    FX ({fx_key}): {old} -> {round(fx_val, 4)}  (as of {fx_date})")
        elif fx_key:
            print(f"    FX: no data in sheet")

        # ── 10Y Bond Yield ────────────────────────────────────────────────────
        y10_val, y10_date = latest_value(df, "Bond_Yield_10Y")
        y10_key = find_market_metric(country_data, "10y bond")
        if y10_key and y10_val is not None:
            old = country_data["metrics"]["market"][y10_key].get("value")
            changes.append((code, y10_key, old, round(y10_val, 3), y10_date))
            print(f"    10Y Bond Yield: {old} -> {round(y10_val, 3)}%  (as of {y10_date})")
        elif y10_key:
            print(f"    10Y Bond Yield: no data in sheet")

        # ── Yield Curve ───────────────────────────────────────────────────────
        yc_val, yc_date = latest_value(df, "Yield_Curve")
        yc_key = find_market_metric(country_data, "yield curve")
        if yc_key and yc_val is not None:
            old = country_data["metrics"]["market"][yc_key].get("value")
            changes.append((code, yc_key, old, round(yc_val, 1), yc_date))
            print(f"    Yield Curve: {old} -> {round(yc_val, 1)}bps  (as of {yc_date})")
        elif yc_key:
            print(f"    Yield Curve: no data in sheet")

        # ── Stock Market YTD (USD) ────────────────────────────────────────────
        if "Stock_Market_YTD_USD" not in df.columns:
            print(f"    Stock Market YTD (USD): column not in sheet yet -- skipping")
        else:
            ytd_usd_val, ytd_usd_date = latest_value(df, "Stock_Market_YTD_USD")
            ytd_usd_key = find_or_create_ytd_usd_key(country_data)
            if ytd_usd_val is not None:
                old = country_data["metrics"]["market"][ytd_usd_key].get("value")
                changes.append((code, ytd_usd_key, old, round(ytd_usd_val, 2), ytd_usd_date))
                print(f"    Stock Market YTD (USD): {old} -> {round(ytd_usd_val, 2)}%  (as of {ytd_usd_date})")
            else:
                print(f"    Stock Market YTD (USD): no data in sheet yet")

    # Summary table
    print("\n" + "=" * 64)
    print(f"{'Country':<6}  {'Metric':<20}  {'Old':>10}  {'New':>10}  {'As of'}")
    print("-" * 64)
    for code, key, old, new, as_of in changes:
        print(f"{code:<6}  {key:<20}  {str(old):>10}  {str(new):>10}  {as_of}")

    if args.preview:
        print(f"\n{len(changes)} change(s) would be written. Run with --apply to write.")
        return

    # Apply changes to data.json
    print(f"\nApplying {len(changes)} change(s) to data.json...")
    for code, key, old, new, as_of in changes:
        data["countries"][code]["metrics"]["market"][key]["value"]        = new
        data["countries"][code]["metrics"]["market"][key]["last_updated"] = as_of

    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("data.json updated.")
    print("\nNext steps:")
    print("  python3 update_stories.py")
    print("  python3 build.py")


if __name__ == "__main__":
    main()
