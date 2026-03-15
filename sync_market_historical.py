#!/usr/bin/env python3
"""
sync_market_historical.py
Rebuilds all market metric spark arrays in data.json from Jan 2000 to the present.

Rule
----
Every spark array must cover Jan 2000 → last available data point.
"Last available" must be within the last 3 months of today's date.
If a source stops updating, the chart shows a visible trailing gap rather than
silently hiding stale frozen data. This is intentional: gaps are diagnostic.

Metrics rebuilt
---------------
  Stock Market (index level)  — yfinance monthly last close
  FX rate                     — yfinance monthly last close
  10Y Bond Yield (%)          — FRED monthly (or daily resampled to month-end)
  Yield Curve (bps)           — derived: 10Y monthly − short rate monthly

Commodities
-----------
NOT touched here. sync_commodity_data.py owns commodity sparks and already
implements the correct full-history rebuild pattern from the Commodities sheet.

NOTE: The rolling spark update (spark[1:] + [new_close]) in fetch_market_data.py
is now superseded by this script. That block should be removed from
fetch_market_data.py once this script is confirmed working.

Run
---
  python3 sync_market_historical.py             # preview (no writes)
  python3 sync_market_historical.py --apply     # write to data.json
"""

import json
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit("ERROR: yfinance not installed.  pip3 install yfinance")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

APPLY        = "--apply" in sys.argv
DATA_FILE    = Path(__file__).parent / "data.json"
FRED_BASE    = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
START_DATE   = "2000-01-01"
STALE_MONTHS = 3   # warn if last spark point appears older than this

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA",
             "CHN", "IND", "ZAF", "BRA", "RUS"]

# ---------------------------------------------------------------------------
# SOURCE CONFIG  (mirrors fetch_market_data.py — keep in sync if changed)
# ---------------------------------------------------------------------------

STOCK_TICKERS = {
    "USA": "^GSPC",      "CAN": "^GSPTSE",    "GBR": "^FTSE",
    "JPN": "^N225",      "DEU": "^GDAXI",     "FRA": "^FCHI",
    "ITA": "FTSEMIB.MI", "CHN": "000001.SS",  "IND": "^BSESN",
    "ZAF": "^J203.JO",   "BRA": "^BVSP",      "RUS": "IMOEX.ME",
}

FX_TICKERS = {
    "USA": "DX-Y.NYB",  "CAN": "CADUSD=X",  "GBR": "GBPUSD=X",
    "JPN": "JPYUSD=X",  "DEU": "EURUSD=X",  "FRA": "EURUSD=X",
    "ITA": "EURUSD=X",  "CHN": "CNYUSD=X",  "IND": "INRUSD=X",
    "ZAF": "ZARUSD=X",  "BRA": "BRLUSD=X",  "RUS": "USDRUB=X",
}

FX_LABELS = {
    "USA": "USD/DXY",  "CAN": "CAD/USD",  "GBR": "GBP/USD",
    "JPN": "USD/JPY",  "DEU": "EUR/USD",  "FRA": "EUR/USD",
    "ITA": "EUR/USD",  "CHN": "USD/CNY",  "IND": "USD/INR",
    "ZAF": "USD/ZAR",  "BRA": "USD/BRL",  "RUS": "USD/RUB",
}

FX_INVERT = {
    "USA": False, "CAN": False, "GBR": False, "JPN": True,
    "DEU": False, "FRA": False, "ITA": False, "CHN": True,
    "IND": True,  "ZAF": True,  "BRA": True,  "RUS": False,
}

FX_DECIMALS = {
    "USA": 1, "CAN": 2, "GBR": 2, "JPN": 1,
    "DEU": 4, "FRA": 4, "ITA": 4, "CHN": 2,
    "IND": 2, "ZAF": 2, "BRA": 2, "RUS": 1,
}

# FRED 10Y bond yield series.  None = no series, spark will be empty.
BOND_10Y_SERIES = {
    "USA": "DGS10",            # daily → resampled
    "CAN": "IRLTLT01CAM156N",  # monthly
    "GBR": "IRLTLT01GBM156N",  # monthly
    "JPN": "IRLTLT01JPM156N",  # monthly
    "DEU": "IRLTLT01DEM156N",  # monthly
    "FRA": "IRLTLT01FRM156N",  # monthly
    "ITA": "IRLTLT01ITM156N",  # monthly
    "CHN": None,
    "IND": "INDIRLTLT01STM",   # monthly
    "ZAF": "IRLTLT01ZAM156N",  # monthly
    "BRA": None,
    "RUS": None,
}

# FRED short rate series (3-month or policy rate proxy) for yield curve.
SHORT_RATE_SERIES = {
    "USA": "TB3MS",
    "CAN": "IR3TIB01CAM156N",
    "GBR": "IR3TIB01GBM156N",
    "JPN": "IR3TIB01JPM156N",
    "DEU": "ECBDFR",
    "FRA": "ECBDFR",
    "ITA": "ECBDFR",
    "CHN": None,
    "IND": "IRSTCI01INM156N",
    "ZAF": "IRSTCI01ZAM156N",
    "BRA": "IRSTCI01BRM156N",
    "RUS": None,
}

# DGS10 is daily on FRED — resample to month-end.
DAILY_FRED_SERIES = {"DGS10", "TB3MS"}


# ---------------------------------------------------------------------------
# STALENESS CHECK
# ---------------------------------------------------------------------------

def stale_check(arr, label):
    """
    Warn if the array is empty or appears to have fewer points than expected.
    Expected minimum = months from Jan 2000 to (today − STALE_MONTHS).
    This catches sources that have quietly stopped updating.
    """
    today = date.today()
    months_since_2000 = (today.year - 2000) * 12 + today.month
    min_expected = months_since_2000 - STALE_MONTHS

    if not arr:
        log.warning(f"    ⚠  {label}: EMPTY — no data returned")
    elif len(arr) < min_expected:
        shortfall = min_expected - len(arr)
        log.warning(
            f"    ⚠  {label}: {len(arr)} pts — ~{shortfall} months missing "
            f"(source may have stopped updating)"
        )
    else:
        log.info(f"    ✓  {label}: {len(arr)} pts")


# ---------------------------------------------------------------------------
# DATA FETCHERS
# ---------------------------------------------------------------------------

_yf_cache  = {}   # ticker → Series of monthly closes
_fred_cache = {}  # series_id → Series of monthly values


def yf_monthly(ticker):
    """
    Fetch monthly last closes for a yfinance ticker from START_DATE to present.
    Cached per ticker — safe to call multiple times (e.g. shared FX tickers).
    Returns pd.Series with DatetimeIndex, or empty Series on failure.
    """
    if ticker in _yf_cache:
        return _yf_cache[ticker]

    try:
        t    = yf.Ticker(ticker)
        hist = t.history(start=START_DATE, auto_adjust=True)
        if hist.empty:
            log.warning(f"    yfinance {ticker}: no data")
            _yf_cache[ticker] = pd.Series(dtype=float)
            return _yf_cache[ticker]
        monthly = hist["Close"].resample("ME").last().dropna()
        _yf_cache[ticker] = monthly
        return monthly
    except Exception as e:
        log.warning(f"    yfinance {ticker}: {e}")
        _yf_cache[ticker] = pd.Series(dtype=float)
        return _yf_cache[ticker]


def fred_monthly(series_id):
    """
    Fetch a FRED series from START_DATE to present as monthly pd.Series.
    Daily series are resampled to month-end last observation.
    Cached per series_id.
    Returns pd.Series with DatetimeIndex, or empty Series on failure.
    """
    if not series_id:
        return pd.Series(dtype=float)
    if series_id in _fred_cache:
        return _fred_cache[series_id]

    params = {
        "series_id":         series_id,
        "api_key":           FRED_API_KEY,
        "file_type":         "json",
        "observation_start": START_DATE,
    }
    try:
        r = requests.get(f"{FRED_BASE}/series/observations", params=params, timeout=30)
        r.raise_for_status()
        time.sleep(0.15)

        records = {}
        for o in r.json().get("observations", []):
            if o["value"] not in (".", "", None):
                try:
                    records[o["date"]] = float(o["value"])
                except ValueError:
                    pass

        if not records:
            log.warning(f"    FRED {series_id}: no usable observations")
            _fred_cache[series_id] = pd.Series(dtype=float)
            return _fred_cache[series_id]

        s = pd.Series(records)
        s.index = pd.to_datetime(s.index)
        monthly = s.resample("ME").last().dropna()
        _fred_cache[series_id] = monthly
        return monthly

    except Exception as e:
        log.warning(f"    FRED {series_id}: {e}")
        _fred_cache[series_id] = pd.Series(dtype=float)
        return _fred_cache[series_id]


# ---------------------------------------------------------------------------
# SPARK BUILDERS
# ---------------------------------------------------------------------------

def build_stock_spark(code):
    """Monthly index level (not YTD%) from Jan 2000. Returns list of floats."""
    ticker = STOCK_TICKERS.get(code)
    if not ticker:
        return []
    monthly = yf_monthly(ticker)
    return [round(float(v), 2) for v in monthly]


def build_fx_spark(code):
    """Monthly FX rate from Jan 2000. Inverts where needed. Returns list of floats."""
    ticker  = FX_TICKERS.get(code)
    invert  = FX_INVERT.get(code, False)
    decimals = FX_DECIMALS.get(code, 2)
    if not ticker:
        return []
    monthly = yf_monthly(ticker)
    result  = []
    for v in monthly:
        v = float(v)
        if invert and v != 0:
            v = 1.0 / v
        result.append(round(v, decimals))
    return result


def build_bond_spark(code):
    """Monthly 10Y bond yield (%) from Jan 2000. Returns list of floats."""
    series = BOND_10Y_SERIES.get(code)
    if not series:
        return []
    monthly = fred_monthly(series)
    return [round(float(v), 3) for v in monthly]


def build_yield_curve_spark(code):
    """
    Monthly yield curve spread in bps (10Y − short rate) from Jan 2000.
    Returns list of floats (e.g. 22.5, -45.0).
    Returns [] if either series is missing.
    """
    ten_y_series   = BOND_10Y_SERIES.get(code)
    short_series   = SHORT_RATE_SERIES.get(code)
    if not ten_y_series or not short_series:
        return []

    ten_y  = fred_monthly(ten_y_series)
    short  = fred_monthly(short_series)

    if ten_y.empty or short.empty:
        return []

    # Align on common dates
    aligned = pd.concat([ten_y, short], axis=1, join="inner").dropna()
    if aligned.empty:
        return []

    aligned.columns = ["ten_y", "short"]
    spread_bps = ((aligned["ten_y"] - aligned["short"]) * 100).round(1)
    return [float(v) for v in spread_bps]


# ---------------------------------------------------------------------------
# WRITE HELPERS
# ---------------------------------------------------------------------------

def set_spark(frozen_historical, label, spark):
    """
    Write spark into _frozen_historical as {"type": "line", "v": [...]}.
    This is the structure the shell reads via historicalData[code][label].v.
    Preserves any existing keys on the entry other than type and v.
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
    log.info(f"Start date: {START_DATE}  |  Stale threshold: {STALE_MONTHS} months")
    log.info("")

    if not FRED_API_KEY:
        sys.exit("ERROR: FRED_API_KEY not set")
    if not DATA_FILE.exists():
        sys.exit(f"ERROR: data.json not found at {DATA_FILE}")

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
            log.warning(f"  No _frozen_historical found — skipping")
            continue

        # Stock Market
        stock_spark = build_stock_spark(code)
        stale_check(stock_spark, "Stock Market")
        if APPLY:
            set_spark(fh, "Stock Market YTD", stock_spark)
            writes += 1

        # FX
        fx_label = FX_LABELS.get(code)
        fx_spark  = build_fx_spark(code)
        stale_check(fx_spark, f"FX ({fx_label})")
        if APPLY and fx_label:
            set_spark(fh, fx_label, fx_spark)
            writes += 1

        # 10Y Bond Yield
        bond_spark = build_bond_spark(code)
        stale_check(bond_spark, "10Y Bond Yield")
        if APPLY:
            set_spark(fh, "10Y Bond Yield", bond_spark)
            writes += 1

        # Yield Curve
        yc_spark = build_yield_curve_spark(code)
        stale_check(yc_spark, "Yield Curve")
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
    log.info(f"Done. {writes} spark arrays written across {len(COUNTRIES)} countries.")
    log.info("")
    log.info("Next: python3 build.py --apply")
    log.info("")
    log.info("NOTE: Remove the rolling spark update block (spark[1:] + [new_close])")
    log.info("      from fetch_market_data.py — it is now superseded by this script.")


if __name__ == "__main__":
    main()
