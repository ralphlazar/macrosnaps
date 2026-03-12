#!/usr/bin/env python3
"""
fetch_market_data.py
MacroSnaps - fetch current market metric values for all 12 countries.

Writes updated `value` and `last_updated` fields for all 8 market metrics
into data.json in place. Never touches historical arrays, stories, macro
metrics, or any other field.

Metrics updated:
  Stock Market YTD   - Yahoo Finance (YTD % change from Jan 1 close)
  Equity Vol         - Yahoo Finance implied vol indices, fallback to realized vol
  10Y Bond Yield     - FRED daily series
  Yield Curve        - Derived: 10Y minus 2Y (FRED)
  Corp Spread        - FRED ICE BofA IG/HY spread series
  Sov CDS            - Derived proxy: local 10Y minus UST or Bund 10Y
  FX pair            - Yahoo Finance
  FX Vol             - Computed: 30-day realized vol from daily FX returns

Run:
  cd ~/Downloads/macrosnaps
  python3 fetch_market_data.py

Dry run (preview only, nothing written):
  python3 fetch_market_data.py --dry-run

Requirements:
  pip3 install requests yfinance python-dotenv

Setup:
  Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
  Create .env in ~/Downloads/macrosnaps/ containing:
    FRED_API_KEY=your_key_here
"""

import json
import logging
import math
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

try:
    import yfinance as yf
except ImportError:
    sys.exit("ERROR: yfinance not installed. Run: pip3 install yfinance")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

DRY_RUN      = "--dry-run" in sys.argv
REQUEST_DELAY = 0.15   # seconds between FRED requests

DATA_FILE    = Path(__file__).parent / "data.json"
FRED_BASE    = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
TODAY        = date.today().isoformat()

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# COUNTRY CONFIG
# ---------------------------------------------------------------------------

# FRED daily 10Y bond yield series per country.
# CHN, IND, BRA, RUS have no reliable FRED daily series - kept as None.
BOND_10Y_SERIES = {
    "USA": "DGS10",
    "CAN": "IRLTLT01CAM156N",
    "GBR": "IRLTLT01GBM156N",
    "JPN": "IRLTLT01JPM156N",
    "DEU": "IRLTLT01DEM156N",
    "FRA": "IRLTLT01FRM156N",
    "ITA": "IRLTLT01ITM156N",
    "CHN": None,
    "IND": "INDIRLTLT01STM",    # OECD monthly series
    "ZAF": "IRLTLT01ZAM156N",
    "BRA": None,                # no reliable FRED series
    "RUS": None,
}

# FRED daily 2Y bond yield series per country for yield curve computation.
# Where no 2Y series exists, falls back to 3-month rate as short-rate proxy.
BOND_2Y_SERIES = {
    "USA": "DGS2",
    "CAN": "IRLTLT01CAM156N",   # no 2Y on FRED - use policy rate proxy below
    "GBR": "IRLTLT01GBM156N",   # no 2Y on FRED - use policy rate proxy below
    "JPN": "IRLTLT01JPM156N",   # no 2Y on FRED - use policy rate proxy below
    "DEU": "IRLTLT01DEM156N",   # no 2Y on FRED - use policy rate proxy below
    "FRA": "IRLTLT01FRM156N",   # no 2Y on FRED - use policy rate proxy below
    "ITA": "IRLTLT01ITM156N",   # no 2Y on FRED - use policy rate proxy below
    "CHN": None,
    "IND": "INDIRLTLT01STM",    # no 2Y on FRED - use policy rate proxy below
    "ZAF": "IRLTLT01ZAM156N",   # no 2Y on FRED - use policy rate proxy below
    "BRA": None,                # no FRED series for Brazil 10Y - keep existing
    "RUS": None,
}

# Short rate series (3-month or policy rate) used as 2Y proxy where 2Y unavailable.
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

# FRED corp spread series.
# BAMLC0A0CM = ICE BofA US Corporate IG OAS (%), multiply by 100 for bps.
# Used as a global IG proxy for all countries. Values on FRED are in percent.
# Note: BAMLC0A0CM2EY and BAMLHE00EHYIEY are Effective Yield series, not OAS.
CORP_SPREAD_SERIES = {
    "USA": "BAMLC0A0CM",
    "CAN": "BAMLC0A0CM",        # US IG as proxy
    "GBR": "BAMLC0A0CM",        # US IG as proxy
    "JPN": "BAMLC0A0CM",        # US IG as proxy
    "DEU": "BAMLC0A0CM",        # US IG as proxy
    "FRA": "BAMLC0A0CM",        # US IG as proxy
    "ITA": "BAMLC0A0CM",        # US IG as proxy
    "CHN": "BAMLEMCBPIOAS",     # ICE BofA EM Corporate OAS as proxy
    "IND": "BAMLEMCBPIOAS",     # ICE BofA EM Corporate OAS as proxy
    "ZAF": "BAMLEMCBPIOAS",     # ICE BofA EM Corporate OAS as proxy
    "BRA": "BAMLEMCBPIOAS",     # ICE BofA EM Corporate OAS as proxy
    "RUS": None,
}

# Yahoo Finance tickers for equity implied vol indices.
# None = fall back to computing 30-day realized vol from stock index.
# ^VFTSE and ^JNIV are delisted on Yahoo - realized vol fallback used for GBR/JPN.
EQUITY_VOL_TICKERS = {
    "USA": "^VIX",
    "CAN": None,            # no liquid vol index - use realized vol
    "GBR": None,            # ^VFTSE delisted - use realized vol
    "JPN": None,            # ^JNIV delisted - use realized vol
    "DEU": None,            # ^V2TX unreliable on Yahoo - use realized vol
    "FRA": None,            # ^V2TX unreliable on Yahoo - use realized vol
    "ITA": None,            # ^V2TX unreliable on Yahoo - use realized vol
    "CHN": None,            # iVIX suspended 2018 - use realized vol
    "IND": "^INDIAVIX",
    "ZAF": None,            # use realized vol
    "BRA": None,            # use realized vol
    "RUS": None,            # use realized vol
}

# Yahoo Finance tickers for stock indices (for YTD and realized vol fallback).
STOCK_TICKERS = {
    "USA": "^GSPC",
    "CAN": "^GSPTSE",
    "GBR": "^FTSE",
    "JPN": "^N225",
    "DEU": "^GDAXI",
    "FRA": "^FCHI",
    "ITA": "FTSEMIB.MI",
    "CHN": "000001.SS",
    "IND": "^BSESN",
    "ZAF": "^J203.JO",
    "BRA": "^BVSP",
    "RUS": "IMOEX.ME",
}

# Yahoo Finance FX tickers.
FX_TICKERS = {
    "USA": "DX-Y.NYB",     # DXY index
    "CAN": "CADUSD=X",
    "GBR": "GBPUSD=X",
    "JPN": "JPYUSD=X",
    "DEU": "EURUSD=X",
    "FRA": "EURUSD=X",
    "ITA": "EURUSD=X",
    "CHN": "CNYUSD=X",
    "IND": "INRUSD=X",
    "ZAF": "ZARUSD=X",
    "BRA": "BRLUSD=X",
    "RUS": "USDRUB=X",
}

# FX label in data.json per country (must match exactly).
FX_LABELS = {
    "USA": "USD/DXY",
    "CAN": "CAD/USD",
    "GBR": "GBP/USD",
    "JPN": "USD/JPY",
    "DEU": "EUR/USD",
    "FRA": "EUR/USD",
    "ITA": "EUR/USD",
    "CHN": "USD/CNY",
    "IND": "USD/INR",
    "ZAF": "USD/ZAR",
    "BRA": "USD/BRL",
    "RUS": "USD/RUB",
}

# Decimal places for FX values per country.
FX_DECIMALS = {
    "USA": 1,
    "CAN": 2,
    "GBR": 2,
    "JPN": 1,
    "DEU": 4,
    "FRA": 4,
    "ITA": 4,
    "CHN": 2,
    "IND": 2,
    "ZAF": 2,
    "BRA": 2,
    "RUS": 1,
}

# Whether Yahoo FX ticker is quoted as X-per-USD (True) or USD-per-X (False).
# If True, the raw Yahoo value is inverted to get display value.
FX_INVERT = {
    "USA": False,   # DXY - no inversion
    "CAN": False,   # CAD/USD - Yahoo gives CAD per USD, we want CAD/USD display
    "GBR": False,   # GBP/USD - Yahoo gives USD per GBP, matches display
    "JPN": True,    # USD/JPY - Yahoo JPYUSD=X gives JPY per USD inverted, we want USD/JPY
    "DEU": False,
    "FRA": False,
    "ITA": False,
    "CHN": True,    # USD/CNY - Yahoo CNYUSD=X, invert to get CNY per USD
    "IND": True,    # USD/INR - Yahoo INRUSD=X, invert to get INR per USD
    "ZAF": True,    # USD/ZAR - Yahoo ZARUSD=X, invert to get ZAR per USD
    "BRA": True,    # USD/BRL - Yahoo BRLUSD=X, invert to get BRL per USD
    "RUS": False,   # USD/RUB - Yahoo USDRUB=X already gives RUB per USD
}

# Sov CDS proxy: computed as local 10Y minus benchmark 10Y.
# Only computed for EM countries where the spread is meaningful.
# Developed markets (USA, CAN, GBR, JPN, DEU, FRA, ITA) are skipped - their
# spreads vs UST/Bunds are near zero or negative, making the proxy uninformative.
SOV_CDS_BENCHMARK = {"USA", "DEU"}
SOV_CDS_EM_ONLY   = {"CHN", "IND", "ZAF", "BRA"}   # only these get a value
SOV_CDS_VS_BUND   = {"FRA", "ITA"}   # unused now but kept for reference

# Yahoo Finance continuous futures tickers for commodities.
# Keyed by the symbol field in data.json commodities items.
COMMODITY_TICKERS = {
    "CL": "CL=F",   # WTI Crude
    "BZ": "BZ=F",   # Brent Crude
    "NG": "NG=F",   # Natural Gas
    "GC": "GC=F",   # Gold
    "SI": "SI=F",   # Silver
    "HG": "HG=F",   # Copper
    "ZW": "ZW=F",   # Wheat
    "ZC": "ZC=F",   # Corn
    "ZS": "ZS=F",   # Soybeans
}

# ---------------------------------------------------------------------------
# FRED FETCH
# ---------------------------------------------------------------------------

def fred_fetch_latest(series_id):
    """
    Fetch the single most recent observation from FRED for a series.
    Returns (date_str, float) or None on failure.
    """
    if not series_id:
        return None
    params = {
        "series_id":  series_id,
        "api_key":    FRED_API_KEY,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      5,   # grab a few in case the most recent is a dot (missing)
    }
    url = f"{FRED_BASE}/series/observations"
    try:
        r = requests.get(url, params=params, timeout=20)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 400:
            log.warning(f"    FRED {series_id}: series not found (400)")
            return None
        if r.status_code != 200:
            log.warning(f"    FRED {series_id}: HTTP {r.status_code}")
            return None
        obs = r.json().get("observations", [])
        for o in obs:
            if o["value"] not in (".", "", None):
                return (o["date"], float(o["value"]))
        log.warning(f"    FRED {series_id}: no usable observations")
        return None
    except Exception as exc:
        log.warning(f"    FRED {series_id}: {exc}")
        return None

# ---------------------------------------------------------------------------
# YAHOO FINANCE HELPERS
# ---------------------------------------------------------------------------

def yf_latest_close(ticker):
    """
    Return the most recent closing price for a Yahoo Finance ticker.
    Returns float or None.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as exc:
        log.warning(f"    Yahoo {ticker}: {exc}")
        return None

def yf_ytd_return(ticker):
    """
    Compute YTD % return for a stock index ticker.
    Fetches daily data from Jan 1 of the current year to today.
    Returns float (e.g. 2.5 for +2.5%) or None.
    """
    try:
        start = f"{date.today().year}-01-01"
        t = yf.Ticker(ticker)
        hist = t.history(start=start)
        if hist.empty or len(hist) < 2:
            return None
        open_price = float(hist["Close"].iloc[0])
        last_price = float(hist["Close"].iloc[-1])
        if open_price == 0:
            return None
        return (last_price - open_price) / open_price * 100
    except Exception as exc:
        log.warning(f"    Yahoo YTD {ticker}: {exc}")
        return None

def yf_realized_vol_30d(ticker):
    """
    Compute 30-day realized (historical) volatility from daily returns,
    annualized. Returns float (e.g. 18.5 for 18.5%) or None.
    """
    try:
        end   = datetime.today()
        start = end - timedelta(days=60)   # extra buffer for weekends/holidays
        t = yf.Ticker(ticker)
        hist = t.history(start=start.strftime("%Y-%m-%d"))
        if hist.empty or len(hist) < 20:
            return None
        closes = hist["Close"].tail(31)
        if len(closes) < 20:
            return None
        returns = closes.pct_change().dropna()
        vol = float(returns.std() * math.sqrt(252) * 100)
        return vol
    except Exception as exc:
        log.warning(f"    Yahoo realized vol {ticker}: {exc}")
        return None

def yf_fx_daily_returns(ticker, days=60):
    """
    Fetch daily FX closing prices for the last `days` calendar days.
    Returns a list of daily % returns, or None.
    """
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        t = yf.Ticker(ticker)
        hist = t.history(start=start.strftime("%Y-%m-%d"))
        if hist.empty or len(hist) < 20:
            return None
        closes = hist["Close"]
        returns = closes.pct_change().dropna().tolist()
        return returns
    except Exception as exc:
        log.warning(f"    Yahoo FX returns {ticker}: {exc}")
        return None

def yf_price_and_ytd(ticker):
    """
    Fetch latest close and YTD % change for a futures ticker.
    Uses the first available close on or after Jan 1 of the current year
    as the base price, matching the convention used for stock indices.
    Returns (current_price_float, ytd_pct_float) or (None, None).
    """
    try:
        today = datetime.today()
        jan1  = datetime(today.year, 1, 1)
        t = yf.Ticker(ticker)
        hist = t.history(start=jan1.strftime("%Y-%m-%d"))
        if hist.empty or len(hist) < 2:
            return None, None
        current    = float(hist["Close"].iloc[-1])
        jan1_close = float(hist["Close"].iloc[0])
        if jan1_close == 0:
            return current, None
        ytd = (current - jan1_close) / jan1_close * 100
        return current, ytd
    except Exception as exc:
        log.warning(f"    Yahoo price/YTD {ticker}: {exc}")
        return None, None

# ---------------------------------------------------------------------------
# METRIC FETCHERS
# ---------------------------------------------------------------------------

def fetch_stock_ytd(code):
    """
    Fetch Stock Market YTD % change.
    Returns formatted string like '+2.5%' or None.
    """
    ticker = STOCK_TICKERS.get(code)
    if not ticker:
        return None
    pct = yf_ytd_return(ticker)
    if pct is None:
        return None
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"

def fetch_equity_vol(code):
    """
    Fetch Equity Vol. Tries implied vol index first, falls back to realized vol.
    Returns formatted string like '~18' or None.
    """
    # Try implied vol ticker
    vol_ticker = EQUITY_VOL_TICKERS.get(code)
    if vol_ticker:
        val = yf_latest_close(vol_ticker)
        if val is not None:
            return f"~{round(val)}"

    # Fall back to realized vol from stock index
    stock_ticker = STOCK_TICKERS.get(code)
    if stock_ticker:
        rv = yf_realized_vol_30d(stock_ticker)
        if rv is not None:
            return f"~{round(rv)}"

    return None

def fetch_bond_10y(code):
    """
    Fetch 10Y bond yield from FRED.
    Returns (yield_float, formatted_string) or (None, None).
    """
    series = BOND_10Y_SERIES.get(code)
    if not series:
        return None, None
    result = fred_fetch_latest(series)
    if result is None:
        return None, None
    _, val = result
    return val, f"{val:.2f}%"

def fetch_short_rate(code):
    """
    Fetch short rate (2Y or 3-month proxy) from FRED.
    Returns float or None.
    """
    series = SHORT_RATE_SERIES.get(code)
    if not series:
        return None
    result = fred_fetch_latest(series)
    if result is None:
        return None
    return result[1]

def fetch_yield_curve(ten_y, short_rate):
    """
    Compute yield curve spread in bps: 10Y minus short rate.
    Returns formatted string like '+22bps' or '-45bps' or None.
    """
    if ten_y is None or short_rate is None:
        return None
    spread_bps = round((ten_y - short_rate) * 100)
    sign = "+" if spread_bps >= 0 else ""
    return f"{sign}{spread_bps}bps"

def fetch_corp_spread(code):
    """
    Fetch Corp Spread from FRED ICE BofA series.
    FRED values are in percent - multiply by 100 for bps.
    Returns formatted string like '100bps' or None.
    """
    series = CORP_SPREAD_SERIES.get(code)
    if not series:
        return None
    result = fred_fetch_latest(series)
    if result is None:
        return None
    _, val_pct = result
    bps = round(val_pct * 100)
    return f"{bps}bps"

def fetch_sov_cds_proxy(code, local_10y, ust_10y, bund_10y):
    """
    Compute Sov CDS proxy as sovereign spread over UST.
    Only computed for EM countries (CHN, IND, ZAF, BRA).
    All developed markets return None - the spread vs UST is near zero or
    negative for safe-haven countries, making the proxy uninformative.
    """
    if code not in SOV_CDS_EM_ONLY:
        return None
    if local_10y is None or ust_10y is None:
        return None

    spread_bps = round((local_10y - ust_10y) * 100)
    spread_bps = max(spread_bps, 0)
    return f"{spread_bps}bps"

def fetch_fx(code):
    """
    Fetch FX rate from Yahoo Finance.
    Inverts where needed and formats to the correct decimal places.
    Returns (raw_float, formatted_string) or (None, None).
    """
    ticker = FX_TICKERS.get(code)
    if not ticker:
        return None, None
    val = yf_latest_close(ticker)
    if val is None:
        return None, None

    if FX_INVERT.get(code) and val != 0:
        val = 1.0 / val

    decimals = FX_DECIMALS.get(code, 2)
    formatted = f"{val:.{decimals}f}"
    return val, formatted

def fetch_fx_vol(code):
    """
    Compute FX Vol as 30-day annualized realized vol from daily FX returns.
    Returns formatted string like '12.5%' or None.
    """
    ticker = FX_TICKERS.get(code)
    if not ticker:
        return None

    returns = yf_fx_daily_returns(ticker)
    if not returns or len(returns) < 20:
        return None

    # Use last 30 trading days
    recent = returns[-30:]
    mean = sum(recent) / len(recent)
    variance = sum((r - mean) ** 2 for r in recent) / len(recent)
    daily_std = math.sqrt(variance)
    annualized = daily_std * math.sqrt(252) * 100
    return f"{annualized:.1f}%"

# ---------------------------------------------------------------------------
# PROCESS ONE COUNTRY
# ---------------------------------------------------------------------------

def process_country(code, country_data, ust_10y, bund_10y):
    """
    Fetch all 8 market metrics for one country and return a dict of
    {metric_label: new_value_string} for metrics that were successfully fetched.
    """
    log.info(f"\n{'='*52}")
    log.info(f"  {code}")
    log.info(f"{'='*52}")

    updates = {}

    # Stock Market YTD
    val = fetch_stock_ytd(code)
    if val:
        updates["Stock Market YTD"] = val
        log.info(f"  Stock Market YTD    {val}")
    else:
        log.warning(f"  Stock Market YTD    FAILED")

    # Equity Vol
    val = fetch_equity_vol(code)
    if val:
        updates["Equity Vol"] = val
        log.info(f"  Equity Vol          {val}")
    else:
        log.warning(f"  Equity Vol          FAILED")

    # 10Y Bond Yield
    ten_y_float, ten_y_str = fetch_bond_10y(code)
    if ten_y_str:
        updates["10Y Bond Yield"] = ten_y_str
        log.info(f"  10Y Bond Yield      {ten_y_str}")
    else:
        log.warning(f"  10Y Bond Yield      FAILED (no FRED series)")

    # Yield Curve (needs 10Y and short rate)
    short_rate = fetch_short_rate(code)
    yc = fetch_yield_curve(ten_y_float, short_rate)
    if yc:
        updates["Yield Curve"] = yc
        log.info(f"  Yield Curve         {yc}")
    else:
        log.warning(f"  Yield Curve         FAILED")

    # Corp Spread
    val = fetch_corp_spread(code)
    if val:
        updates["Corp Spread"] = val
        log.info(f"  Corp Spread         {val}")
    else:
        log.warning(f"  Corp Spread         FAILED")

    # Sov CDS proxy
    val = fetch_sov_cds_proxy(code, ten_y_float, ust_10y, bund_10y)
    if val:
        updates["Sov CDS"] = val
        log.info(f"  Sov CDS             {val}")
    elif code not in SOV_CDS_EM_ONLY:
        log.info(f"  Sov CDS             (developed market - skipped)")
    else:
        log.warning(f"  Sov CDS             FAILED")

    # FX
    fx_float, fx_str = fetch_fx(code)
    fx_label = FX_LABELS.get(code)
    if fx_str and fx_label:
        updates[fx_label] = fx_str
        log.info(f"  {fx_label:<20}{fx_str}")
    else:
        log.warning(f"  FX                  FAILED")

    # FX Vol
    val = fetch_fx_vol(code)
    if val:
        updates["FX Vol"] = val
        log.info(f"  FX Vol              {val}")
    else:
        log.warning(f"  FX Vol              FAILED")

    return updates

# ---------------------------------------------------------------------------
# WRITE UPDATES INTO DATA.JSON
# ---------------------------------------------------------------------------

def apply_updates(country_data, updates):
    """
    Write updated values into the market metrics dict for one country.
    Only touches `value` and `last_updated`. Nothing else.
    """
    market = country_data["metrics"]["market"]
    for label, new_value in updates.items():
        if label in market:
            market[label]["value"] = new_value
            market[label]["last_updated"] = TODAY
        else:
            log.warning(f"    Label '{label}' not found in market metrics - skipped")

# ---------------------------------------------------------------------------
# COMMODITIES
# ---------------------------------------------------------------------------

def process_commodities(data):
    """
    Fetch latest price and YoY % change for all 9 commodities and update
    data.json in place. Only touches `price`, `change`, `spark`, and the
    top-level `asOf` date. Never touches `annual`, `story`, or any other field.
    """
    log.info(f"\n{'='*52}")
    log.info("  COMMODITIES")
    log.info(f"{'='*52}")

    items = data.get("commodities", {}).get("items", [])
    if not items:
        log.warning("  No commodities items found in data.json - skipping")
        return

    ok = 0
    failed = 0

    for item in items:
        symbol  = item.get("symbol")
        name    = item.get("name", symbol)
        ticker  = COMMODITY_TICKERS.get(symbol)

        if not ticker:
            log.warning(f"  {name:<16} no ticker configured - skipped")
            failed += 1
            continue

        current, ytd = yf_price_and_ytd(ticker)

        if current is None:
            log.warning(f"  {name:<16} FAILED")
            failed += 1
            continue

        # Update price (round to match existing precision in data.json)
        item["price"] = round(current, 2)

        # Update YTD change
        if ytd is not None:
            item["change"] = round(ytd, 1)

        # Update spark: drop oldest point, append new close
        spark = item.get("spark", [])
        if isinstance(spark, list) and len(spark) > 0:
            spark = spark[1:] + [round(current, 2)]
            item["spark"] = spark

        change_str = f"{ytd:+.1f}%" if ytd is not None else "YTD n/a"
        log.info(f"  {name:<16} {current:.2f}  ({change_str} YTD)")
        ok += 1

    # Update asOf date to match existing format, e.g. "Mar 12, 2026"
    data["commodities"]["asOf"] = datetime.today().strftime("%b %-d, %Y")

    log.info(f"\n  Commodities updated: {ok}  failed: {failed}")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if DRY_RUN:
        log.info("DRY RUN - no changes will be written to data.json\n")

    if not FRED_API_KEY:
        sys.exit(
            "\nERROR: FRED_API_KEY not set.\n"
            "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "Then add this line to .env in ~/Downloads/macrosnaps/\n"
            "  FRED_API_KEY=your_key_here\n"
        )

    if not DATA_FILE.exists():
        sys.exit(f"\nERROR: data.json not found at {DATA_FILE}\n")

    log.info(f"Reading {DATA_FILE} ...")
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    countries = data["countries"]

    # Pre-fetch UST and Bund 10Y - needed for all Sov CDS proxy calculations.
    log.info("\nPre-fetching benchmark 10Y yields (UST and Bund)...")
    ust_result  = fred_fetch_latest("DGS10")
    bund_result = fred_fetch_latest("IRLTLT01DEM156N")
    ust_10y  = ust_result[1]  if ust_result  else None
    bund_10y = bund_result[1] if bund_result else None
    log.info(f"  UST 10Y:  {ust_10y}%")
    log.info(f"  Bund 10Y: {bund_10y}%")

    run_order = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA",
                 "CHN", "IND", "ZAF", "BRA", "RUS"]

    all_updates  = {}
    total_ok     = 0
    total_failed = 0

    for code in run_order:
        if code not in countries:
            log.warning(f"\n[{code}] not found in data.json - skipping")
            continue

        updates = process_country(code, countries[code], ust_10y, bund_10y)
        all_updates[code] = updates
        total_ok     += len(updates)
        total_failed += (8 - len(updates))

    # Summary preview
    log.info(f"\n{'='*52}")
    log.info("SUMMARY")
    log.info(f"{'='*52}")
    for code, updates in all_updates.items():
        for label, val in updates.items():
            log.info(f"  {code:<4} {label:<22} -> {val}")

    log.info(f"\n  Updated : {total_ok}")
    log.info(f"  Failed  : {total_failed}")

    if DRY_RUN:
        process_commodities(data)
        log.info("\nDRY RUN complete. Nothing written.")
        return

    # Write updates
    for code, updates in all_updates.items():
        if updates:
            apply_updates(countries[code], updates)

    process_commodities(data)

    log.info(f"\nWriting {DATA_FILE} ...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info("Write complete.")

    log.info("\nNext steps:")
    log.info("  python3 build.py && git add -A && git commit -m 'Daily market update' && git push origin master")


if __name__ == "__main__":
    main()
