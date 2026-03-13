#!/usr/bin/env python3
"""
refetch_historical.py
MacroSnaps - re-fetch historical chart data for all 12 countries.

Sources
  FRED  (api.stlouisfed.org) for macro metrics and rates
  Yahoo Finance (yfinance) for stock indices

Writes updated _frozen_historical into data.json in place.
Skips any metric that already has sufficient data, unless FORCE_OVERWRITE = True.
Never touches _frozen_weatherGrid or any other field.

# Fetchable via FRED daily series (USA only):
#   Equity Vol  -> VIXCLS (CBOE VIX)
#   Corp Spread -> BAMLC0A0CM (ICE BofA US IG OAS)
#   USD/DXY     -> DTWEXBGS (Nominal Broad Dollar Index)
#
# Permanently unfetchable (no free public source for any country):
#   Sov CDS, FX Vol
#
# Permanently unfetchable for all non-USA countries:
#   Equity Vol, Corp Spread
#
# Russia-specific gaps (sanctions-era data loss):
#   Yield Curve  -> sparse FRED data post-2022; only 42 points; blanked to avoid
#                   misleading chart artefact where displayed dates shift by view
#   Stock Market -> Yahoo Finance MOEX data ends Jun 2023; left as-is (real data,
#                   truncation is visually obvious)
Budget Deficit is fetched from the World Bank API (no key required).

After a successful run:
  python3 build.py && git add -A && git commit -m "Restore _frozen_historical"

Requirements
  pip3 install requests yfinance python-dotenv

Setup
  Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
  Create .env in ~/Downloads/macrosnaps/ containing:
    FRED_API_KEY=your_key_here

Run
  cd ~/Downloads/macrosnaps
  python3 refetch_historical.py
"""

import json
import logging
import os
import sys
import time
from collections import defaultdict
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
    pass  # .env is optional if FRED_API_KEY is already in the environment

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

FORCE_OVERWRITE = True   # Re-fetch everything to apply all fixes cleanly
MIN_POINTS      = 5      # Existing point count that qualifies as "already populated"
REQUEST_DELAY   = 0.15   # Seconds between FRED requests (avoid rate limiting)

DATA_FILE    = Path(__file__).parent / "data.json"
FRED_BASE    = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SERIES CONFIGURATION
#
# FRED_METRICS maps: country code -> metric label -> series config dict.
#
# Config fields:
#   id          FRED series ID
#   type        "line" or "bar" (how the chart renders)
#   transform   one of: monthly_120 | annual_10 | qtr_sum_pct_gdp | gdp_qtr_10
#   annual      True for annual bar charts
#   stepped     True for policy rate charts
#   zeroLine    True for yield curve
#   indexLabel  True for stock market charts
#
# Transforms
#   monthly_120       last 120 monthly observations as-is (10 years)
#   annual_10         last 10 annual observations as-is (direct annual series)
#   qtr_sum_pct_gdp   sum quarterly CA to annual totals, divide by nominal GDP
#                     to get % of GDP, last 10 matched years
#   gdp_qtr_10        compute annual real GDP growth from quarterly level series,
#                     last 10 complete years
# ---------------------------------------------------------------------------

# Short-rate series used only to compute yield curve (10Y - short rate).
# Fetched separately and not written directly to _frozen_historical.
SHORT_RATE_SERIES = {
    "USA": "GS3M",
    "CAN": "IR3TIB01CAM156N",
    "GBR": "IR3TIB01GBM156N",
    "JPN": "IR3TIB01JPM156N",
    "DEU": "IR3TIB01EZM156N",   # Eurozone 3-month interbank rate
    "FRA": "IR3TIB01EZM156N",
    "ITA": "IR3TIB01EZM156N",
    "CHN": "IRSTCI01CNM156N",   # Policy rate as short rate proxy
    "IND": "IRSTCI01INM156N",
    "ZAF": "IRSTCI01ZAM156N",
    "BRA": "IRSTCI01BRM156N",
    "RUS": "IRSTCI01RUM156N",
}

# FX series on FRED (daily, resampled to monthly end-of-month values).
FX_FRED_SERIES = {
    "USA": "DTWEXBGS",  # Nominal Broad U.S. Dollar Index (DXY proxy)
    "CAN": "DEXCAUS",   # Canadian dollars per USD
    "GBR": "DEXUSUK",   # USD per British pound
    "JPN": "DEXJPUS",   # Yen per USD
    "DEU": "DEXUSEU",   # USD per euro
    "FRA": "DEXUSEU",
    "ITA": "DEXUSEU",
    "CHN": "DEXCHUS",   # Yuan per USD
    "IND": "DEXINUS",   # Rupees per USD
    "ZAF": "DEXSFUS",   # Rand per USD
    "BRA": "DEXBZUS",   # Brazilian reals per USD
    "RUS": "DEXRUUS",   # Rubles per USD (may have post-2022 gaps)
}

# Fallback FX metric labels if the label cannot be detected from data.json.
FX_LABEL_DEFAULTS = {
    "USA": "USD/DXY",
    "CAN": "USD/CAD",
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

# Yahoo Finance tickers for the stock market index in each country.
STOCK_TICKERS = {
    "USA": "^GSPC",       # S&P 500
    "CAN": "^GSPTSE",     # TSX Composite
    "GBR": "^FTSE",       # FTSE 100
    "JPN": "^N225",       # Nikkei 225
    "DEU": "^GDAXI",      # DAX
    "FRA": "^FCHI",       # CAC 40
    "ITA": "FTSEMIB.MI",  # FTSE MIB
    "CHN": "000001.SS",   # Shanghai Composite
    "IND": "^BSESN",      # BSE Sensex
    "ZAF": "^J203.JO",    # JSE All Share
    "BRA": "^BVSP",       # Bovespa
    "RUS": "IMOEX.ME",    # MOEX (may have post-2022 gaps)
}


# World Bank nominal GDP series via FRED (current USD, annual).
# Used to convert Current Account from millions USD to % of GDP.
# Pattern: MKTGDP + ISO-2 + A646NWDB
NOMINAL_GDP_SERIES = {
    "USA": "MKTGDPUSA646NWDB",
    "CAN": "MKTGDPCAA646NWDB",
    "GBR": "MKTGDPGBA646NWDB",
    "JPN": "MKTGDPJPA646NWDB",
    "DEU": "MKTGDPDEA646NWDB",
    "FRA": "MKTGDPFRA646NWDB",
    "ITA": "MKTGDPITA646NWDB",
    "CHN": "MKTGDPCNA646NWDB",
    "IND": "MKTGDPINA646NWDB",
    "ZAF": "MKTGDPZAA646NWDB",
    "BRA": "MKTGDPBRA646NWDB",
    "RUS": "MKTGDPRUA646NWDB",
}

# Yahoo Finance tickers for commodity continuous futures contracts.
# Written to each commodity item as _frozen_historical (120 monthly closes).
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

# FRED daily series fetchable for specific countries only.
# Uses the same fetch_fx_monthly daily-to-monthly resampler.
# Add a country code here when a free FRED source exists for that country.
DAILY_FRED_SERIES = {
    "USA": {
        "Equity Vol":  "VIXCLS",       # CBOE VIX (daily)
        "Corp Spread": "BAMLC0A0CM",   # ICE BofA US Investment Grade OAS (daily)
    },
}

# Metrics with no free data source for a given country.
# The exempt set contains country codes that CAN be fetched (handled above).
# All other countries get their _frozen_historical["v"] written to [] so the
# chart shows blank instead of stale or misleading data.
VOID_METRICS = {
    "Equity Vol":  {"USA"},   # USA fetched via DAILY_FRED_SERIES; all others blank
    "Corp Spread": {"USA"},   # USA fetched via DAILY_FRED_SERIES; all others blank
    "Sov CDS":     set(),     # no free source for any country
    "FX Vol":      set(),     # no free source for any country
}

# Metrics blanked per country for specific data quality reasons.
# These have partial data that produces misleading chart artefacts.
COUNTRY_VOID_METRICS = {
    "RUS": {"Yield Curve", "USD/RUB"},  # Yield Curve: only 42 points post-sanctions (misleading);
                                         # USD/RUB: DEXRUUS discontinued on FRED post-sanctions
    "CHN": {"Policy Rate"},             # PBOC rate not available on FRED (non-OECD member)
}

# All metric names that are NOT the FX pair. Used to detect the FX label.
KNOWN_NON_FX_METRICS = {
    "GDP Growth", "Inflation (CPI)", "Unemployment", "Budget Deficit",
    "Current Account", "Policy Rate", "Stock Market YTD", "Equity Vol",
    "10Y Bond Yield", "Yield Curve", "Corp Spread", "Sov CDS", "FX Vol",
}

FRED_METRICS = {
    "USA": {
        "GDP Growth":      {"id": "A191RL1A225NBEA", "transform": "annual_10",   "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01USM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "UNRATE",           "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "FEDFUNDS",         "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "GS10",             "transform": "monthly_120", "type": "line"},
    },
    "CAN": {
        "GDP Growth":      {"id": "NGDPRSAXDCCAQ",   "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01CAM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTCAM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01CAM156N", "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01CAM156N", "transform": "monthly_120", "type": "line"},
    },
    "GBR": {
        "GDP Growth":      {"id": "NGDPRSAXDCGBQ",   "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01GBM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRHUTTTTGBM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01GBM156N",  "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01GBM156N", "transform": "monthly_120", "type": "line"},
    },
    "JPN": {
        "GDP Growth":      {"id": "NGDPRSAXDCJPQ",   "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01JPM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTJPM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01JPM156N", "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01JPM156N", "transform": "monthly_120", "type": "line"},
    },
    "DEU": {
        "GDP Growth":      {"id": "CLVMNACSCAB1GQDE", "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01DEM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRHUTTTTDEM156S",  "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01EZM156N",   "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01DEM156N",  "transform": "monthly_120", "type": "line"},
    },
    "FRA": {
        "GDP Growth":      {"id": "CLVMNACSCAB1GQFR", "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01FRM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRHUTTTTFRM156S",  "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01EZM156N",   "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01FRM156N",  "transform": "monthly_120", "type": "line"},
    },
    "ITA": {
        "GDP Growth":      {"id": "CLVMNACSCAB1GQIT", "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01ITM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRHUTTTTITM156S",  "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01EZM156N",   "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01ITM156N",  "transform": "monthly_120", "type": "line"},
    },
    "CHN": {
        "GDP Growth":      {"id": "CHNGDPNQDSMEI",    "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01CNM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTCNM156S",  "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01CNM156N",  "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "INTGSTCNM193N",    "transform": "monthly_120", "type": "line"},
    },
    "IND": {
        "GDP Growth":      {"id": "INDGDPNQDSMEI",    "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01INM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTINM156S",  "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01INM156N",  "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "INTGSTINM193N",    "transform": "monthly_120", "type": "line"},
    },
    "ZAF": {
        "GDP Growth":      {"id": "ZAFGDPNQDSMEI",    "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01ZAM659N",  "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTMZAM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01ZAM156N",  "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01ZAM156N",  "transform": "monthly_120", "type": "line"},
    },
    "BRA": {
        "GDP Growth":      {"id": "NGDPRSAXDCBRQ",   "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01BRM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTBRM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01BRM156N", "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "INTGSTBRM193N",   "transform": "monthly_120", "type": "line"},
    },
    "RUS": {
        "GDP Growth":      {"id": "NGDPRSAXDCRUQ",   "transform": "gdp_qtr_10",  "type": "bar",  "annual": True},
        "Inflation (CPI)": {"id": "CPALTT01RUM659N", "transform": "monthly_120", "type": "line"},
        "Unemployment":    {"id": "LRUNTTTTRUM156S", "transform": "monthly_120", "type": "line"},
        "Policy Rate":     {"id": "IRSTCI01RUM156N", "transform": "monthly_120", "type": "line", "stepped": True},
        "10Y Bond Yield":  {"id": "IRLTLT01RUM156N", "transform": "monthly_120", "type": "line"},
    },
}


# ---------------------------------------------------------------------------
# FRED FETCH
# ---------------------------------------------------------------------------

def fred_fetch(series_id, limit=200, observation_start=None):
    """
    Fetch observations from FRED for one series.
    Fetches the most recent `limit` observations (sort_order=desc, then reversed)
    so results are always sorted oldest first and contain recent data.
    Returns a list of (date_str, float) pairs, or None on error.
    """
    params = {
        "series_id":  series_id,
        "api_key":    FRED_API_KEY,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      limit,
    }
    if observation_start:
        params["observation_start"] = observation_start

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
        pairs = [
            (o["date"], float(o["value"]))
            for o in obs
            if o["value"] not in (".", "", None)
        ]
        if not pairs:
            log.warning(f"    FRED {series_id}: returned no usable observations")
            return None
        # Reverse so result is oldest-first
        pairs.reverse()
        return pairs
    except Exception as exc:
        log.warning(f"    FRED {series_id}: {exc}")
        return None


# ---------------------------------------------------------------------------
# OECD FETCH (fallback for unemployment where FRED has no monthly series)
# ---------------------------------------------------------------------------

# OECD uses standard ISO-3 country codes for most countries.
# Non-members (CHN, IND, RUS) are not in this dataset.
OECD_UNEMPLOYMENT_COUNTRIES = {"GBR", "DEU", "FRA", "ITA", "ZAF", "BRA"}

def oecd_fetch_unemployment(country_code):
    """
    Fetch monthly harmonized unemployment rate from the OECD Data API.
    Returns a list of (date_str, float) pairs sorted oldest first, or None.
    Only works for OECD member and partner countries in the HUR dataset.
    """
    url = (
        f"https://stats.oecd.org/SDMX-JSON/data/LFSRATE/"
        f"{country_code}.LR/all"
    )
    params = {"startTime": "2008-01", "format": "jsondata"}
    try:
        r = requests.get(url, params=params, timeout=30)
        time.sleep(REQUEST_DELAY)
        if r.status_code != 200:
            log.warning(f"    OECD {country_code} unemployment: HTTP {r.status_code}")
            return None
        body = r.json()
        datasets   = body.get("data", {}).get("dataSets", [])
        structures = body.get("data", {}).get("structures", [])
        if not datasets or not structures:
            log.warning(f"    OECD {country_code} unemployment: empty response")
            return None
        series_map = datasets[0].get("series", {})
        if not series_map:
            log.warning(f"    OECD {country_code} unemployment: no series in response")
            return None
        # Take the first series key
        obs = list(series_map.values())[0].get("observations", {})
        time_values = structures[0]["dimensions"]["observation"][0]["values"]
        pairs = []
        for idx_str, vals in obs.items():
            idx = int(idx_str)
            if idx < len(time_values) and vals and vals[0] is not None:
                period = time_values[idx]["id"]   # "2019-01"
                pairs.append((period + "-01", float(vals[0])))
        pairs.sort(key=lambda x: x[0])
        return pairs if pairs else None
    except Exception as exc:
        log.warning(f"    OECD {country_code} unemployment: {exc}")
        return None




# ---------------------------------------------------------------------------
# WORLD BANK FETCH (Budget Deficit - no key required)
# ---------------------------------------------------------------------------

def fetch_wb_budget_deficit(country_code):
    """
    Fetch general government net lending/borrowing (% GDP) from World Bank API.
    Indicator: GC.NLD.TOTL.GD.ZS (negative = deficit).
    Returns last 10 annual values sorted oldest first, or None on error.
    No API key required.
    """
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/GC.NLD.TOTL.GD.ZS"
    try:
        r = requests.get(url, params={"format": "json", "mrv": 10, "per_page": 10}, timeout=20)
        time.sleep(REQUEST_DELAY)
        if r.status_code != 200:
            log.warning(f"    World Bank budget deficit {country_code}: HTTP {r.status_code}")
            return None
        data = r.json()
        if not isinstance(data, list) or len(data) < 2 or not data[1]:
            log.warning(f"    World Bank budget deficit {country_code}: unexpected response")
            return None
        pts = sorted(
            [(x["date"], r2(x["value"])) for x in data[1] if x is not None and x["value"] is not None],
            key=lambda x: x[0]
        )
        vals = [v for _, v in pts]
        return vals[-10:] if vals else None
    except Exception as exc:
        log.warning(f"    World Bank budget deficit {country_code}: {exc}")
        return None


# World Bank ISO-2 codes mapped from MacroSnaps ISO-3 codes.
WB_ISO2 = {
    "USA": "US", "CAN": "CA", "GBR": "GB", "JPN": "JP",
    "DEU": "DE", "FRA": "FR", "ITA": "IT", "CHN": "CN",
    "IND": "IN", "ZAF": "ZA", "BRA": "BR", "RUS": "RU",
}


def fetch_wb_current_account(country_code):
    """
    Fetch current account balance (% of GDP) from World Bank API.
    Indicator: BN.CAB.XOKA.GD.ZS (negative = deficit).
    Returns last 10 annual values sorted oldest first, or None on error.
    No API key required.
    """
    iso2 = WB_ISO2.get(country_code, country_code)
    url = f"https://api.worldbank.org/v2/country/{iso2}/indicator/BN.CAB.XOKA.GD.ZS"
    try:
        r = requests.get(url, params={"format": "json", "mrv": 10, "per_page": 10}, timeout=20)
        time.sleep(REQUEST_DELAY)
        if r.status_code != 200:
            log.warning(f"    World Bank current account {country_code}: HTTP {r.status_code}")
            return None
        data = r.json()
        if not isinstance(data, list) or len(data) < 2 or not data[1]:
            log.warning(f"    World Bank current account {country_code}: unexpected response")
            return None
        pts = sorted(
            [(x["date"], r2(x["value"])) for x in data[1] if x is not None and x["value"] is not None],
            key=lambda x: x[0]
        )
        vals = [v for _, v in pts]
        return vals[-10:] if vals else None
    except Exception as exc:
        log.warning(f"    World Bank current account {country_code}: {exc}")
        return None


def r2(v):
    """Round to 2 decimal places."""
    return round(v, 2)


def parse_forecast_value(s):
    """
    Extract a numeric float from a forecast string like '+2.2%' or '-7.5% GDP'.
    Returns a rounded float, or None if no number is found.
    """
    import re
    m = re.search(r'[-+]?\d+\.?\d*', str(s))
    return r2(float(m.group())) if m else None


def apply_monthly_120(pairs):
    """Return the last 120 monthly values from the series (10 years)."""
    if not pairs:
        return None
    vals = [r2(v) for _, v in pairs]
    return vals[-120:] if len(vals) >= 1 else None


def apply_annual_10(pairs):
    """Return the last 10 values from a directly annual series."""
    if not pairs:
        return None
    vals = [r2(v) for _, v in pairs]
    return vals[-10:] if len(vals) >= 1 else None


def apply_qtr_sum_pct_gdp(pairs, gdp_by_year):
    """
    Sum quarterly CA values to annual totals (millions USD), then divide by
    nominal GDP (also converted to millions USD) to get % of GDP.
    Returns the last 10 matched years. Skips years where GDP is missing
    (handles World Bank data lag gracefully).
    """
    if not pairs:
        return None
    by_year = defaultdict(list)
    for date_str, val in pairs:
        by_year[date_str[:4]].append(val)
    complete = {y: vs for y, vs in by_year.items() if len(vs) >= 4}
    if not complete:
        return None
    results = []
    for year in sorted(complete.keys()):
        gdp_usd = gdp_by_year.get(year)
        if not gdp_usd or gdp_usd == 0:
            continue  # World Bank lag: skip years with no GDP data
        ca_millions = sum(complete[year])
        gdp_millions = gdp_usd / 1_000_000
        pct = r2(ca_millions / gdp_millions * 100)
        results.append(pct)
    return results[-10:] if results else None


def apply_gdp_qtr_10(pairs):
    """
    Compute annual real GDP growth from a quarterly level series.
    Averages the 4 quarters within each year to get an annual level,
    then computes year-over-year percentage change.
    Returns the last 10 complete-year growth values.
    """
    if not pairs or len(pairs) < 8:
        return None
    by_year = defaultdict(list)
    for date_str, val in pairs:
        by_year[date_str[:4]].append(val)
    # Only use years with all 4 quarters
    complete = {y: vs for y, vs in by_year.items() if len(vs) >= 4}
    if len(complete) < 2:
        return None
    sorted_years = sorted(complete.keys())
    annual_avg = {y: sum(complete[y]) / len(complete[y]) for y in sorted_years}
    growth = []
    for i in range(1, len(sorted_years)):
        y_prev = sorted_years[i - 1]
        y_curr = sorted_years[i]
        base = annual_avg[y_prev]
        if base and base != 0:
            pct = (annual_avg[y_curr] - base) / abs(base) * 100
            growth.append(r2(pct))
    return growth[-10:] if growth else None


def apply_transform(pairs, transform):
    """Dispatch to the correct transform function."""
    if transform == "monthly_120":
        return apply_monthly_120(pairs)
    if transform == "annual_10":
        return apply_annual_10(pairs)
    if transform == "gdp_qtr_10":
        return apply_gdp_qtr_10(pairs)
    log.warning(f"    Unknown transform '{transform}'")
    return None


# ---------------------------------------------------------------------------
# YIELD CURVE
# ---------------------------------------------------------------------------

def compute_yield_curve(long_pairs, short_pairs):
    """
    Subtract short rate from 10Y rate on matching months.
    Normalizes dates to YYYY-MM to handle FRED series with different
    day-of-month conventions for the same reporting period.
    Returns the last 120 monthly spread values (10 years).
    """
    if not long_pairs or not short_pairs:
        return None
    long_dict  = {d[:7]: v for d, v in long_pairs}
    short_dict = {d[:7]: v for d, v in short_pairs}
    common = sorted(set(long_dict) & set(short_dict))
    if not common:
        return None
    spread = [r2(long_dict[d] - short_dict[d]) for d in common]
    return spread[-120:] if spread else None


# ---------------------------------------------------------------------------
# STOCK MARKET (Yahoo Finance)
# ---------------------------------------------------------------------------

def fetch_stock_monthly(ticker):
    """
    Fetch monthly closing prices for a stock index via yfinance.
    Returns the last 120 monthly values (10 years), or None on failure.
    """
    try:
        hist = yf.Ticker(ticker).history(period="11y", interval="1mo")
        if hist.empty:
            log.warning(f"    Yahoo {ticker}: no data returned")
            return None
        vals = [r2(float(v)) for v in hist["Close"].dropna().tolist()]
        return vals[-120:] if vals else None
    except Exception as exc:
        log.warning(f"    Yahoo {ticker}: {exc}")
        return None


# ---------------------------------------------------------------------------
# NOMINAL GDP (World Bank via FRED, for Current Account % GDP conversion)
# ---------------------------------------------------------------------------

def fetch_nominal_gdp(code):
    """
    Fetch annual nominal GDP in current USD from the World Bank series on FRED.
    Returns a {year_str: gdp_usd_float} dict, or empty dict on failure.
    Series are annual and typically lag by 1-2 years (World Bank publication delay).
    """
    series_id = NOMINAL_GDP_SERIES.get(code)
    if not series_id:
        log.warning(f"  No nominal GDP series configured for {code}")
        return {}
    pairs = fred_fetch(series_id, limit=20)
    if not pairs:
        log.warning(f"  Nominal GDP fetch failed for {code} [{series_id}]")
        return {}
    gdp_by_year = {date_str[:4]: val for date_str, val in pairs}
    log.info(f"  Nominal GDP [{series_id}]: {len(gdp_by_year)} years "
             f"({min(gdp_by_year)} to {max(gdp_by_year)})")
    return gdp_by_year


# ---------------------------------------------------------------------------
# COMMODITIES (Yahoo Finance)
# ---------------------------------------------------------------------------

def fetch_commodity_historical(ticker):
    """
    Fetch monthly closing prices for a commodity futures contract via yfinance.
    Returns the last 120 monthly values (10 years), or None on failure.
    """
    try:
        hist = yf.Ticker(ticker).history(period="11y", interval="1mo")
        if hist.empty:
            log.warning(f"    Yahoo {ticker}: no data returned")
            return None
        vals = [r2(float(v)) for v in hist["Close"].dropna().tolist()]
        return vals[-120:] if vals else None
    except Exception as exc:
        log.warning(f"    Yahoo {ticker}: {exc}")
        return None


def process_commodities(data):
    """
    Fetch and write _frozen_historical for each commodity item.
    Writes {"v": [...], "type": "line"} to each item in data["commodities"]["items"].
    Never touches price, change, spark, annual, or story fields.
    """
    items = data.get("commodities", {}).get("items", [])
    if not items:
        log.warning("No commodity items found in data.json")
        return

    log.info(f"\n{'='*52}")
    log.info("  COMMODITIES")
    log.info(f"{'='*52}")

    fetched, skipped, failed = 0, 0, 0

    for item in items:
        name   = item.get("name", "?")
        ticker = COMMODITY_TICKERS.get(name)

        if not ticker:
            log.warning(f"  No ticker configured for '{name}' - skipping")
            skipped += 1
            continue

        if not FORCE_OVERWRITE and isinstance(item.get("_frozen_historical"), dict):
            existing = item["_frozen_historical"].get("v", [])
            if len(existing) >= MIN_POINTS:
                log.info(f"  SKIP    {name} (already populated)")
                skipped += 1
                continue

        log.info(f"  Fetch   {name}  [{ticker}]")
        vals = fetch_commodity_historical(ticker)
        if vals:
            item["_frozen_historical"] = {"v": vals, "type": "line"}
            log.info(f"    OK ({len(vals)} points)")
            fetched += 1
        else:
            log.warning(f"    FAILED")
            failed += 1

    log.info(f"\n  Commodities: fetched={fetched}, skipped={skipped}, failed={failed}")


# ---------------------------------------------------------------------------
# FX (FRED daily, resampled to monthly)
# ---------------------------------------------------------------------------

def fetch_fx_monthly(fred_series):
    """
    Fetch daily FX rate from FRED, resample to monthly end-of-month values.
    Returns the last 120 monthly values (10 years), or None on failure.
    """
    pairs = fred_fetch(fred_series, limit=3000, observation_start="2015-01-01")
    if not pairs:
        return None
    # Keep only the last observation within each YYYY-MM month
    by_month = {}
    for date_str, val in pairs:
        by_month[date_str[:7]] = val
    sorted_months = sorted(by_month.keys())
    vals = [r2(by_month[m]) for m in sorted_months]
    return vals[-120:] if vals else None


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def is_populated(frozen, metric_key):
    """Return True if the metric already has MIN_POINTS or more data points."""
    entry = frozen.get(metric_key)
    if not entry:
        return False
    return len(entry.get("v", [])) >= MIN_POINTS


def build_entry(vals, cfg):
    """Build a _frozen_historical entry dict from processed values and config."""
    entry = {"v": vals, "type": cfg["type"]}
    if cfg.get("annual"):    entry["annual"]     = True
    if cfg.get("stepped"):   entry["stepped"]    = True
    if cfg.get("zeroLine"):  entry["zeroLine"]   = True
    if cfg.get("indexLabel"):entry["indexLabel"] = True
    return entry


def detect_fx_label(country_data, frozen, code):
    """
    Find the FX metric key for a country.
    Checks: (1) nested metrics dict (macro/market sub-keys),
            (2) flat metrics list/dict,
            (3) existing frozen keys,
            (4) hardcoded default table.
    """
    metrics = country_data.get("metrics", {})

    # Case 1: nested dict with 'macro' and 'market' sub-dicts
    if isinstance(metrics, dict):
        for section in metrics.values():
            if isinstance(section, dict):
                for name in section.keys():
                    if name and name not in KNOWN_NON_FX_METRICS:
                        return name
            elif isinstance(section, list):
                for item in section:
                    name = item if isinstance(item, str) else item.get("name", "")
                    if name and name not in KNOWN_NON_FX_METRICS:
                        return name

    # Case 2: flat list
    elif isinstance(metrics, list):
        for item in metrics:
            name = item if isinstance(item, str) else item.get("name", "")
            if name and name not in KNOWN_NON_FX_METRICS:
                return name

    # Case 3: existing frozen keys (excluding the wrong "macro" fallback)
    for key in frozen:
        if key not in KNOWN_NON_FX_METRICS and key != "macro":
            return key

    # Case 4: hardcoded defaults
    return FX_LABEL_DEFAULTS.get(code)


# ---------------------------------------------------------------------------
# PER-COUNTRY PROCESSING
# ---------------------------------------------------------------------------

def process_country(code, country_data):
    """
    Fetch and update _frozen_historical for one country.
    Returns a dict with 'fetched', 'skipped', and 'failed' lists.
    """
    if "_frozen_historical" not in country_data:
        country_data["_frozen_historical"] = {}
    frozen = country_data["_frozen_historical"]

    metrics_cfg = FRED_METRICS.get(code, {})
    results = {"fetched": [], "skipped": [], "failed": []}

    # Retain 10Y and short rate pairs so we can compute yield curve after.
    ten_y_pairs   = None
    short_pairs   = None

    # Fetch FRED-sourced metrics
    for metric, cfg in metrics_cfg.items():

        if is_populated(frozen, metric) and not FORCE_OVERWRITE:
            log.info(f"  SKIP    {metric} (already populated)")
            results["skipped"].append(metric)
            # Still need 10Y pairs for yield curve even when skipping
            if metric == "10Y Bond Yield":
                ten_y_pairs = fred_fetch(cfg["id"], limit=130, observation_start="2015-01-01")
            continue

        log.info(f"  Fetch   {metric}  [{cfg['id']}]")
        pairs = fred_fetch(cfg["id"], limit=250)

        if metric == "10Y Bond Yield":
            ten_y_pairs = pairs[-130:] if pairs else None  # keep only recent 130 for yield curve

        if not pairs:
            # FRED has no monthly unemployment for many non-US countries.
            # Try OECD as a fallback.
            if metric == "Unemployment" and code in OECD_UNEMPLOYMENT_COUNTRIES:
                log.info(f"    Trying OECD fallback for {metric}...")
                pairs = oecd_fetch_unemployment(code)
                if pairs:
                    log.info(f"    OECD OK ({len(pairs)} raw points)")
                else:
                    log.warning(f"    OECD fallback also failed")

        if not pairs:
            results["failed"].append(metric)
            continue

        vals = apply_transform(pairs, cfg["transform"])
        if not vals:
            log.warning(f"    transform produced no values")
            results["failed"].append(metric)
            continue

        frozen[metric] = build_entry(vals, cfg)
        log.info(f"    OK ({len(vals)} points)")
        results["fetched"].append(metric)

    # Fetch short rate for yield curve
    short_series = SHORT_RATE_SERIES.get(code)
    if short_series:
        short_pairs = fred_fetch(short_series, limit=130, observation_start="2015-01-01")
        if short_pairs:
            log.info(f"  Short rate [{short_series}]: OK ({len(short_pairs)} points)")
        else:
            log.warning(f"  Short rate [{short_series}]: FAILED - yield curve will be skipped")

    # Yield curve
    if not is_populated(frozen, "Yield Curve") or FORCE_OVERWRITE:
        log.info(f"  Compute Yield Curve (10Y - short rate)")
        log.info(f"    DEBUG: ten_y_pairs={len(ten_y_pairs) if ten_y_pairs else None}, short_pairs={len(short_pairs) if short_pairs else None}")
        if ten_y_pairs:
            log.info(f"    DEBUG: 10Y sample dates: {[d for d,v in ten_y_pairs[:3]]}")
        if short_pairs:
            log.info(f"    DEBUG: short rate sample dates: {[d for d,v in short_pairs[:3]]}")
        spread = compute_yield_curve(ten_y_pairs, short_pairs)
        if spread:
            frozen["Yield Curve"] = {"v": spread, "type": "line", "zeroLine": True}
            log.info(f"    OK ({len(spread)} points)")
            results["fetched"].append("Yield Curve")
        else:
            log.warning(f"    failed - missing 10Y or short rate data")
            results["failed"].append("Yield Curve")
    else:
        log.info(f"  SKIP    Yield Curve (already populated)")
        results["skipped"].append("Yield Curve")

    # Stock Market (Yahoo Finance)
    ticker = STOCK_TICKERS.get(code)
    if ticker:
        if not is_populated(frozen, "Stock Market YTD") or FORCE_OVERWRITE:
            log.info(f"  Fetch   Stock Market YTD  [{ticker}]")
            vals = fetch_stock_monthly(ticker)
            if vals:
                frozen["Stock Market YTD"] = {
                    "v": vals, "type": "line", "indexLabel": True
                }
                log.info(f"    OK ({len(vals)} points)")
                results["fetched"].append("Stock Market YTD")
            else:
                results["failed"].append("Stock Market YTD")
        else:
            log.info(f"  SKIP    Stock Market YTD (already populated)")
            results["skipped"].append("Stock Market YTD")

    # FRED daily series (Equity Vol, Corp Spread for countries that have them)
    for metric, series_id in DAILY_FRED_SERIES.get(code, {}).items():
        if not is_populated(frozen, metric) or FORCE_OVERWRITE:
            log.info(f"  Fetch   {metric}  [{series_id}]")
            vals = fetch_fx_monthly(series_id)
            if vals:
                frozen[metric] = {"v": vals, "type": "line"}
                log.info(f"    OK ({len(vals)} points)")
                results["fetched"].append(metric)
            else:
                results["failed"].append(metric)
        else:
            log.info(f"  SKIP    {metric} (already populated)")
            results["skipped"].append(metric)

    # Blank out void metrics - no free source exists for this country.
    # Write {"v": []} so the chart shows blank rather than stale data.
    for metric, exempt_codes in VOID_METRICS.items():
        if code not in exempt_codes:
            if frozen.get(metric, {}).get("v"):
                log.info(f"  BLANK   {metric} (no free source for {code})")
            frozen[metric] = {"v": []}

    # FX rate (FRED daily, resampled)
    fx_series = FX_FRED_SERIES.get(code)
    fx_label  = detect_fx_label(country_data, frozen, code)
    if fx_series and fx_label:
        if not is_populated(frozen, fx_label) or FORCE_OVERWRITE:
            log.info(f"  Fetch   {fx_label}  [{fx_series}]")
            vals = fetch_fx_monthly(fx_series)
            if vals:
                frozen[fx_label] = {"v": vals, "type": "line"}
                log.info(f"    OK ({len(vals)} points)")
                results["fetched"].append(fx_label)
            else:
                results["failed"].append(fx_label)
        else:
            log.info(f"  SKIP    {fx_label} (already populated)")
            results["skipped"].append(fx_label)

    # Blank out country-specific metrics with misleading partial data.
    # Runs AFTER the FX fetch so these voids always win over any fetched data.
    for metric in COUNTRY_VOID_METRICS.get(code, set()):
        if frozen.get(metric, {}).get("v"):
            log.info(f"  BLANK   {metric} (data quality void for {code})")
        frozen[metric] = {"v": []}

    # Budget Deficit (World Bank API - no key required)
    if not is_populated(frozen, "Budget Deficit") or FORCE_OVERWRITE:
        log.info(f"  Fetch   Budget Deficit  [World Bank GC.NLD.TOTL.GD.ZS]")
        vals = fetch_wb_budget_deficit(code)
        if vals:
            frozen["Budget Deficit"] = {"v": vals, "type": "bar", "annual": True}
            log.info(f"    OK ({len(vals)} points)")
            results["fetched"].append("Budget Deficit")
        else:
            results["failed"].append("Budget Deficit")
    else:
        log.info(f"  SKIP    Budget Deficit (already populated)")
        results["skipped"].append("Budget Deficit")

    # Current Account % GDP (World Bank API - no key required)
    if not is_populated(frozen, "Current Account") or FORCE_OVERWRITE:
        log.info(f"  Fetch   Current Account  [World Bank BN.CAB.XOKA.GD.ZS]")
        vals = fetch_wb_current_account(code)
        if vals:
            frozen["Current Account"] = {"v": vals, "type": "bar", "annual": True}
            log.info(f"    OK ({len(vals)} points)")
            results["fetched"].append("Current Account")
        else:
            results["failed"].append("Current Account")
    else:
        log.info(f"  SKIP    Current Account (already populated)")
        results["skipped"].append("Current Account")

    # Rename any wrongly stored "macro" FX entry to the correct label
    if "macro" in frozen and fx_label and fx_label != "macro":
        log.info(f"  Rename  'macro' -> '{fx_label}' in frozen historical")
        frozen[fx_label] = frozen.pop("macro")

    # Append 2026F forecast as the final point for all annual metrics.
    # The 'value' field in data.json holds the current year-end forecast.
    # Convention: the last point in every annual array is always the 2026F.
    ANNUAL_METRICS = ["GDP Growth", "Budget Deficit", "Current Account"]
    macro = country_data.get("metrics", {}).get("macro", {})
    for metric in ANNUAL_METRICS:
        if metric not in frozen or not frozen[metric].get("v"):
            continue
        val_str = macro.get(metric, {}).get("value", "")
        forecast = parse_forecast_value(val_str)
        if forecast is None:
            log.warning(f"  2026F append: could not parse value for {metric} ({val_str!r})")
            continue
        frozen[metric]["v"].append(forecast)
        log.info(f"  2026F append: {metric} += {forecast}")

    return results


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # Pre-flight checks
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

    # Support list, {countries: [...]}, or {countries: {CODE: {...}}}
    if isinstance(data, list):
        country_map = {c["code"]: c for c in data if "code" in c}
    elif isinstance(data, dict) and "countries" in data:
        raw = data["countries"]
        if isinstance(raw, dict):
            country_map = raw  # already keyed by country code
        else:
            country_map = {c["code"]: c for c in raw if "code" in c}
    else:
        sys.exit("\nERROR: Cannot find country list in data.json\n")

    run_order = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA",
                 "CHN", "IND", "ZAF", "BRA", "RUS"]

    totals = {"fetched": 0, "skipped": 0, "failed": 0, "failed_list": []}

    for code in run_order:
        if code not in country_map:
            log.warning(f"\n[{code}] not found in data.json - skipping")
            continue

        log.info(f"\n{'='*52}")
        log.info(f"  {code}")
        log.info(f"{'='*52}")

        results = process_country(code, country_map[code])

        totals["fetched"]  += len(results["fetched"])
        totals["skipped"]  += len(results["skipped"])
        totals["failed"]   += len(results["failed"])
        totals["failed_list"].extend(
            [f"{code}/{m}" for m in results["failed"]]
        )

    # Commodity historical
    process_commodities(data)

    # Write data.json back
    log.info(f"\nWriting {DATA_FILE} ...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info("Write complete.")

    # Summary
    log.info(f"\n{'='*52}")
    log.info("SUMMARY")
    log.info(f"{'='*52}")
    log.info(f"  Fetched : {totals['fetched']}")
    log.info(f"  Skipped : {totals['skipped']}  (already populated)")
    log.info(f"  Failed  : {totals['failed']}")
    if totals["failed_list"]:
        log.info("  Failed series:")
        for item in totals["failed_list"]:
            log.info(f"    - {item}")
        log.info("\n  Note: Some series may simply not exist on FRED for a given")
        log.info("  country. Check the series IDs in FRED_METRICS near the top")
        log.info("  of this file if you want to substitute alternatives.")

    log.info("\nNext steps:")
    log.info("  python3 build.py && git add -A && git commit -m 'Restore _frozen_historical'")


if __name__ == "__main__":
    main()
