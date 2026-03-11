#!/usr/bin/env python3
"""
fetch_market_data.py
====================
Fetches live market and commodity data and writes it into data.json.

Usage:
    python3 fetch_market_data.py           # preview mode (no writes)
    python3 fetch_market_data.py --apply   # apply all changes

Data sources:
    - Yahoo Finance: stocks, FX, commodities
    - FRED: USA 10Y and 2Y bond yields (requires FRED_API_KEY in .env)
    - Stooq.com: international 10Y and 2Y bond yields (no key needed)

Rules:
    - Never touches macro fields (GDP, CPI, Unemployment, Budget Deficit,
      Current Account, Policy Rate). The Google Sheet owns those via sync_sheet.py.
    - Skips the 4 data-void metrics (Equity Vol, Corp Spread, Sov CDS, FX Vol).
    - Russia: all fields skipped gracefully. Existing values are preserved.
    - If any ticker or series returns no data, logs a warning and leaves the
      existing value untouched. Never crashes the whole run.
    - Preview mode shows a diff of every field that would change before any write.
    - Run sync_sheet.py --apply before this script so sheet values land first.
"""

import json
import sys
import argparse
import os
import time
from datetime import date
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip3 install yfinance")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip3 install requests")
    sys.exit(1)

# Load .env if present (for FRED_API_KEY).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).parent / "data.json"
TODAY = date.today().isoformat()

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

MACRO_FIELDS_LOCKED = {
    "GDP Growth",
    "Inflation (CPI)",
    "Unemployment",
    "Budget Deficit",
    "Current Account",
    "Policy Rate",
}

DATA_VOID_METRICS = {
    "Equity Vol",
    "Corp Spread",
    "Sov CDS",
    "FX Vol",
}

# Countries where all market data is kept manual. Existing values preserved.
MANUAL_COUNTRIES = {"RUS"}

# ---------------------------------------------------------------------------
# Ticker / series maps
# ---------------------------------------------------------------------------

STOCK_TICKERS = {
    "USA": "^GSPC",
    "CAN": "^GSPTSE",
    "GBR": "^FTSE",
    "JPN": "^N225",
    "DEU": "^GDAXI",
    "FRA": "^FCHI",
    "ITA": "FTSEMIB.MI",
    "CHN": "000001.SS",
    "IND": "^NSEI",
    "ZAF": "^J203.JO",
    "BRA": "^BVSP",
}

FX_CONFIG = {
    "USA": {"field": "USD/DXY",  "ticker": "DX-Y.NYB"},
    "CAN": {"field": "CAD/USD",  "ticker": "CADUSD=X"},
    "GBR": {"field": "GBP/USD",  "ticker": "GBPUSD=X"},
    "JPN": {"field": "USD/JPY",  "ticker": "USDJPY=X"},
    "DEU": {"field": "EUR/USD",  "ticker": "EURUSD=X"},
    "FRA": {"field": "EUR/USD",  "ticker": "EURUSD=X"},
    "ITA": {"field": "EUR/USD",  "ticker": "EURUSD=X"},
    "CHN": {"field": "USD/CNY",  "ticker": "USDCNY=X"},
    "IND": {"field": "USD/INR",  "ticker": "USDINR=X"},
    "ZAF": {"field": "USD/ZAR",  "ticker": "USDZAR=X"},
    "BRA": {"field": "USD/BRL",  "ticker": "USDBRL=X"},
    "RUS": {"field": "USD/RUB",  "ticker": "USDRUB=X"},
}

COMMODITY_TICKERS = {
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

# FRED series IDs for USA government bond yields.
FRED_SERIES = {
    "10Y": "DGS10",
    "2Y":  "DGS2",
}

# Stooq tickers for international government bond yields.
# Yields are returned as plain percentage points (e.g. 4.23 = 4.23%).
STOOQ_10Y = {
    "CAN": "10cab.b",
    "GBR": "10ukb.b",
    "JPN": "10jpb.b",
    "DEU": "10deb.b",
    "FRA": "10frb.b",
    "ITA": "10itb.b",
    "CHN": "10cnb.b",
    "IND": "10inb.b",
    "ZAF": "10zab.b",
    "BRA": "10brb.b",
}

STOOQ_2Y = {
    "CAN": "2cab.b",
    "GBR": "2ukb.b",
    "JPN": "2jpb.b",
    "DEU": "2deb.b",
    "FRA": "2frb.b",
    "ITA": "2itb.b",
    "CHN": "2cnb.b",
    "IND": "2inb.b",
    "ZAF": "2zab.b",
    "BRA": "2brb.b",
}

# ---------------------------------------------------------------------------
# Fetch helpers: Yahoo Finance
# ---------------------------------------------------------------------------

def yf_latest_close(ticker_symbol):
    """Returns the latest closing price, or None on failure."""
    try:
        hist = yf.Ticker(ticker_symbol).history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


def yf_ytd(ticker_symbol):
    """
    Returns (latest_close, ytd_pct) or (None, None).
    YTD = (latest close / first close of year - 1) * 100.
    """
    try:
        hist = yf.Ticker(ticker_symbol).history(period="ytd")
        if hist.empty or len(hist) < 2:
            return None, None
        first = float(hist["Close"].iloc[0])
        last  = float(hist["Close"].iloc[-1])
        if first == 0:
            return None, None
        return last, (last / first - 1) * 100
    except Exception:
        return None, None


def yf_daily_change(ticker_symbol):
    """
    Returns (latest_close, daily_pct) or (None, None).
    Daily = (today close / yesterday close - 1) * 100.
    """
    try:
        hist = yf.Ticker(ticker_symbol).history(period="5d")
        if hist.empty or len(hist) < 2:
            return None, None
        prev = float(hist["Close"].iloc[-2])
        last = float(hist["Close"].iloc[-1])
        if prev == 0:
            return None, None
        return last, (last / prev - 1) * 100
    except Exception:
        return None, None

# ---------------------------------------------------------------------------
# Fetch helpers: FRED
# ---------------------------------------------------------------------------

def fred_latest(series_id):
    """
    Returns the latest daily value for a FRED series, or None on failure.
    Requires FRED_API_KEY in environment or .env file.
    """
    if not FRED_API_KEY:
        return None
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key":   FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 5,
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        for ob in r.json().get("observations", []):
            val = ob.get("value", ".")
            if val != ".":
                return float(val)
        return None
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Fetch helpers: Stooq
# ---------------------------------------------------------------------------

def stooq_latest(ticker):
    """
    Returns the latest daily close for a Stooq bond ticker, or None on failure.
    Stooq returns plain CSV: Date,Open,High,Low,Close,Volume
    Values are in percentage points (e.g. 4.23 = 4.23%).
    """
    try:
        url = f"https://stooq.com/q/d/l/?s={ticker}&i=d"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return None
        last = lines[-1].split(",")
        if len(last) < 5:
            return None
        val = last[4]  # Close column
        if not val or val == "N/D":
            return None
        return float(val)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------

def fmt_ytd(pct):
    if pct is None:
        return None
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def fmt_yield(val):
    """
    All sources return yields as plain percentage points (e.g. 4.23).
    Normalise any accidental decimal form (< 1.0) just in case.
    """
    if val is None:
        return None
    if val < 1:
        val = val * 100
    return f"{val:.2f}%"


def fmt_yield_curve(y10, y2):
    """
    Both inputs in percentage points. Returns spread in basis points.
    """
    if y10 is None or y2 is None:
        return None
    bp   = round((y10 - y2) * 100)
    sign = "+" if bp >= 0 else ""
    return f"{sign}{bp}bp"


def fmt_fx(val, field_name):
    if val is None:
        return None
    if "DXY" in field_name:
        return f"{val:.2f}"
    if any(x in field_name for x in ["JPY", "INR", "ZAR", "RUB", "BRL", "CNY"]):
        return f"{val:.2f}"
    return f"{val:.4f}"


def fmt_commodity_price(price, unit):
    if price is None:
        return None
    if unit == "¢/bu":
        return round(price)
    if unit == "$/oz":
        return round(price, 1)
    if unit == "$/lb":
        return round(price, 4)
    return round(price, 2)

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def collect_changes(data):
    changes = []
    warns   = []
    countries = data["countries"]

    # --- Stocks (Yahoo Finance) ---
    print("Fetching stock indices       (Yahoo Finance)...")
    for code, ticker in STOCK_TICKERS.items():
        if code in MANUAL_COUNTRIES:
            continue
        _, ytd_pct = yf_ytd(ticker)
        if ytd_pct is None:
            warns.append(f"  WARN [{code}] Stock Market YTD: no data ({ticker})")
            continue
        new_val = fmt_ytd(ytd_pct)
        old_val = countries[code]["metrics"]["market"]["Stock Market YTD"]["value"]
        if new_val != old_val:
            changes.append({
                "path":    f"{code} > Stock Market YTD",
                "country": code,
                "section": "market",
                "field":   "Stock Market YTD",
                "old":     old_val,
                "new":     new_val,
            })

    # --- USA bonds (FRED) ---
    print("Fetching USA bond yields     (FRED)...")
    usa_10y = usa_2y = None
    if not FRED_API_KEY:
        warns.append("  WARN [USA] FRED_API_KEY not set. USA bond yields skipped.")
    else:
        usa_10y = fred_latest(FRED_SERIES["10Y"])
        usa_2y  = fred_latest(FRED_SERIES["2Y"])

        if usa_10y is None:
            warns.append(f"  WARN [USA] 10Y Bond Yield: no data from FRED ({FRED_SERIES['10Y']})")
        else:
            new_val = fmt_yield(usa_10y)
            old_val = countries["USA"]["metrics"]["market"]["10Y Bond Yield"]["value"]
            if new_val != old_val:
                changes.append({
                    "path":    "USA > 10Y Bond Yield",
                    "country": "USA",
                    "section": "market",
                    "field":   "10Y Bond Yield",
                    "old":     old_val,
                    "new":     new_val,
                })

        if usa_10y and usa_2y:
            new_val = fmt_yield_curve(usa_10y, usa_2y)
            old_val = countries["USA"]["metrics"]["market"]["Yield Curve"]["value"]
            if new_val != old_val:
                changes.append({
                    "path":    "USA > Yield Curve",
                    "country": "USA",
                    "section": "market",
                    "field":   "Yield Curve",
                    "old":     old_val,
                    "new":     new_val,
                })
        elif usa_2y is None and usa_10y is not None:
            warns.append(f"  WARN [USA] Yield Curve: no 2Y data from FRED ({FRED_SERIES['2Y']})")

    # --- International bonds (Stooq) ---
    print("Fetching international bonds (Stooq)...")
    raw_10y = {}
    raw_2y  = {}

    for code, ticker in STOOQ_10Y.items():
        val = stooq_latest(ticker)
        time.sleep(0.3)  # polite pacing for Stooq
        if val is None:
            warns.append(f"  WARN [{code}] 10Y Bond Yield: no data from Stooq ({ticker})")
        else:
            raw_10y[code] = val

    for code, ticker in STOOQ_2Y.items():
        val = stooq_latest(ticker)
        time.sleep(0.3)
        if val is None:
            warns.append(f"  WARN [{code}] Yield Curve (2Y): no data from Stooq ({ticker})")
        else:
            raw_2y[code] = val

    for code in STOOQ_10Y:
        if code in MANUAL_COUNTRIES:
            continue

        if code in raw_10y:
            new_val = fmt_yield(raw_10y[code])
            old_val = countries[code]["metrics"]["market"]["10Y Bond Yield"]["value"]
            if new_val != old_val:
                changes.append({
                    "path":    f"{code} > 10Y Bond Yield",
                    "country": code,
                    "section": "market",
                    "field":   "10Y Bond Yield",
                    "old":     old_val,
                    "new":     new_val,
                })

        if code in raw_10y and code in raw_2y:
            new_val = fmt_yield_curve(raw_10y[code], raw_2y[code])
            old_val = countries[code]["metrics"]["market"]["Yield Curve"]["value"]
            if new_val != old_val:
                changes.append({
                    "path":    f"{code} > Yield Curve",
                    "country": code,
                    "section": "market",
                    "field":   "Yield Curve",
                    "old":     old_val,
                    "new":     new_val,
                })

    # --- FX (Yahoo Finance) ---
    print("Fetching FX rates            (Yahoo Finance)...")
    for code, cfg in FX_CONFIG.items():
        if code in MANUAL_COUNTRIES:
            continue
        val = yf_latest_close(cfg["ticker"])
        if val is None:
            warns.append(f"  WARN [{code}] {cfg['field']}: no data ({cfg['ticker']})")
            continue
        new_val = fmt_fx(val, cfg["field"])
        old_val = countries[code]["metrics"]["market"][cfg["field"]]["value"]
        if new_val != old_val:
            changes.append({
                "path":    f"{code} > {cfg['field']}",
                "country": code,
                "section": "market",
                "field":   cfg["field"],
                "old":     old_val,
                "new":     new_val,
            })

    # --- Commodities (Yahoo Finance) ---
    print("Fetching commodities         (Yahoo Finance)...")
    items = data["commodities"]["items"]
    for item in items:
        name   = item["name"]
        ticker = COMMODITY_TICKERS.get(name)
        if not ticker:
            warns.append(f"  WARN [commodity] {name}: no ticker configured")
            continue

        price, daily_pct = yf_daily_change(ticker)
        if price is None:
            warns.append(f"  WARN [commodity] {name}: no data ({ticker})")
            continue

        unit      = item.get("unit", "")
        new_price = fmt_commodity_price(price, unit)
        new_chg   = round(daily_pct, 1) if daily_pct is not None else None
        old_price = item.get("price")
        old_chg   = item.get("change")

        if new_price != old_price:
            changes.append({
                "path":           f"commodity > {name} > price",
                "country":        None,
                "section":        "commodity",
                "commodity_name": name,
                "field":          "price",
                "old":            old_price,
                "new":            new_price,
                "spark":          item.get("spark", []),
            })
        if new_chg != old_chg:
            changes.append({
                "path":           f"commodity > {name} > change",
                "country":        None,
                "section":        "commodity",
                "commodity_name": name,
                "field":          "change",
                "old":            old_chg,
                "new":            new_chg,
            })

    return changes, warns


def apply_changes(data, changes):
    countries     = data["countries"]
    items_by_name = {item["name"]: item for item in data["commodities"]["items"]}

    for ch in changes:
        # Safety belt: never write to macro fields.
        if ch.get("field") in MACRO_FIELDS_LOCKED:
            print(f"  BLOCKED (macro lock): {ch['path']}")
            continue

        if ch["section"] == "market":
            mkt = countries[ch["country"]]["metrics"]["market"][ch["field"]]
            mkt["value"]        = ch["new"]
            mkt["last_updated"] = TODAY

        elif ch["section"] == "commodity":
            item = items_by_name[ch["commodity_name"]]
            if ch["field"] == "price":
                spark = list(item.get("spark", []))
                item["spark"] = spark[1:] + [ch["new"]]
                item["price"] = ch["new"]
            elif ch["field"] == "change":
                item["change"] = ch["new"]

    data["commodities"]["asOf"] = TODAY
    return data

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch live market and commodity data.")
    parser.add_argument("--apply", action="store_true",
                        help="Write changes to data.json. Without this flag, preview only.")
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print(f"ERROR: data.json not found at {DATA_FILE}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  fetch_market_data.py  |  {TODAY}")
    print(f"  Mode: {'APPLY' if args.apply else 'PREVIEW'}")
    if not FRED_API_KEY:
        print("  WARNING: FRED_API_KEY not set in .env. USA bonds will be skipped.")
    print(f"{'='*60}\n")

    with open(DATA_FILE) as f:
        data = json.load(f)

    changes, warns = collect_changes(data)

    if warns:
        print("\nWarnings (fields skipped, existing values preserved):")
        for w in warns:
            print(w)

    print(f"\n{'='*60}")
    print(f"  Changes found: {len(changes)}")
    print(f"{'='*60}")

    if not changes:
        print("  No changes detected. Data is already current.")
    else:
        market_ch    = [c for c in changes if c["section"] == "market"]
        commodity_ch = [c for c in changes if c["section"] == "commodity"]

        if market_ch:
            print("\n  MARKET METRICS")
            for ch in market_ch:
                print(f"    {ch['path']}")
                print(f"      {ch['old']}  ->  {ch['new']}")

        if commodity_ch:
            print("\n  COMMODITIES")
            for ch in commodity_ch:
                print(f"    {ch['path']}")
                print(f"      {ch['old']}  ->  {ch['new']}")

    print()

    if not args.apply:
        print("Preview mode. No changes written.")
        print("Run with --apply to write to data.json.\n")
        return

    if not changes:
        print("Nothing to write.\n")
        return

    apply_changes(data, changes)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Applied {len(changes)} change(s) to data.json.")
    print("Run python3 build.py to rebuild the output file.\n")


if __name__ == "__main__":
    main()
