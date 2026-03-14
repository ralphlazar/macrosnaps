#!/usr/bin/env python3
"""
populate_market_sheet.py
One-time historical backfill for the MARKET-STATS Google Sheet.

Pulls daily data from START_DATE to today for all 12 countries.
Writes 12 tabs named by 3-letter country code (USA, CAN, GBR, etc.).

Columns per tab:
    Date | Stock_Market_Index | FX_Rate | Bond_Yield_10Y | Bond_Yield_2Y | Yield_Curve

Sources:
    Stock index levels  -- Yahoo Finance (yfinance)
    FX rates            -- Yahoo Finance (yfinance)
    10Y bond yields     -- FRED API (daily for USA, monthly forward-filled for others)
    2Y bond yields      -- FRED API (daily for USA, monthly for others where available)

Yield_Curve = (Bond_Yield_10Y - Bond_Yield_2Y) * 100, stored in basis points.
Cells are left blank (not zero) where data is unavailable.

Usage:
    python3 populate_market_sheet.py --dry-run          # fetch + preview, no write
    python3 populate_market_sheet.py --dry-run --country USA  # single country
    python3 populate_market_sheet.py                    # write all 12 tabs

Requirements:
    pip3 install yfinance gspread google-auth pandas python-dotenv requests

One-time Google Cloud setup (do this before running):
    1. Go to https://console.cloud.google.com and create a project (or use an existing one)
    2. Enable the Google Sheets API for that project
    3. Go to IAM > Service Accounts > Create Service Account
    4. Name it something like "macrosnaps-sheets"
    5. Skip the optional role/permission steps at creation time
    6. Once created, click the account > Keys > Add Key > JSON
    7. Save the downloaded file as:
           ~/Downloads/macrosnaps/market-stats-key.json
    8. In your MARKET-STATS Google Sheet, click Share and add the service account
       email address (looks like macrosnaps-sheets@your-project.iam.gserviceaccount.com)
       with Editor access
    9. Add the sheet ID to .env (the long string in the sheet URL)

Environment variables (.env):
    FRED_API_KEY=your_fred_key
    MARKET_STATS_SHEET_ID=your_sheet_id
    MARKET_STATS_KEY_FILE=~/Downloads/macrosnaps/market-stats-key.json  (optional, this is the default)
"""

import os, sys, time, argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Constants ──────────────────────────────────────────────────────────────────

START_DATE   = "2000-01-01"
COUNTRIES    = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]
COLUMNS      = ["Date", "Stock_Market_Index", "FX_Rate", "Bond_Yield_10Y", "Bond_Yield_2Y", "Yield_Curve"]

FRED_API_KEY = os.getenv("FRED_API_KEY")
SHEET_ID     = os.getenv("MARKET_STATS_SHEET_ID")
KEY_FILE     = os.path.expanduser(
    os.getenv("MARKET_STATS_KEY_FILE", "~/Downloads/macrosnaps/market-stats-key.json")
)

# ── Ticker / series config ─────────────────────────────────────────────────────

# Yahoo Finance equity index tickers (closing price = raw index level)
EQUITY_TICKERS = {
    "USA": "^GSPC",       # S&P 500
    "CAN": "^GSPTSE",     # S&P/TSX Composite
    "GBR": "^FTSE",       # FTSE 100
    "JPN": "^N225",       # Nikkei 225
    "DEU": "^GDAXI",      # DAX
    "FRA": "^FCHI",       # CAC 40
    "ITA": "FTSEMIB.MI",  # FTSE MIB
    "CHN": "000001.SS",   # Shanghai Composite
    "IND": "^BSESN",      # BSE Sensex
    "ZAF": "^J203.JO",    # JSE All Share
    "BRA": "^BVSP",       # Bovespa
    "RUS": "IMOEX.ME",    # MOEX (data truncates post-2022 sanctions)
}

# Yahoo Finance FX tickers.
# Convention matches data.json card values:
#   USD pairs (CAN, CHN, IND, ZAF, BRA, RUS, JPN) -- units of foreign currency per 1 USD
#   Non-USD pairs (GBR, DEU, FRA, ITA) -- USD per 1 unit of foreign currency
#   USA -- DXY dollar index level
FX_TICKERS = {
    "USA": "DX-Y.NYB",  # DXY dollar index (~99)
    "CAN": "CADUSD=X",  # CAD per USD (~1.37) -- matches card convention
    "GBR": "GBPUSD=X",  # USD per GBP (~1.34)
    "JPN": "USDJPY=X",  # JPY per USD (~158.6)
    "DEU": "EURUSD=X",  # USD per EUR (~1.1589)
    "FRA": "EURUSD=X",  # same pair as DEU
    "ITA": "EURUSD=X",  # same pair as DEU
    "CHN": "USDCNY=X",  # CNY per USD (~6.86)
    "IND": "USDINR=X",  # INR per USD (~92.04)
    "ZAF": "USDZAR=X",  # ZAR per USD (~16.38)
    "BRA": "USDBRL=X",  # BRL per USD (~5.16)
    "RUS": "USDRUB=X",  # RUB per USD (~79.1, may be missing or unofficial post-sanctions)
}

# FRED series for 10Y government bond yield (percent).
# DGS10 is daily. IRLTLT01XXM156N series are monthly (OECD) -- forward-filled to daily.
FRED_10Y = {
    "USA": "DGS10",           # daily
    "CAN": "IRLTLT01CAM156N", # monthly
    "GBR": "IRLTLT01GBM156N", # monthly
    "JPN": "IRLTLT01JPM156N", # monthly
    "DEU": "IRLTLT01DEM156N", # monthly
    "FRA": "IRLTLT01FRM156N", # monthly
    "ITA": "IRLTLT01ITM156N", # monthly
    "CHN": None,               # not available on FRED
    "IND": None,               # not available on FRED
    "ZAF": "IRLTLT01ZAM156N", # monthly
    "BRA": None,               # not available on FRED
    "RUS": None,               # unavailable post-sanctions
}

# FRED series for 2Y government bond yield (percent).
# DGS2 is daily. IRLTST01XXM156N series are monthly (OECD) -- forward-filled to daily.
# Non-US coverage is limited. Gaps are left blank, not zero.
FRED_2Y = {
    "USA": "DGS2",  # daily, reliable
    "CAN": None,    # no reliable FRED 2Y series for non-US countries
    "GBR": None,
    "JPN": None,
    "DEU": None,
    "FRA": None,
    "ITA": None,
    "CHN": None,
    "IND": None,
    "ZAF": None,
    "BRA": None,
    "RUS": None,
}

# ── FRED fetch ─────────────────────────────────────────────────────────────────

def fetch_fred(series_id: str) -> pd.Series:
    """Fetch one FRED series from START_DATE to today. Returns a float Series indexed by date."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":        series_id,
        "api_key":          FRED_API_KEY,
        "file_type":        "json",
        "observation_start": START_DATE,
        "observation_end":  date.today().isoformat(),
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    if not obs:
        return pd.Series(dtype=float, name=series_id)
    data = {
        o["date"]: float(o["value"]) if o["value"] not in (".", "") else float("nan")
        for o in obs
    }
    s = pd.Series(data, name=series_id)
    s.index = pd.to_datetime(s.index)
    return s

# ── yfinance fetch ─────────────────────────────────────────────────────────────

def fetch_yfinance(ticker: str) -> pd.Series:
    """Download closing prices for one ticker from START_DATE to today."""
    try:
        raw = yf.download(ticker, start=START_DATE, progress=False, auto_adjust=True)
        if raw.empty:
            return pd.Series(dtype=float, name=ticker)
        close = raw["Close"]
        # yfinance >= 0.2 with a single ticker returns a plain Series or a single-column DataFrame
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close.index = pd.to_datetime(close.index).tz_localize(None)
        close.name = ticker
        return close.dropna()
    except Exception as exc:
        print(f"[WARN] yfinance {ticker}: {exc}")
        return pd.Series(dtype=float, name=ticker)

# ── Build daily DataFrame for one country ─────────────────────────────────────

def build_country_frame(code: str, verbose: bool = True) -> pd.DataFrame:
    """
    Fetch all 5 series for one country. Return a daily DataFrame with business-day index
    and columns [Stock_Market_Index, FX_Rate, Bond_Yield_10Y, Bond_Yield_2Y, Yield_Curve].
    Blanks where data is unavailable (empty string, not NaN, for sheet compatibility).
    """

    def _log(label, s):
        if verbose:
            if s.empty:
                print(f"    {label}: no data")
            else:
                non_null = s.dropna()
                print(f"    {label}: {len(non_null)} non-null rows  "
                      f"(latest {non_null.index[-1].date()} = {non_null.iloc[-1]:.4f})")

    print(f"\n  [{code}]")

    equity = fetch_yfinance(EQUITY_TICKERS[code])
    _log("Equity index", equity)

    fx = fetch_yfinance(FX_TICKERS[code])
    _log("FX rate", fx)

    fred_10y_id = FRED_10Y.get(code)
    if fred_10y_id:
        y10 = fetch_fred(fred_10y_id)
        _log(f"10Y ({fred_10y_id})", y10)
    else:
        y10 = pd.Series(dtype=float)
        print(f"    10Y: no series configured")

    fred_2y_id = FRED_2Y.get(code)
    if fred_2y_id:
        try:
            y2 = fetch_fred(fred_2y_id)
            _log(f"2Y  ({fred_2y_id})", y2)
        except Exception as exc:
            y2 = pd.Series(dtype=float)
            print(f"    2Y  ({fred_2y_id}): fetch failed -- {exc}")
    else:
        y2 = pd.Series(dtype=float)
        print(f"    2Y: no series configured")

    # Daily business-day spine
    spine = pd.date_range(start=START_DATE, end=date.today(), freq="B")
    df = pd.DataFrame(index=spine)
    df.index.name = "Date"

    # Align to spine. Monthly FRED series forward-fill to fill weekdays.
    def _align(s):
        if s.empty:
            return pd.Series(float("nan"), index=spine)
        return s.reindex(spine, method="ffill")

    df["Stock_Market_Index"] = _align(equity).round(2)
    # Do not forward-fill equity past the last real observation (e.g. RUS post-sanctions)
    if not equity.empty:
        last_real = equity.dropna().index.max()
        df.loc[df.index > last_real, "Stock_Market_Index"] = float("nan")

    df["FX_Rate"]            = _align(fx).round(4)
    df["Bond_Yield_10Y"]     = _align(y10).round(3)
    df["Bond_Yield_2Y"]      = _align(y2).round(3)

    both_yields = (not y10.empty) and (not y2.empty)
    if both_yields:
        df["Yield_Curve"] = ((df["Bond_Yield_10Y"] - df["Bond_Yield_2Y"]) * 100).round(1)
    else:
        df["Yield_Curve"] = float("nan")

    # Replace NaN with "" so the sheet cell is blank, not the string "nan"
    df = df.where(pd.notnull(df), "")

    coverage = {
        "Equity":  equity.dropna().__len__() > 0,
        "FX":      fx.dropna().__len__() > 0,
        "10Y":     not y10.empty,
        "2Y":      not y2.empty,
        "YC":      both_yields,
    }
    print(f"    Coverage: " + " | ".join(f"{k} {'ok' if v else '--'}" for k, v in coverage.items()))
    print(f"    Rows in frame: {len(df)}")

    return df

# ── Google Sheets helpers ──────────────────────────────────────────────────────

def get_gc():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: service account key not found at {KEY_FILE}")
        print("  Follow the setup instructions at the top of this file.")
        sys.exit(1)
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds)

def write_tab(gc, sheet_id: str, code: str, df: pd.DataFrame):
    """Write (or overwrite) one country tab in the sheet."""
    sh = gc.open_by_key(sheet_id)

    try:
        ws = sh.worksheet(code)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=code, rows=str(len(df) + 5), cols=str(len(COLUMNS)))

    # Build 2D list: header row + data rows
    header = [COLUMNS]
    data_rows = [
        [idx.strftime("%Y-%m-%d")] + list(row)
        for idx, row in zip(df.index, df.itertuples(index=False, name=None))
    ]
    all_rows = header + data_rows

    ws.clear()
    # Single update call -- gspread handles chunking internally
    ws.update("A1", all_rows, value_input_option="RAW")
    print(f"    Wrote {len(data_rows)} rows to tab [{code}]")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Populate MARKET-STATS Google Sheet")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Fetch and preview data without writing to the sheet")
    parser.add_argument("--country",  metavar="CODE",
                        help="Run for a single country only (e.g. --country USA)")
    args = parser.parse_args()

    # Validate environment
    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not set in .env"); sys.exit(1)
    if not SHEET_ID and not args.dry_run:
        print("ERROR: MARKET_STATS_SHEET_ID not set in .env"); sys.exit(1)

    countries = [args.country.upper()] if args.country else COUNTRIES
    mode = "DRY RUN (no write)" if args.dry_run else "LIVE WRITE"

    print(f"\nMARKET-STATS populate | {mode}")
    print(f"Countries: {', '.join(countries)}")
    print(f"Date range: {START_DATE} to {date.today()}")
    print("=" * 64)

    gc = None
    if not args.dry_run:
        print("Connecting to Google Sheets...")
        gc = get_gc()
        print("Connected.\n")

    results = {}
    for code in countries:
        try:
            df = build_country_frame(code, verbose=True)
            results[code] = df

            if not args.dry_run:
                write_tab(gc, SHEET_ID, code, df)
                time.sleep(2)  # polite pause between tabs to avoid Sheets API rate limit

        except Exception as exc:
            print(f"  [{code}] ERROR: {exc}")
            results[code] = None

    # Summary
    print("\n" + "=" * 64)
    print("SUMMARY")
    print(f"{'Country':<8}  {'Equity':>8}  {'FX':>6}  {'10Y':>6}  {'2Y':>6}  {'YC':>6}  {'Rows':>6}")
    print("-" * 64)
    for code in countries:
        df = results.get(code)
        if df is None:
            print(f"{code:<8}  ERROR (see above)")
            continue
        def pct(col):
            non_blank = (df[col] != "").sum()
            return f"{int(non_blank / len(df) * 100)}%" if len(df) else "--"
        print(
            f"{code:<8}  {pct('Stock_Market_Index'):>8}  {pct('FX_Rate'):>6}  "
            f"{pct('Bond_Yield_10Y'):>6}  {pct('Bond_Yield_2Y'):>6}  {pct('Yield_Curve'):>6}  "
            f"{len(df):>6}"
        )

    if args.dry_run:
        print("\nDRY RUN complete. No data written.")
        print("Run without --dry-run to write to the sheet.")
    else:
        print("\nPopulate complete.")
        print("Next step: spot-check a few values in the sheet, then run update_market_sheet.py daily.")


if __name__ == "__main__":
    main()
