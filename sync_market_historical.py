#!/usr/bin/env python3
"""
sync_market_historical.py
Rebuilds all market metric spark arrays in data.json from Jan 2000 to the present.

Architecture rule
-----------------
This script reads exclusively from the MARKET-STATS Google Sheet.
It never contacts yfinance, FRED, or any external API.
External sources are the responsibility of fetch_market_data.py only.

Rule
----
Every spark array must cover Jan 2000 → last available data point.
"Last available" must be within the last 3 months of today's date.
If a source stops updating, the chart shows a visible trailing gap rather than
silently hiding stale frozen data. This is intentional: gaps are diagnostic.

Metrics rebuilt (per country tab in MARKET-STATS)
--------------------------------------------------
  Stock Market   — column Stock_Market_Index, monthly last-close
  FX Rate        — column FX_Rate, monthly last-close (already display format)
  10Y Bond Yield — column Bond_Yield_10Y, monthly last-close
  Yield Curve    — column Yield_Curve, monthly last-close (already in bps)

Commodities
-----------
NOT touched here. sync_commodity_data.py owns commodity sparks.

Run
---
  python3 sync_market_historical.py             # preview (no writes)
  python3 sync_market_historical.py --apply     # write to data.json
"""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("ERROR: gspread / google-auth not installed. "
             "pip3 install gspread google-auth --break-system-packages")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

APPLY       = "--apply" in sys.argv
DATA_FILE   = Path(__file__).parent / "data.json"
CREDS_FILE  = Path(__file__).parent / "market-stats-key.json"
SHEET_ID    = os.environ.get(
    "MARKET_STATS_SHEET_ID",
    "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI"
)
START_DATE  = "2000-01-01"
STALE_MONTHS = 3   # warn if last data point is older than this

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA",
             "CHN", "IND", "ZAF", "BRA", "RUS"]

# Exact label each FX spark is stored under in _frozen_historical.
# Must match what the shell reads.
FX_LABELS = {
    "USA": "USD/DXY",  "CAN": "CAD/USD",  "GBR": "GBP/USD",
    "JPN": "USD/JPY",  "DEU": "EUR/USD",  "FRA": "EUR/USD",
    "ITA": "EUR/USD",  "CHN": "USD/CNY",  "IND": "USD/INR",
    "ZAF": "USD/ZAR",  "BRA": "USD/BRL",  "RUS": "USD/RUB",
}

# Rounding per metric
STOCK_DECIMALS    = 2
FX_DECIMALS       = 2
BOND_DECIMALS     = 3
YC_DECIMALS       = 1


# ---------------------------------------------------------------------------
# GSPREAD AUTH
# ---------------------------------------------------------------------------

def get_sheet():
    """Open MARKET-STATS workbook via service account credentials."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    if not CREDS_FILE.exists():
        sys.exit(f"ERROR: credentials file not found: {CREDS_FILE}")
    creds  = Credentials.from_service_account_file(str(CREDS_FILE), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


# ---------------------------------------------------------------------------
# SHEET READER
# ---------------------------------------------------------------------------

def read_country_tab(sheet, code):
    """
    Read all rows from a country tab in MARKET-STATS.
    Returns a pd.DataFrame indexed by Date (DatetimeIndex), or None on failure.

    Expected columns: Date, Stock_Market_Index, FX_Rate,
                      Bond_Yield_10Y, Bond_Yield_3M, Yield_Curve,
                      Stock_Market_YTD_USD
    """
    try:
        ws   = sheet.worksheet(code)
        rows = ws.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        log.warning(f"  [{code}] tab not found in MARKET-STATS — skipping")
        return None
    except Exception as e:
        log.warning(f"  [{code}] error reading tab: {e} — skipping")
        return None

    if not rows or len(rows) < 2:
        log.warning(f"  [{code}] tab is empty — skipping")
        return None

    # Strip trailing empty column names; truncate each data row to match.
    # get_all_values() pads all rows to the width of the widest row, which
    # can introduce empty-string duplicate column names and break pd.to_numeric.
    headers = [h for h in rows[0] if h]
    data    = [r[:len(headers)] for r in rows[1:]]

    df = pd.DataFrame(data, columns=headers)

    if "Date" not in df.columns:
        log.warning(f"  [{code}] no Date column found — skipping")
        return None

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.set_index("Date")
    df = df.sort_index()

    # Convert all value columns to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Trim to START_DATE
    df = df[df.index >= START_DATE]

    return df


# ---------------------------------------------------------------------------
# STALENESS CHECK
# ---------------------------------------------------------------------------

def stale_check(arr, label):
    """
    Warn if the array is empty or if the last data point is older than
    STALE_MONTHS from today. A point-count check is not used because some
    sources have shorter history (e.g. ZAF stocks from ~2012).
    """
    if not arr:
        log.warning(f"    ⚠  {label}: EMPTY — no data")
        return

    # arr is a list of floats — we check its length against a date-based
    # estimate of how many months of data we'd expect if current.
    # We can't recover the last date from the list alone, so we use length
    # as a proxy: if len < (months since 2000 - STALE_MONTHS - 24) it's
    # likely stale. 24 is a generous buffer for sources with shorter history.
    today           = date.today()
    months_since_2000 = (today.year - 2000) * 12 + today.month
    stale_threshold   = months_since_2000 - STALE_MONTHS - 24

    if len(arr) < stale_threshold:
        log.warning(
            f"    ⚠  {label}: {len(arr)} pts — may be stale or short history"
        )
    else:
        log.info(f"    ✓  {label}: {len(arr)} pts")


def stale_check_with_date(last_date, label, n_pts):
    """
    Check staleness using the actual last date from the DataFrame.
    More accurate than the length-based check.
    """
    today        = date.today()
    months_old   = (today.year - last_date.year) * 12 + (today.month - last_date.month)

    if n_pts == 0:
        log.warning(f"    ⚠  {label}: EMPTY — no data")
    elif months_old > STALE_MONTHS:
        log.warning(
            f"    ⚠  {label}: {n_pts} pts, last={last_date.strftime('%Y-%m')} "
            f"({months_old} months ago — may be stale)"
        )
    else:
        log.info(
            f"    ✓  {label}: {n_pts} pts, last={last_date.strftime('%Y-%m')}"
        )


# ---------------------------------------------------------------------------
# SPARK BUILDERS
# ---------------------------------------------------------------------------

def monthly_last(df, col, decimals):
    """
    Resample a daily column to month-end last close.
    Returns (list_of_floats, last_date_or_None).
    Ignores NaN rows. Returns ([], None) if column missing or all NaN.
    """
    if col not in df.columns:
        return [], None

    series  = df[col].dropna()
    if series.empty:
        return [], None

    monthly = series.resample("ME").last().dropna()
    if monthly.empty:
        return [], None

    last_date = monthly.index[-1].date()
    result    = [round(float(v), decimals) for v in monthly]
    return result, last_date


def build_stock_spark(df):
    return monthly_last(df, "Stock_Market_Index", STOCK_DECIMALS)


def build_fx_spark(df):
    # FX_Rate is already in display format — no inversion needed
    return monthly_last(df, "FX_Rate", FX_DECIMALS)


def build_bond_spark(df):
    return monthly_last(df, "Bond_Yield_10Y", BOND_DECIMALS)


def build_yc_spark(df):
    # Yield_Curve already in bps in the sheet
    return monthly_last(df, "Yield_Curve", YC_DECIMALS)


# ---------------------------------------------------------------------------
# WRITE HELPER
# ---------------------------------------------------------------------------

def set_spark(frozen_historical, label, spark):
    """
    Write spark into _frozen_historical as {"type": "line", "v": [...]}.
    This is the structure the shell reads via historicalData[code][label].v.
    """
    if label not in frozen_historical:
        frozen_historical[label] = {}
    frozen_historical[label]["type"] = "line"
    frozen_historical[label]["v"]    = spark


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    mode = "[APPLY]" if APPLY else "[PREVIEW]"
    log.info(f"{mode} sync_market_historical.py")
    log.info(f"Source: MARKET-STATS sheet ({SHEET_ID})")
    log.info(f"Start date: {START_DATE}  |  Stale threshold: {STALE_MONTHS} months")
    log.info("")

    if not DATA_FILE.exists():
        sys.exit(f"ERROR: data.json not found at {DATA_FILE}")

    log.info("Connecting to MARKET-STATS sheet ...")
    sheet = get_sheet()
    log.info("Connected.\n")

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    countries = data["countries"]
    writes    = 0

    for code in COUNTRIES:
        if code not in countries:
            log.warning(f"\n[{code}] not found in data.json — skipping")
            continue

        log.info(f"{'='*56}")
        log.info(f"  {code}")
        log.info(f"{'='*56}")

        fh = countries[code].get("_frozen_historical")
        if fh is None:
            log.warning(f"  No _frozen_historical key found — skipping")
            continue

        df = read_country_tab(sheet, code)
        if df is None:
            continue

        # ── Stock Market ──────────────────────────────────────────────────
        stock_spark, stock_last = build_stock_spark(df)
        if stock_last:
            stale_check_with_date(stock_last, "Stock Market", len(stock_spark))
        else:
            log.warning("    ⚠  Stock Market: EMPTY")
        if APPLY:
            set_spark(fh, "Stock Market YTD", stock_spark)
            writes += 1

        # ── FX Rate ───────────────────────────────────────────────────────
        fx_label          = FX_LABELS.get(code)
        fx_spark, fx_last = build_fx_spark(df)
        if fx_last:
            stale_check_with_date(fx_last, f"FX ({fx_label})", len(fx_spark))
        else:
            log.warning(f"    ⚠  FX ({fx_label}): EMPTY")
        if APPLY and fx_label:
            set_spark(fh, fx_label, fx_spark)
            writes += 1

        # ── 10Y Bond Yield ────────────────────────────────────────────────
        bond_spark, bond_last = build_bond_spark(df)
        if bond_last:
            stale_check_with_date(bond_last, "10Y Bond Yield", len(bond_spark))
        else:
            log.warning("    ⚠  10Y Bond Yield: EMPTY (expected for CHN/BRA/RUS)")
        if APPLY:
            set_spark(fh, "10Y Bond Yield", bond_spark)
            writes += 1

        # ── Yield Curve ───────────────────────────────────────────────────
        yc_spark, yc_last = build_yc_spark(df)
        if yc_last:
            stale_check_with_date(yc_last, "Yield Curve", len(yc_spark))
        else:
            log.warning("    ⚠  Yield Curve: EMPTY (expected for CHN/BRA/RUS)")
        if APPLY:
            set_spark(fh, "Yield Curve", yc_spark)
            writes += 1

        log.info("")

    if not APPLY:
        log.info("Preview complete. Run with --apply to write to data.json.")
        return

    log.info(f"Writing {DATA_FILE} ...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(
        f"Done. {writes} spark arrays written across {len(COUNTRIES)} countries."
    )
    log.info("")
    log.info("Next: python3 build.py --apply")


if __name__ == "__main__":
    main()
