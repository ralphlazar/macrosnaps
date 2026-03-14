#!/usr/bin/env python3
"""
update_market_sheet.py
Daily appender for the MARKET-STATS Google Sheet.

Fetches today's values for all 12 countries and appends one row to each
country tab. Skips countries where today's data is not yet available
(markets closed, weekend, public holiday).

Run this as step 2 of the daily ritual, after sheet sync and before
sync_sheet.py --market.

Usage:
    python3 update_market_sheet.py --dry-run      # preview, no write
    python3 update_market_sheet.py                # append to all 12 tabs

Requirements:
    pip3 install yfinance gspread google-auth pandas python-dotenv requests

Environment variables (.env):
    FRED_API_KEY=your_fred_key
    MARKET_STATS_SHEET_ID=your_sheet_id
    MARKET_STATS_KEY_FILE=~/Downloads/macrosnaps/market-stats-key.json  (optional default)
"""

import os, sys, argparse
from datetime import date, timedelta

import pandas as pd
import requests
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Constants (must match populate_market_sheet.py) ───────────────────────────

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]
COLUMNS   = ["Date", "Stock_Market_Index", "FX_Rate", "Bond_Yield_10Y", "Bond_Yield_2Y", "Yield_Curve"]

FRED_API_KEY = os.getenv("FRED_API_KEY")
SHEET_ID     = os.getenv("MARKET_STATS_SHEET_ID")
KEY_FILE     = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)

TODAY     = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

# ── Ticker config (mirrors populate_market_sheet.py) ──────────────────────────

EQUITY_TICKERS = {
    "USA": "^GSPC", "CAN": "^GSPTSE", "GBR": "^FTSE",  "JPN": "^N225",
    "DEU": "^GDAXI","FRA": "^FCHI",   "ITA": "FTSEMIB.MI","CHN": "000001.SS",
    "IND": "^BSESN","ZAF": "^J203.JO","BRA": "^BVSP",  "RUS": "IMOEX.ME",
}

FX_TICKERS = {
    "USA": "DX-Y.NYB", "CAN": "CADUSD=X",  "GBR": "GBPUSD=X","JPN": "USDJPY=X",
    "DEU": "EURUSD=X", "FRA": "EURUSD=X", "ITA": "EURUSD=X","CHN": "USDCNY=X",
    "IND": "USDINR=X", "ZAF": "USDZAR=X", "BRA": "USDBRL=X","RUS": "USDRUB=X",
}

FRED_10Y = {
    "USA": "DGS10",           "CAN": "IRLTLT01CAM156N","GBR": "IRLTLT01GBM156N",
    "JPN": "IRLTLT01JPM156N", "DEU": "IRLTLT01DEM156N","FRA": "IRLTLT01FRM156N",
    "ITA": "IRLTLT01ITM156N", "CHN": None,              "IND": None,
    "ZAF": "IRLTLT01ZAM156N", "BRA": None,              "RUS": None,
}

FRED_2Y = {
    "USA": "DGS2",
    **{c: None for c in ["CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"]},
}

# ── Fetch helpers ──────────────────────────────────────────────────────────────

def fetch_latest_yfinance(ticker: str) -> float | None:
    """Return the most recent closing price for a yfinance ticker."""
    try:
        # Pull last 5 days to handle weekends / holidays
        raw = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
        if raw.empty:
            return None
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        val = float(close.dropna().iloc[-1])
        return round(val, 4)
    except Exception as exc:
        print(f"    [WARN] yfinance {ticker}: {exc}")
        return None

def fetch_latest_fred(series_id: str) -> float | None:
    """Return the most recent observation for a FRED series."""
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id":         series_id,
            "api_key":           FRED_API_KEY,
            "file_type":         "json",
            "sort_order":        "desc",
            "limit":             "5",   # last 5 obs to handle gaps
        }
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        obs = [
            o for o in resp.json().get("observations", [])
            if o["value"] not in (".", "")
        ]
        if not obs:
            return None
        return round(float(obs[0]["value"]), 3)
    except Exception as exc:
        print(f"    [WARN] FRED {series_id}: {exc}")
        return None

# ── Build today's row for one country ─────────────────────────────────────────

def build_row(code: str) -> dict:
    """Fetch latest values for one country. Returns a dict keyed by column name."""
    equity = fetch_latest_yfinance(EQUITY_TICKERS[code])
    fx     = fetch_latest_yfinance(FX_TICKERS[code])

    fred_10y_id = FRED_10Y.get(code)
    y10 = fetch_latest_fred(fred_10y_id) if fred_10y_id else None

    fred_2y_id = FRED_2Y.get(code)
    y2  = fetch_latest_fred(fred_2y_id) if fred_2y_id else None

    yc = None
    if y10 is not None and y2 is not None:
        yc = round((y10 - y2) * 100, 1)

    return {
        "Date":               TODAY,
        "Stock_Market_Index": equity if equity is not None else "",
        "FX_Rate":            fx     if fx     is not None else "",
        "Bond_Yield_10Y":     y10    if y10    is not None else "",
        "Bond_Yield_2Y":      y2     if y2     is not None else "",
        "Yield_Curve":        yc     if yc     is not None else "",
    }

# ── Duplicate check ───────────────────────────────────────────────────────────

def last_date_in_tab(ws) -> str | None:
    """Return the date string in the last data row of a worksheet, or None."""
    try:
        all_vals = ws.col_values(1)  # column A = Date
        # Skip header, find last non-empty
        data_vals = [v for v in all_vals[1:] if v.strip()]
        return data_vals[-1] if data_vals else None
    except Exception:
        return None

# ── Google Sheets helpers ──────────────────────────────────────────────────────

def get_gc():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: service account key not found at {KEY_FILE}")
        sys.exit(1)
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Append today's row to MARKET-STATS")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch and preview without writing to the sheet")
    args = parser.parse_args()

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not set in .env"); sys.exit(1)
    if not SHEET_ID and not args.dry_run:
        print("ERROR: MARKET_STATS_SHEET_ID not set in .env"); sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "LIVE WRITE"
    print(f"\nMARKET-STATS daily update | {mode} | {TODAY}")
    print("=" * 64)

    gc = sh = None
    if not args.dry_run:
        gc = get_gc()
        sh = gc.open_by_key(SHEET_ID)

    results = []
    for code in COUNTRIES:
        print(f"\n  [{code}]")
        row = build_row(code)

        # Check if any data came back at all
        data_cols = [c for c in COLUMNS if c != "Date"]
        has_data  = any(row[c] != "" for c in data_cols)

        if not has_data:
            print(f"    No data available -- skipping")
            results.append((code, "skipped", "--"))
            continue

        # Preview
        print(f"    Equity: {row['Stock_Market_Index']}  "
              f"FX: {row['FX_Rate']}  "
              f"10Y: {row['Bond_Yield_10Y']}  "
              f"2Y: {row['Bond_Yield_2Y']}  "
              f"YC: {row['Yield_Curve']}")

        if args.dry_run:
            results.append((code, "would append", TODAY))
            continue

        # Check for duplicate before appending
        try:
            ws = sh.worksheet(code)
        except gspread.WorksheetNotFound:
            print(f"    [WARN] Tab '{code}' not found -- run populate_market_sheet.py first")
            results.append((code, "error: tab missing", "--"))
            continue

        last_date = last_date_in_tab(ws)
        if last_date == TODAY:
            print(f"    Already has today's row ({TODAY}) -- skipping")
            results.append((code, "skipped: already exists", TODAY))
            continue

        # Append
        row_values = [row[c] for c in COLUMNS]
        ws.append_row(row_values, value_input_option="RAW")
        print(f"    Appended row for {TODAY}")
        results.append((code, "appended", TODAY))

    # Summary
    print("\n" + "=" * 64)
    print("SUMMARY")
    print(f"{'Country':<8}  {'Status':<30}  {'Date'}")
    print("-" * 64)
    for code, status, dt in results:
        print(f"{code:<8}  {status:<30}  {dt}")

    if args.dry_run:
        print("\nDRY RUN complete. No data written.")
    else:
        print("\nUpdate complete.")
        print("Next: python3 sync_sheet.py --market --preview")


if __name__ == "__main__":
    main()
