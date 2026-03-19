"""
build_snapshot.py - Daily snapshot builder for MacroSnaps

Fetches all 14 metrics for 11 countries from FRED + Yahoo Finance,
computes derived metrics, assigns weather status, and outputs
snapshot.json matching the frontend's countries-data schema.

Usage:
    FRED_API_KEY=xxx python backend/build_snapshot.py
    FRED_API_KEY=xxx python backend/build_snapshot.py --output /path/to/snapshot.json
"""

import json
import os
import sys
import math
import time
import logging
import argparse
from datetime import datetime, date, timedelta
from statistics import stdev

import requests
import yfinance as yf

try:
    from imf_reader import weo
    HAS_IMF_READER = True
except ImportError:
    HAS_IMF_READER = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_snapshot")

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# ---------------------------------------------------------------------------
# Country configuration - FRED series IDs verified from backend/services/*_fetcher.py
# ---------------------------------------------------------------------------

COUNTRY_CONFIG = {
    "USA": {
        "name": "United States",
        "flag": "\U0001f1fa\U0001f1f8",
        "lat": 38.9,
        "lon": -77,
        "fx_key": "USD/DXY",
        "stock_symbol": "^GSPC",
        "fx_yahoo": None,           # USA uses FRED DXY index
        "fred": {
            "gdp_growth":     "A191RL1Q225SBEA",
            "inflation":      "CPIAUCSL",
            "unemployment":   "UNRATE",
            "policy_rate":    "FEDFUNDS",
            "bond_yield_10y": "DGS10",
            "bond_yield_2y":  "DGS2",
            "currency":       "DTWEXBGS",
            "current_account": "USAB6BLTT02STSAQ",
            "vix":            "VIXCLS",
        },
        "inflation_is_yoy": False,
        "rate_is_range": True,
        "fx_invert": False,
        "fx_decimals": 1,
    },
    "CAN": {
        "name": "Canada",
        "flag": "\U0001f1e8\U0001f1e6",
        "lat": 45.4,
        "lon": -75.7,
        "fx_key": "CAD/USD",
        "stock_symbol": "^GSPTSE",
        "fx_yahoo": "CADUSD=X",
        "fred": {
            "gdp_growth":     "NAEXKP01CAQ657S",
            "inflation":      "CPALTT01CAM659N",
            "unemployment":   "LRHUTTTTCAM156S",
            "policy_rate":    "IRSTCI01CAM156N",
            "bond_yield_10y": "IRLTLT01CAM156N",
            "currency":       "DEXCAUS",
            "current_account": "CANB6BLTT02STSAQ",
        },
        "inflation_is_yoy": True,
        "rate_is_range": False,
        "fx_invert": True,         # DEXCAUS is CAD per USD; we want USD per CAD
        "fx_decimals": 2,
    },
    "GBR": {
        "name": "United Kingdom",
        "flag": "\U0001f1ec\U0001f1e7",
        "lat": 51.5,
        "lon": -0.1,
        "fx_key": "GBP/USD",
        "stock_symbol": "^FTSE",
        "fx_yahoo": "GBPUSD=X",
        "fred": {
            "gdp_growth":     "NAEXKP01GBQ657S",
            "inflation":      "GBRCPIALLMINMEI",
            "unemployment":   "LRHUTTTTGBM156S",
            "policy_rate":    "IRSTCI01GBM156N",
            "bond_yield_10y": "IRLTLT01GBM156N",
            "currency":       "DEXUSUK",
            "current_account": "GBRB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXUSUK is USD per GBP - already correct
        "fx_decimals": 2,
    },
    "JPN": {
        "name": "Japan",
        "flag": "\U0001f1ef\U0001f1f5",
        "lat": 35.7,
        "lon": 139.7,
        "fx_key": "USD/JPY",
        "stock_symbol": "^N225",
        "fx_yahoo": "USDJPY=X",
        "fred": {
            "gdp_growth":     "NAEXKP01JPQ657S",
            # inflation: not available in FRED for Japan
            "unemployment":   "LRHUTTTTJPM156S",
            "policy_rate":    "IRSTCI01JPM156N",
            "bond_yield_10y": "IRLTLT01JPM156N",
            "currency":       "DEXJPUS",
            "current_account": "JPNB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXJPUS is JPY per USD - matches USD/JPY
        "fx_decimals": 1,
    },
    "DEU": {
        "name": "Germany",
        "flag": "\U0001f1e9\U0001f1ea",
        "lat": 52.5,
        "lon": 13.4,
        "fx_key": "EUR/USD",
        "stock_symbol": "^GDAXI",
        "fx_yahoo": "EURUSD=X",
        "fred": {
            "gdp_growth":     "NAEXKP01DEQ657S",
            "inflation":      "DEUCPIALLMINMEI",
            "unemployment":   "LRHUTTTTDEM156S",
            "policy_rate":    "IRSTCI01DEM156N",
            "bond_yield_10y": "IRLTLT01DEM156N",
            "currency":       "DEXUSEU",
            "current_account": "DEUB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXUSEU is USD per EUR - matches EUR/USD
        "fx_decimals": 2,
    },
    "FRA": {
        "name": "France",
        "flag": "\U0001f1eb\U0001f1f7",
        "lat": 48.9,
        "lon": 2.3,
        "fx_key": "EUR/USD",
        "stock_symbol": "^FCHI",
        "fx_yahoo": "EURUSD=X",
        "fred": {
            "gdp_growth":     "NAEXKP01FRQ657S",
            "inflation":      "FRACPIALLMINMEI",
            "unemployment":   "LRHUTTTTFRM156S",
            "policy_rate":    "IRSTCI01FRM156N",
            "bond_yield_10y": "IRLTLT01FRM156N",
            "currency":       "DEXUSEU",
            "current_account": "FRAB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,
        "fx_decimals": 2,
    },
    "ITA": {
        "name": "Italy",
        "flag": "\U0001f1ee\U0001f1f9",
        "lat": 41.9,
        "lon": 12.5,
        "fx_key": "EUR/USD",
        "stock_symbol": "FTSEMIB.MI",
        "fx_yahoo": "EURUSD=X",
        "fred": {
            "gdp_growth":     "NAEXKP01ITQ657S",
            "inflation":      "ITACPIALLMINMEI",
            "unemployment":   "LRHUTTTTITM156S",
            "policy_rate":    "IRSTCI01ITM156N",
            "bond_yield_10y": "IRLTLT01ITM156N",
            "currency":       "DEXUSEU",
            "current_account": "ITAB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,
        "fx_decimals": 2,
    },
    "CHN": {
        "name": "China",
        "flag": "\U0001f1e8\U0001f1f3",
        "lat": 39.9,
        "lon": 116.4,
        "fx_key": "USD/CNY",
        "stock_symbol": "000001.SS",
        "fx_yahoo": "USDCNY=X",
        "fred": {
            # gdp_growth: not available in FRED
            "inflation":      "CHNCPIALLMINMEI",
            # unemployment: not available in FRED
            "policy_rate":    "IRSTCI01CNM156N",
            # bond_yield_10y: not available in FRED
            "currency":       "DEXCHUS",
            "current_account": "CHNB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXCHUS is CNY per USD - matches USD/CNY
        "fx_decimals": 2,
    },
    "IND": {
        "name": "India",
        "flag": "\U0001f1ee\U0001f1f3",
        "lat": 28.6,
        "lon": 77.2,
        "fx_key": "USD/INR",
        "stock_symbol": "^BSESN",
        "fx_yahoo": "USDINR=X",
        "fred": {
            "gdp_growth":     "NAEXKP01INQ657S",
            "inflation":      "INDCPIALLMINMEI",
            # unemployment: not available in FRED
            "policy_rate":    "IRSTCI01INM156N",
            # bond_yield_10y: not available in FRED
            "currency":       "DEXINUS",
            "current_account": "INDB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXINUS is INR per USD - matches USD/INR
        "fx_decimals": 1,
    },
    "ZAF": {
        "name": "South Africa",
        "flag": "\U0001f1ff\U0001f1e6",
        "lat": -29.0,
        "lon": 24.0,
        "fx_key": "USD/ZAR",
        "stock_symbol": "^J203.JO",
        "fx_yahoo": "USDZAR=X",
        "fred": {
            "gdp_growth":     "NAEXKP01ZAQ657S",
            "inflation":      "ZAFCPIALLMINMEI",
            "unemployment":   "LRHUTTTTZAM156S",
            "policy_rate":    "IRSTCI01ZAM156N",
            "bond_yield_10y": "IRLTLT01ZAM156N",
            "currency":       "DEXSFUS",
            "current_account": "ZAFB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXSFUS is ZAR per USD - matches USD/ZAR
        "fx_decimals": 1,
    },
    "BRA": {
        "name": "Brazil",
        "flag": "\U0001f1e7\U0001f1f7",
        "lat": -15.8,
        "lon": -47.9,
        "fx_key": "USD/BRL",
        "stock_symbol": "^BVSP",
        "fx_yahoo": "USDBRL=X",
        "fred": {
            "gdp_growth":     "NAEXKP01BRQ657S",
            "inflation":      "BRACPIALLMINMEI",
            # unemployment: not available in FRED — uses fallback
            "policy_rate":    "IRSTCI01BRM156N",
            # bond_yield_10y: not available in FRED — uses fallback
            "currency":       "DEXBZUS",
            "current_account": "BRAB6BLTT02STSAQ",
        },
        "inflation_is_yoy": False,
        "rate_is_range": False,
        "fx_invert": False,        # DEXBZUS is BRL per USD — matches USD/BRL
        "fx_decimals": 2,
    },
}

# ---------------------------------------------------------------------------
# Hardcoded fallback values (from current frontend JSON)
# Used for metrics with no free API or known FRED gaps
# ---------------------------------------------------------------------------

FALLBACK = {
    "corp_spread": {
        "USA": 85, "CAN": 115, "GBR": 100, "JPN": 42,
        "DEU": 55, "FRA": 60, "ITA": 65, "CHN": 55, "IND": 75, "ZAF": 180, "BRA": 220,
    },
    "sov_cds": {
        "USA": 35, "CAN": 40, "GBR": 25, "JPN": 22,
        "DEU": 15, "FRA": 30, "ITA": 55, "CHN": 60, "IND": 95, "ZAF": 195, "BRA": 160,
    },
    "yield_curve": {
        "CAN": 15, "GBR": 10, "JPN": 53,
        "DEU": 30, "FRA": 38, "ITA": 62, "CHN": 46, "IND": 23, "ZAF": 85, "BRA": -145,
    },
    # Known FRED data gaps
    "inflation":      {"JPN": 2.8},
    "gdp_growth":     {"CHN": 5.2},
    "unemployment":   {"CHN": 5.1, "IND": 4.7, "BRA": 5.1},
    "bond_yield_10y": {"CHN": 2.56, "IND": 7.18, "BRA": 13.56},
}


# ---------------------------------------------------------------------------
# Commodity configuration - Yahoo Finance futures symbols
# ---------------------------------------------------------------------------

COMMODITY_CONFIG = [
    {"name": "WTI Crude",    "symbol": "CL", "yahoo": "CL=F",  "cat": "energy",      "unit": "$/bbl"},
    {"name": "Brent Crude",  "symbol": "BZ", "yahoo": "BZ=F",  "cat": "energy",      "unit": "$/bbl"},
    {"name": "Natural Gas",  "symbol": "NG", "yahoo": "NG=F",  "cat": "energy",      "unit": "$/mmBtu"},
    {"name": "Gold",         "symbol": "GC", "yahoo": "GC=F",  "cat": "metals",      "unit": "$/oz"},
    {"name": "Silver",       "symbol": "SI", "yahoo": "SI=F",  "cat": "metals",      "unit": "$/oz"},
    {"name": "Copper",       "symbol": "HG", "yahoo": "HG=F",  "cat": "metals",      "unit": "$/lb"},
    {"name": "Wheat",        "symbol": "ZW", "yahoo": "ZW=F",  "cat": "agriculture", "unit": "\u00a2/bu"},
    {"name": "Corn",         "symbol": "ZC", "yahoo": "ZC=F",  "cat": "agriculture", "unit": "\u00a2/bu"},
    {"name": "Soybeans",     "symbol": "ZS", "yahoo": "ZS=F",  "cat": "agriculture", "unit": "\u00a2/bu"},
]

# Fallback commodity prices (used if Yahoo fails)
COMMODITY_FALLBACK = {
    "CL=F": {"price": 71.24, "change": -1.8, "spark": [68,70,73,76,74,72,69,71,74,73,72,71],
             "annual": [79.61,94.88,94.05,97.98,93.17,48.66,43.29,50.80,65.23,56.99,39.68,67.99,94.53,77.61,75.89,71.24]},
    "BZ=F": {"price": 75.06, "change": -1.5, "spark": [72,74,77,80,78,76,73,75,78,77,76,75],
             "annual": [79.50,111.26,111.63,108.56,98.97,52.32,43.73,54.13,71.34,64.21,41.96,70.86,100.93,82.49,79.64,75.06]},
    "NG=F": {"price": 3.42, "change": 5.2, "spark": [2.1,2.3,2.0,2.4,2.8,3.1,2.9,3.0,3.2,3.3,3.1,3.4],
             "annual": [4.39,4.00,2.75,3.73,4.37,2.62,2.52,3.11,3.16,2.56,2.13,3.73,6.45,2.54,2.19,3.42]},
    "GC=F": {"price": 2918.40, "change": 1.2, "spark": [2640,2660,2700,2680,2720,2750,2780,2810,2830,2870,2890,2918],
             "annual": [1224.53,1571.52,1668.98,1411.23,1266.40,1160.06,1250.74,1257.15,1268.49,1392.60,1769.64,1798.61,1800.09,1943.28,2386.40,2918.40]},
    "SI=F": {"price": 32.56, "change": 0.8, "spark": [28.5,29.0,29.8,30.2,30.0,30.5,31.0,31.2,31.8,32.0,32.3,32.6],
             "annual": [20.19,35.12,31.15,23.79,19.08,15.68,17.14,17.05,15.71,16.21,20.69,25.14,21.73,23.35,28.27,32.56]},
    "HG=F": {"price": 4.38, "change": -0.6, "spark": [3.80,3.90,4.10,4.20,4.15,4.05,4.10,4.25,4.30,4.35,4.40,4.38],
             "annual": [3.42,4.00,3.61,3.32,3.11,2.49,2.21,2.80,2.96,2.72,2.80,4.23,3.99,3.85,4.15,4.38]},
    "ZW=F": {"price": 572, "change": -2.1, "spark": [620,610,595,580,590,600,585,570,575,580,578,572],
             "annual": [597,715,778,655,589,502,429,443,510,485,550,710,902,610,565,572]},
    "ZC=F": {"price": 448, "change": 0.3, "spark": [420,425,430,435,440,438,442,445,440,443,446,448],
             "annual": [396,657,629,498,386,367,352,358,363,387,384,545,679,485,432,448]},
    "ZS=F": {"price": 1042, "change": -0.9, "spark": [1080,1070,1060,1055,1065,1050,1040,1045,1050,1048,1045,1042],
             "annual": [989,1243,1461,1303,1028,889,965,955,904,886,1027,1396,1488,1291,1098,1042]},
}


# ---------------------------------------------------------------------------
# Google Sheet forecasts (absolute truth for macro forecasts)
# ---------------------------------------------------------------------------

GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj"
    "/pub?gid=0&single=true&output=csv"
)

# Mapping from CSV column names to our metric names and formatting
FORECAST_COLUMNS = {
    "GDP_Growth_2026":     "GDP Growth",
    "Inflation_2026":      "Inflation (CPI)",
    "Unemployment_2026":   "Unemployment",
    "Budget_Deficit_2026": "Budget Deficit",
    "Current_Account_2026":"Current Account",
}


def fetch_forecasts():
    """
    Fetch Ralph's forecast spreadsheet from Google Sheets (published CSV).
    Returns {country_code: {metric_name: float_value}} or {} on failure.
    Google Sheet is absolute truth for macro forecasts.
    """
    import csv
    import io

    try:
        resp = requests.get(GOOGLE_SHEET_CSV_URL, timeout=15)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        forecasts = {}
        for row in reader:
            code = row.get("Country", "").strip()
            if not code or code not in COUNTRY_CONFIG:
                continue
            fc = {}
            for csv_col, metric_name in FORECAST_COLUMNS.items():
                raw = row.get(csv_col, "").strip()
                if raw:
                    try:
                        fc[metric_name] = float(raw)
                    except ValueError:
                        pass
            if fc:
                forecasts[code] = fc
        log.info("Google Sheet forecasts loaded: %d countries", len(forecasts))
        return forecasts
    except Exception as e:
        log.warning("Google Sheet fetch failed: %s - using no forecasts", e)
        return {}


def format_forecast_macro(forecasts_for_country, rate_val, country_code):
    """
    Build the metrics.macro dict using Google Sheet forecast values.
    Policy Rate comes from FRED (not in the spreadsheet).
    """
    fc = forecasts_for_country

    return {
        "GDP Growth":      fmt_pct_signed(fc.get("GDP Growth")),
        "Inflation (CPI)": fmt_pct(fc.get("Inflation (CPI)")),
        "Unemployment":    fmt_pct(fc.get("Unemployment")),
        "Budget Deficit":  fmt_pct_gdp(fc.get("Budget Deficit")),
        "Current Account": fmt_pct_gdp(fc.get("Current Account")),
        "Policy Rate":     fmt_rate(rate_val, country_code),
    }

def fetch_fred(series_id, days_back=730):
    """Fetch a single FRED series. Returns [(date, float)] or [] on error."""
    if not series_id or not FRED_API_KEY:
        return []

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date.isoformat(),
        "observation_end": end_date.isoformat(),
    }

    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        obs = []
        for o in data.get("observations", []):
            if o["value"] == ".":
                continue
            d = datetime.strptime(o["date"], "%Y-%m-%d").date()
            obs.append((d, float(o["value"])))
        return obs
    except Exception as e:
        log.warning("FRED fetch failed for %s: %s", series_id, e)
        return []


def fetch_fred_batch(series_dict, days_back=730):
    """Fetch multiple FRED series. Returns {key: [(date, val)]}."""
    results = {}
    for key, sid in series_dict.items():
        results[key] = fetch_fred(sid, days_back)
        if sid:
            time.sleep(0.2)  # stay under FRED rate limit
    return results


def fetch_yahoo(symbol, days_back=60):
    """Fetch daily closes from Yahoo Finance. Returns [(date, close)] or []."""
    if not symbol:
        return []
    try:
        end = datetime.now()
        start = end - timedelta(days=days_back)
        hist = yf.Ticker(symbol).history(start=start, end=end)
        obs = []
        for ts, row in hist.iterrows():
            obs.append((ts.date(), float(row["Close"])))
        return obs
    except Exception as e:
        log.warning("Yahoo fetch failed for %s: %s", symbol, e)
        return []


def fetch_weo_budget(country_code):
    """Fetch budget balance (% GDP) from IMF WEO. Returns [(date, float)]."""
    if not HAS_IMF_READER:
        log.info("imf_reader not installed - skipping WEO budget for %s", country_code)
        return []
    try:
        df = weo.fetch_data()
        budget = df[df["CONCEPT_CODE"] == "GGXCNL_NGDP"]
        country = budget[budget["REF_AREA_CODE"] == country_code]
        if country.empty:
            return []
        country = country[country["TIME_PERIOD"].astype(int) <= 2025]
        country = country[country["TIME_PERIOD"].astype(int) >= 2020]
        results = []
        for _, row in country.iterrows():
            year = int(row["TIME_PERIOD"])
            results.append((date(year, 1, 1), float(row["OBS_VALUE"])))
        results.sort(key=lambda x: x[0])
        return results
    except Exception as e:
        log.warning("WEO fetch failed for %s: %s", country_code, e)
        return []


# ===================================================================
# Computation functions
# ===================================================================

def latest_value(obs):
    """Return (value, date) of the most recent observation, or (None, None)."""
    if not obs:
        return None, None
    obs_sorted = sorted(obs, key=lambda x: x[0])
    d, v = obs_sorted[-1]
    return v, d


def compute_yoy_inflation(obs):
    """Compute YoY % change from a CPI index series. Returns float or None."""
    if not obs or len(obs) < 2:
        return None

    obs_sorted = sorted(obs, key=lambda x: x[0])
    latest_date, latest_val = obs_sorted[-1]

    # Target: 12 months ago
    try:
        target = date(latest_date.year - 1, latest_date.month, latest_date.day)
    except ValueError:
        target = date(latest_date.year - 1, latest_date.month, 28)

    # Find closest within 45-day window
    best_val, best_dist = None, 999
    for d, v in obs_sorted:
        dist = abs((d - target).days)
        if dist <= 45 and dist < best_dist:
            best_val = v
            best_dist = dist

    if best_val is None or best_val == 0:
        return None

    return round(((latest_val - best_val) / best_val) * 100, 1)


def compute_ytd_return(prices):
    """Compute YTD % return from daily price series. Returns float or None."""
    if not prices:
        return None

    prices_sorted = sorted(prices, key=lambda x: x[0])
    latest_price = prices_sorted[-1][1]
    current_year = datetime.now().year

    # Find first available price in January of current year
    jan_price = None
    for d, p in prices_sorted:
        if d.year == current_year and d.month == 1:
            jan_price = p
            break

    # Fallback: last trading day of previous year
    if jan_price is None:
        for d, p in reversed(prices_sorted):
            if d.year == current_year - 1:
                jan_price = p
                break

    if jan_price is None or jan_price == 0:
        return None

    return round(((latest_price - jan_price) / jan_price) * 100, 1)


def compute_realized_vol(prices, window=30):
    """Compute annualized realized vol from daily closes. Returns % or None."""
    if not prices or len(prices) < window + 1:
        return None

    prices_sorted = sorted(prices, key=lambda x: x[0])
    closes = [p for _, p in prices_sorted[-(window + 1):]]

    # Daily log returns
    returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] <= 0 or closes[i] <= 0:
            continue
        returns.append(math.log(closes[i] / closes[i - 1]))

    if len(returns) < 5:
        return None

    vol = stdev(returns) * math.sqrt(252) * 100
    return round(vol, 1)


def compute_yield_curve(bond_10y_obs, bond_2y_obs):
    """Compute 10Y-2Y spread in basis points. Returns float or None."""
    val_10y, _ = latest_value(bond_10y_obs)
    val_2y, _ = latest_value(bond_2y_obs)
    if val_10y is None or val_2y is None:
        return None
    return round((val_10y - val_2y) * 100, 0)


# ===================================================================
# Formatting functions - output strings matching frontend exactly
# ===================================================================

def fmt_pct_signed(val, dec=1):
    """'+2.8%' or '-0.1%'. Returns '-' if None."""
    if val is None:
        return "-"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.{dec}f}%"


def fmt_pct(val, dec=1):
    """'3.1%' (no explicit + sign). Returns '-' if None."""
    if val is None:
        return "-"
    return f"{val:.{dec}f}%"


def fmt_pct_gdp(val):
    """'-6.2% GDP' with sign. Returns '-' if None."""
    if val is None:
        return "-"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}% GDP"


def fmt_rate(val, country_code):
    """
    Policy rate. USA shows range '5.25-5.50%'.
    Others show '4.50%'. Returns '-' if None.
    """
    if val is None:
        return "-"
    if country_code == "USA":
        lower = math.floor(val * 4) / 4
        upper = lower + 0.25
        return f"{lower:.2f}-{upper:.2f}%"
    return f"{val:.2f}%"


def fmt_bps(val, signed=False):
    """'85bps' or '+8bps'. Returns '-' if None."""
    if val is None:
        return "-"
    v = int(round(val))
    if signed:
        sign = "+" if v >= 0 else ""
        return f"{sign}{v}bps"
    return f"{v}bps"


def fmt_vol(val):
    """'~16'. Returns '-' if None."""
    if val is None:
        return "-"
    return f"~{int(round(val))}"


def fmt_fx(val, country_code):
    """Country-specific FX formatting. Returns '-' if None."""
    if val is None:
        return "-"
    dec = COUNTRY_CONFIG[country_code]["fx_decimals"]
    return f"{val:.{dec}f}"


def fmt_bond_yield(val):
    """'4.28%' with 2 decimal places. Returns '-' if None."""
    if val is None:
        return "-"
    return f"{val:.2f}%"


# ===================================================================
# Weather assignment
# ===================================================================

def assign_weather(gdp=None, inflation=None, unemployment=None, stock_ytd=None):
    """
    Assign weather icon based on economic conditions.
    Returns one of: sunny, cloudy, stormy (emoji strings).
    """
    score = 0
    counted = 0

    if gdp is not None:
        counted += 1
        if gdp > 2:
            score += 1
        elif gdp < 0:
            score -= 1

    if inflation is not None:
        counted += 1
        if 1 <= inflation <= 3:
            score += 1
        elif inflation > 5 or inflation < 0:
            score -= 1

    if unemployment is not None:
        counted += 1
        if unemployment < 5:
            score += 1
        elif unemployment > 7:
            score -= 1

    if stock_ytd is not None:
        counted += 1
        if stock_ytd > 5:
            score += 1
        elif stock_ytd < 0:
            score -= 1

    if score >= 2:
        return "\u2600\ufe0f"    # sunny
    elif score <= -1:
        return "\u26c8\ufe0f"    # stormy
    else:
        return "\u2601\ufe0f"    # cloudy


# ===================================================================
# Historical data - full time series from 2010
# ===================================================================

HIST_START = "2010-01-01"
HIST_ANNUAL_START = 2010
HIST_ANNUAL_END = 2025
HIST_MONTHLY_START_YEAR = 2011
HIST_MONTHLY_END_YEAR = 2025


def fetch_fred_historical(series_id):
    """Fetch FRED series from 2010-01-01 to present. Returns [(date, float)]."""
    if not series_id or not FRED_API_KEY:
        return []

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": HIST_START,
        "observation_end": datetime.now().date().isoformat(),
    }

    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        obs = []
        for o in data.get("observations", []):
            if o["value"] == ".":
                continue
            d = datetime.strptime(o["date"], "%Y-%m-%d").date()
            obs.append((d, float(o["value"])))
        return obs
    except Exception as e:
        log.warning("FRED historical fetch failed for %s: %s", series_id, e)
        return []


def fetch_yahoo_historical(symbol, start="2011-01-01"):
    """Fetch Yahoo Finance daily prices from start date. Returns [(date, close)]."""
    if not symbol:
        return []
    try:
        hist = yf.Ticker(symbol).history(start=start, end=datetime.now().strftime("%Y-%m-%d"))
        obs = []
        for ts, row in hist.iterrows():
            obs.append((ts.date(), float(row["Close"])))
        return obs
    except Exception as e:
        log.warning("Yahoo historical fetch failed for %s: %s", symbol, e)
        return []


def _group_by_month(obs):
    """Group observations by (year, month). Returns {(year, month): [values]}."""
    groups = {}
    for d, v in obs:
        key = (d.year, d.month)
        groups.setdefault(key, []).append(v)
    return groups


def _group_by_year(obs):
    """Group observations by year. Returns {year: [values]}."""
    groups = {}
    for d, v in obs:
        groups.setdefault(d.year, []).append(v)
    return groups


def resample_monthly_avg(obs):
    """Daily/irregular observations -> monthly averages. Returns [(year, month, avg)]."""
    groups = _group_by_month(obs)
    result = []
    for (y, m) in sorted(groups):
        vals = groups[(y, m)]
        result.append((y, m, round(sum(vals) / len(vals), 2)))
    return result


def resample_monthly_last(obs):
    """Daily observations -> last value per month. Returns [(year, month, value)]."""
    groups = {}
    for d, v in sorted(obs, key=lambda x: x[0]):
        groups[(d.year, d.month)] = v
    return [(y, m, v) for (y, m), v in sorted(groups.items())]


def resample_annual_last(obs):
    """Observations -> last value per year. Returns [(year, value)]."""
    groups = {}
    for d, v in sorted(obs, key=lambda x: x[0]):
        groups[d.year] = v
    return [(y, v) for y, v in sorted(groups.items())]


def resample_annual_avg(obs):
    """Observations -> annual averages. Returns [(year, avg)]."""
    groups = _group_by_year(obs)
    return [(y, round(sum(vals) / len(vals), 2)) for y, vals in sorted(groups.items())]


def compute_monthly_yoy_series(obs):
    """
    From monthly CPI index observations, compute YoY% for each month.
    Returns [(year, month, yoy_pct)].
    """
    monthly = _group_by_month(obs)
    # Average each month to get single value
    monthly_avg = {}
    for (y, m), vals in monthly.items():
        monthly_avg[(y, m)] = sum(vals) / len(vals)

    result = []
    for (y, m) in sorted(monthly_avg):
        prev_key = (y - 1, m)
        if prev_key in monthly_avg and monthly_avg[prev_key] != 0:
            yoy = ((monthly_avg[(y, m)] - monthly_avg[prev_key]) / monthly_avg[prev_key]) * 100
            result.append((y, m, round(yoy, 1)))
    return result


def compute_monthly_vol_series(daily_prices, window=21):
    """
    Compute monthly realized vol from daily prices.
    For each month, compute annualized vol from daily log returns.
    Returns [(year, month, vol_pct)].
    """
    if not daily_prices or len(daily_prices) < window + 5:
        return []

    sorted_prices = sorted(daily_prices, key=lambda x: x[0])

    # Compute daily log returns
    returns_by_month = {}
    for i in range(1, len(sorted_prices)):
        d_prev, p_prev = sorted_prices[i - 1]
        d_curr, p_curr = sorted_prices[i]
        if p_prev <= 0 or p_curr <= 0:
            continue
        lr = math.log(p_curr / p_prev)
        key = (d_curr.year, d_curr.month)
        returns_by_month.setdefault(key, []).append(lr)

    result = []
    for (y, m) in sorted(returns_by_month):
        rets = returns_by_month[(y, m)]
        if len(rets) >= 10:
            vol = stdev(rets) * math.sqrt(252) * 100
            result.append((y, m, round(vol, 1)))
    return result


def monthly_to_array(monthly_vals, start_year=None, end_year=None):
    """
    Convert [(year, month, value)] to flat array aligned from start.
    Returns array of values, trimmed to available range.
    """
    if not monthly_vals:
        return []
    sy = start_year or HIST_MONTHLY_START_YEAR
    ey = end_year or HIST_MONTHLY_END_YEAR

    # Filter to range
    filtered = [(y, m, v) for y, m, v in monthly_vals if sy <= y <= ey]
    if not filtered:
        return []

    # Build dense array from first available month to last
    first_y, first_m = filtered[0][0], filtered[0][1]
    last_y, last_m = filtered[-1][0], filtered[-1][1]

    lookup = {(y, m): v for y, m, v in filtered}
    result = []
    y, m = first_y, first_m
    while (y, m) <= (last_y, last_m):
        result.append(lookup.get((y, m)))
        m += 1
        if m > 12:
            m = 1
            y += 1

    # Replace None with last known value (forward fill) for cleaner charts
    for i in range(1, len(result)):
        if result[i] is None:
            result[i] = result[i - 1]

    # Drop leading Nones
    while result and result[0] is None:
        result.pop(0)

    return result


def annual_to_array(annual_vals, start_year=None, end_year=None):
    """
    Convert [(year, value)] to flat array aligned from start.
    Returns array of values, trimmed to available range.
    """
    if not annual_vals:
        return []
    sy = start_year or HIST_ANNUAL_START
    ey = end_year or HIST_ANNUAL_END

    filtered = [(y, v) for y, v in annual_vals if sy <= y <= ey]
    if not filtered:
        return []

    first_y = filtered[0][0]
    last_y = filtered[-1][0]

    lookup = {y: v for y, v in filtered}
    result = []
    for y in range(first_y, last_y + 1):
        result.append(lookup.get(y))

    # Forward fill None gaps
    for i in range(1, len(result)):
        if result[i] is None:
            result[i] = result[i - 1]

    while result and result[0] is None:
        result.pop(0)

    return result


def build_historical_data(code, cfg):
    """
    Build the complete historical data object for one country.
    Fetches full FRED + Yahoo time series from 2010 and processes into
    the format the frontend charts expect.

    Returns dict matching: {metricName: {v: [...], type: "line"|"bar", annual?: true, zeroLine?: true}}
    """
    log.info("  [%s] Fetching historical data...", code)
    historical = {}
    fred_series = cfg["fred"]

    # --- FRED historical fetches ---
    fred_hist = {}
    for key, sid in fred_series.items():
        fred_hist[key] = fetch_fred_historical(sid)
        if sid:
            time.sleep(0.15)

    # --- Yahoo historical fetches ---
    log.info("  [%s] Fetching historical stock prices...", code)
    stock_hist = fetch_yahoo_historical(cfg["stock_symbol"], start="2011-01-01")

    fx_yahoo = cfg.get("fx_yahoo")
    fx_hist = fetch_yahoo_historical(fx_yahoo, start="2011-01-01") if fx_yahoo else []

    # =================================================================
    # GDP Growth (annual, bar chart)
    # =================================================================
    gdp_obs = fred_hist.get("gdp_growth", [])
    if gdp_obs:
        # Quarterly QoQ annualized -> take annual average
        gdp_annual = resample_annual_avg(gdp_obs)
        gdp_arr = annual_to_array(gdp_annual)
        if gdp_arr:
            historical["GDP Growth"] = {"v": gdp_arr, "annual": True, "type": "bar"}

    # =================================================================
    # Inflation CPI (monthly, line chart)
    # =================================================================
    inf_obs = fred_hist.get("inflation", [])
    if inf_obs:
        if cfg["inflation_is_yoy"]:
            # Already YoY - just resample to monthly
            inf_monthly = resample_monthly_last(inf_obs)
            inf_arr = monthly_to_array([(y, m, v) for y, m, v in inf_monthly])
        else:
            # CPI index -> compute YoY
            inf_yoy = compute_monthly_yoy_series(inf_obs)
            inf_arr = monthly_to_array(inf_yoy)
        if inf_arr:
            historical["Inflation (CPI)"] = {"v": inf_arr, "type": "line"}

    # =================================================================
    # Unemployment (monthly, line chart)
    # =================================================================
    unemp_obs = fred_hist.get("unemployment", [])
    if unemp_obs:
        unemp_monthly = resample_monthly_last(unemp_obs)
        unemp_arr = monthly_to_array([(y, m, v) for y, m, v in unemp_monthly])
        if unemp_arr:
            historical["Unemployment"] = {"v": unemp_arr, "type": "line"}

    # =================================================================
    # Budget Deficit (annual, bar chart) - from WEO
    # =================================================================
    if HAS_IMF_READER:
        try:
            df = weo.fetch_data()
            budget = df[df["CONCEPT_CODE"] == "GGXCNL_NGDP"]
            country_budget = budget[budget["REF_AREA_CODE"] == code]
            if not country_budget.empty:
                budget_pairs = []
                for _, row in country_budget.iterrows():
                    yr = int(row["TIME_PERIOD"])
                    if HIST_ANNUAL_START <= yr <= HIST_ANNUAL_END:
                        budget_pairs.append((yr, round(float(row["OBS_VALUE"]), 1)))
                budget_pairs.sort()
                budget_arr = annual_to_array(budget_pairs)
                if budget_arr:
                    historical["Budget Deficit"] = {"v": budget_arr, "annual": True, "type": "bar"}
        except Exception as e:
            log.warning("  [%s] WEO historical budget fetch failed: %s", code, e)

    # =================================================================
    # Current Account (annual, bar chart)
    # =================================================================
    ca_obs = fred_hist.get("current_account", [])
    if ca_obs:
        ca_annual = resample_annual_last(ca_obs)
        ca_arr = annual_to_array(ca_annual)
        if ca_arr:
            historical["Current Account"] = {"v": ca_arr, "annual": True, "type": "bar"}

    # =================================================================
    # Policy Rate (annual, line chart)
    # =================================================================
    rate_obs = fred_hist.get("policy_rate", [])
    if rate_obs:
        rate_annual = resample_annual_last(rate_obs)
        rate_arr = annual_to_array(rate_annual)
        if rate_arr:
            historical["Policy Rate"] = {"v": rate_arr, "annual": True, "type": "line"}

    # =================================================================
    # Stock Market (monthly levels, line chart)
    # =================================================================
    if stock_hist:
        stock_monthly = resample_monthly_last(stock_hist)
        stock_arr = monthly_to_array([(y, m, round(v, 0)) for y, m, v in stock_monthly])
        if stock_arr:
            historical["Stock Market YTD"] = {"v": stock_arr, "type": "line"}

    # =================================================================
    # Equity Vol (monthly, line chart)
    # =================================================================
    if code == "USA":
        vix_obs = fred_hist.get("vix", [])
        if vix_obs:
            vix_monthly = resample_monthly_avg(vix_obs)
            vix_arr = monthly_to_array([(y, m, v) for y, m, v in vix_monthly])
            if vix_arr:
                historical["Equity Vol"] = {"v": vix_arr, "type": "line"}
    elif stock_hist:
        eq_vol = compute_monthly_vol_series(stock_hist)
        eq_vol_arr = monthly_to_array(eq_vol)
        if eq_vol_arr:
            historical["Equity Vol"] = {"v": eq_vol_arr, "type": "line"}

    # =================================================================
    # 10Y Bond Yield (monthly, line chart)
    # =================================================================
    bond_obs = fred_hist.get("bond_yield_10y", [])
    if bond_obs:
        bond_monthly = resample_monthly_avg(bond_obs)
        bond_arr = monthly_to_array([(y, m, v) for y, m, v in bond_monthly])
        if bond_arr:
            historical["10Y Bond Yield"] = {"v": bond_arr, "type": "line"}

    # =================================================================
    # Yield Curve (monthly, line chart with zero line)
    # =================================================================
    if code == "USA":
        bond10_obs = fred_hist.get("bond_yield_10y", [])
        bond2_obs = fred_hist.get("bond_yield_2y", [])
        if bond10_obs and bond2_obs:
            b10_monthly = {(y, m): v for y, m, v in resample_monthly_avg(bond10_obs)}
            b2_monthly = {(y, m): v for y, m, v in resample_monthly_avg(bond2_obs)}
            yc_monthly = []
            for key in sorted(set(b10_monthly) & set(b2_monthly)):
                spread = round((b10_monthly[key] - b2_monthly[key]) * 100, 0)
                yc_monthly.append((key[0], key[1], spread))
            yc_arr = monthly_to_array(yc_monthly)
            if yc_arr:
                historical["Yield Curve"] = {"v": yc_arr, "type": "line", "zeroLine": True}

    # =================================================================
    # FX Rate (monthly, line chart)
    # =================================================================
    fx_key = cfg["fx_key"]
    fx_obs = fred_hist.get("currency", [])
    if fx_obs:
        # Apply inversion if needed
        if cfg.get("fx_invert"):
            fx_obs = [(d, round(1.0 / v, cfg["fx_decimals"] + 2)) for d, v in fx_obs if v != 0]
        fx_monthly = resample_monthly_avg(fx_obs)
        fx_arr = monthly_to_array([(y, m, round(v, cfg["fx_decimals"])) for y, m, v in fx_monthly])
        if fx_arr:
            historical[fx_key] = {"v": fx_arr, "type": "line"}

    # =================================================================
    # FX Vol (monthly, line chart)
    # =================================================================
    if code == "USA":
        # Use FRED DXY daily data
        dxy_obs = fred_hist.get("currency", [])
        if dxy_obs:
            fxvol_series = compute_monthly_vol_series(dxy_obs)
            fxvol_arr = monthly_to_array(fxvol_series)
            if fxvol_arr:
                historical["FX Vol"] = {"v": fxvol_arr, "type": "line"}
    elif fx_hist:
        fxvol_series = compute_monthly_vol_series(fx_hist)
        fxvol_arr = monthly_to_array(fxvol_series)
        if fxvol_arr:
            historical["FX Vol"] = {"v": fxvol_arr, "type": "line"}

    # Corp Spread and Sov CDS: no free historical source
    # Omitted - frontend shows "No historical data" gracefully

    log.info("  [%s] Historical data: %d metrics built", code, len(historical))
    return historical if historical else None


# ===================================================================
# Core: build one country
# ===================================================================

def _fallback(metric_key, country_code, prev_snapshot):
    """Try previous snapshot, then hardcoded fallback. Returns (value, source)."""
    # Tier 1: previous snapshot carry-forward
    if prev_snapshot:
        prev_country = prev_snapshot.get("countries", {}).get(country_code)
        if prev_country:
            # Try to find the raw metric in data_freshness to get the numeric value
            # But for simplicity, we can't reverse-parse formatted strings easily
            pass

    # Tier 2: hardcoded fallback
    fb = FALLBACK.get(metric_key, {})
    if isinstance(fb, dict) and country_code in fb:
        return fb[country_code], "fallback"

    return None, "missing"


def build_country(code, cfg, prev_snapshot, skip_historical=False, forecasts=None):
    """Build one country object matching the frontend schema."""
    if forecasts is None:
        forecasts = {}
    freshness = {}
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def record(metric, value, obs_date, source):
        freshness[metric] = {
            "source": source,
            "as_of": obs_date.isoformat() if obs_date else None,
            "fetched_at": now_str if source in ("fred", "yahoo", "weo") else None,
        }
        return value

    # --- Fetch FRED data ---
    log.info("  [%s] Fetching FRED data...", code)
    fred = fetch_fred_batch(cfg["fred"])

    # --- Fetch Yahoo stock (400 days for YTD calc) ---
    log.info("  [%s] Fetching stock prices (%s)...", code, cfg["stock_symbol"])
    stock_prices = fetch_yahoo(cfg["stock_symbol"], days_back=400)

    # --- Fetch Yahoo FX (60 days for vol) ---
    fx_yahoo = cfg.get("fx_yahoo")
    fx_prices = fetch_yahoo(fx_yahoo, days_back=60) if fx_yahoo else []

    # --- Fetch WEO budget ---
    log.info("  [%s] Fetching WEO budget...", code)
    weo_budget = fetch_weo_budget(code)

    # =================================================================
    # Extract raw values
    # =================================================================

    # GDP Growth
    gdp_val, gdp_date = latest_value(fred.get("gdp_growth", []))
    if gdp_val is None:
        gdp_val, gdp_src = _fallback("gdp_growth", code, prev_snapshot)
    else:
        gdp_src = "fred"
    record("gdp_growth", gdp_val, gdp_date, gdp_src)

    # Inflation
    inf_obs = fred.get("inflation", [])
    if cfg["inflation_is_yoy"]:
        inf_val, inf_date = latest_value(inf_obs)
        inf_src = "fred" if inf_val is not None else None
    else:
        inf_val = compute_yoy_inflation(inf_obs)
        _, inf_date = latest_value(inf_obs)
        inf_src = "fred" if inf_val is not None else None
    if inf_val is None:
        inf_val, inf_src = _fallback("inflation", code, prev_snapshot)
        inf_date = None
    record("inflation", inf_val, inf_date, inf_src or "missing")

    # Unemployment
    unemp_val, unemp_date = latest_value(fred.get("unemployment", []))
    if unemp_val is None:
        unemp_val, unemp_src = _fallback("unemployment", code, prev_snapshot)
    else:
        unemp_src = "fred"
    record("unemployment", unemp_val, unemp_date, unemp_src)

    # Budget Deficit (from WEO)
    budget_val, budget_date = latest_value(weo_budget)
    budget_src = "weo" if budget_val is not None else "missing"
    if budget_val is None:
        budget_val, budget_src = _fallback("budget_deficit", code, prev_snapshot)
    record("budget_deficit", budget_val, budget_date, budget_src)

    # Current Account
    ca_val, ca_date = latest_value(fred.get("current_account", []))
    if ca_val is None:
        ca_val, ca_src = _fallback("current_account", code, prev_snapshot)
    else:
        ca_src = "fred"
    record("current_account", ca_val, ca_date, ca_src)

    # Policy Rate
    rate_val, rate_date = latest_value(fred.get("policy_rate", []))
    if rate_val is None:
        rate_val, rate_src = _fallback("policy_rate", code, prev_snapshot)
    else:
        rate_src = "fred"
    record("policy_rate", rate_val, rate_date, rate_src)

    # Stock Market YTD
    stock_ytd = compute_ytd_return(stock_prices)
    _, stock_date = latest_value(stock_prices)
    stock_src = "yahoo" if stock_ytd is not None else "missing"
    record("stock_ytd", stock_ytd, stock_date, stock_src)

    # Equity Vol
    if code == "USA":
        eq_vol_val, eq_vol_date = latest_value(fred.get("vix", []))
        eq_vol_src = "fred" if eq_vol_val is not None else "missing"
    else:
        eq_vol_val = compute_realized_vol(stock_prices)
        _, eq_vol_date = latest_value(stock_prices)
        eq_vol_src = "yahoo" if eq_vol_val is not None else "missing"
    record("equity_vol", eq_vol_val, eq_vol_date, eq_vol_src)

    # 10Y Bond Yield
    bond_val, bond_date = latest_value(fred.get("bond_yield_10y", []))
    if bond_val is None:
        bond_val, bond_src = _fallback("bond_yield_10y", code, prev_snapshot)
    else:
        bond_src = "fred"
    record("bond_yield_10y", bond_val, bond_date, bond_src)

    # Yield Curve
    if code == "USA":
        yc_val = compute_yield_curve(
            fred.get("bond_yield_10y", []),
            fred.get("bond_yield_2y", []),
        )
        yc_src = "fred" if yc_val is not None else "missing"
    else:
        yc_val, yc_src = _fallback("yield_curve", code, prev_snapshot)
    record("yield_curve", yc_val, bond_date, yc_src)

    # Corp Spread (always fallback - no free API)
    cs_val = FALLBACK["corp_spread"].get(code)
    record("corp_spread", cs_val, None, "fallback")

    # Sov CDS (always fallback - no free API)
    cds_val = FALLBACK["sov_cds"].get(code)
    record("sov_cds", cds_val, None, "fallback")

    # FX rate
    fx_val, fx_date = latest_value(fred.get("currency", []))
    fx_src = "fred"
    if fx_val is not None and cfg.get("fx_invert"):
        # FRED DEXCAUS gives CAD per USD; invert to get USD per CAD
        fx_val = round(1.0 / fx_val, cfg["fx_decimals"] + 2)
    if fx_val is None:
        # Try Yahoo FX as fallback (already in correct direction)
        fx_val, fx_date = latest_value(fx_prices)
        fx_src = "yahoo" if fx_val is not None else "missing"
    record("fx_rate", fx_val, fx_date, fx_src)

    # FX Vol
    # For USA, compute vol from FRED DXY daily data
    if code == "USA":
        dxy_obs = fred.get("currency", [])
        fxvol_val = compute_realized_vol(dxy_obs) if len(dxy_obs) > 30 else None
    else:
        fxvol_val = compute_realized_vol(fx_prices)
    fxvol_src = "yahoo" if fxvol_val is not None else "missing"
    if code == "USA" and fxvol_val is not None:
        fxvol_src = "fred"
    record("fx_vol", fxvol_val, fx_date, fxvol_src)

    # =================================================================
    # Weather
    # =================================================================
    weather = assign_weather(
        gdp=gdp_val,
        inflation=inf_val,
        unemployment=unemp_val,
        stock_ytd=stock_ytd,
    )

    # =================================================================
    # Format metrics
    # =================================================================
    # If Google Sheet forecasts are available, use them for macro section.
    # Google Sheet is absolute truth for macro forecasts.
    if forecasts:
        macro = format_forecast_macro(forecasts, rate_val, code)
    else:
        macro = {
            "GDP Growth": fmt_pct_signed(gdp_val),
            "Inflation (CPI)": fmt_pct(inf_val),
            "Unemployment": fmt_pct(unemp_val),
            "Budget Deficit": fmt_pct_gdp(budget_val),
            "Current Account": fmt_pct_gdp(ca_val),
            "Policy Rate": fmt_rate(rate_val, code),
        }

    market = {
        "Stock Market YTD": fmt_pct_signed(stock_ytd),
        "Equity Vol": fmt_vol(eq_vol_val),
        "10Y Bond Yield": fmt_bond_yield(bond_val),
        "Yield Curve": fmt_bps(yc_val, signed=True),
        "Corp Spread": fmt_bps(cs_val),
        "Sov CDS": fmt_bps(cds_val),
        cfg["fx_key"]: fmt_fx(fx_val, code),
        "FX Vol": fmt_pct(fxvol_val),
    }

    # =================================================================
    # Carry forward non-metric fields from previous snapshot
    # =================================================================
    prev = {}
    if prev_snapshot:
        prev = prev_snapshot.get("countries", {}).get(code, {})

    # =================================================================
    # Historical data from 2010
    # =================================================================
    if skip_historical:
        hist_data = prev.get("historical", None)
    else:
        hist_data = build_historical_data(code, cfg)

    # =================================================================
    # Append 2026F forecast to annual historical charts
    # =================================================================
    if hist_data and forecasts:
        forecast_map = {
            "GDP Growth":      forecasts.get("GDP Growth"),
            "Budget Deficit":  forecasts.get("Budget Deficit"),
            "Current Account": forecasts.get("Current Account"),
        }
        for metric_name, fc_val in forecast_map.items():
            if metric_name in hist_data and fc_val is not None:
                hist_data[metric_name]["v"].append(fc_val)
        # For annual metrics WITHOUT a forecast, append None so arrays
        # stay aligned with the 2010-2026F label array (17 entries)
        for metric_name, cfg_h in hist_data.items():
            if cfg_h.get("annual") and metric_name not in forecast_map:
                cfg_h["v"].append(None)

    # =================================================================
    # Weather grid: historical actuals + 2026F forecast
    # Years: 2020, 2021, 2022, 2023, 2024, 2025, 2026F
    # =================================================================
    gdp_grid = []
    cpi_grid = []
    unemp_grid = []
    budget_grid = []
    ca_grid = []
    if hist_data:
        # Pull annual GDP actuals for 2020-2025 from historical data
        gdp_hist = hist_data.get("GDP Growth", {}).get("v", [])
        # Annual labels start at 2010; index 10 = 2020, through index 15 = 2025
        if len(gdp_hist) >= 16:
            gdp_grid = [round(v, 1) if v is not None else 0 for v in gdp_hist[10:16]]
        # Append 2026F forecast
        fc_gdp = forecasts.get("GDP Growth")
        gdp_grid.append(round(fc_gdp, 1) if fc_gdp is not None else 0)

        # Pull annual CPI - we need annual averages from monthly inflation data
        inf_hist = hist_data.get("Inflation (CPI)", {}).get("v", [])
        if inf_hist:
            # Monthly data from Jan 2011. Compute annual averages for 2020-2025.
            # Index: 2011=0..11, 2012=12..23, ..., 2020=108..119, 2021=120..131, etc.
            for year in range(2020, 2026):
                start_idx = (year - 2011) * 12
                end_idx = start_idx + 12
                if end_idx <= len(inf_hist):
                    year_vals = [v for v in inf_hist[start_idx:end_idx] if v is not None]
                    cpi_grid.append(round(sum(year_vals) / len(year_vals), 1) if year_vals else 0)
                elif start_idx < len(inf_hist):
                    year_vals = [v for v in inf_hist[start_idx:] if v is not None]
                    cpi_grid.append(round(sum(year_vals) / len(year_vals), 1) if year_vals else 0)
                else:
                    cpi_grid.append(0)
        # Append 2026F CPI forecast
        fc_cpi = forecasts.get("Inflation (CPI)")
        cpi_grid.append(round(fc_cpi, 1) if fc_cpi is not None else 0)

        # Pull monthly Unemployment and compute annual averages for 2020-2025
        unemp_hist = hist_data.get("Unemployment", {}).get("v", [])
        if unemp_hist:
            for year in range(2020, 2026):
                start_idx = (year - 2011) * 12
                end_idx = start_idx + 12
                if end_idx <= len(unemp_hist):
                    year_vals = [v for v in unemp_hist[start_idx:end_idx] if v is not None]
                    unemp_grid.append(round(sum(year_vals) / len(year_vals), 1) if year_vals else 0)
                elif start_idx < len(unemp_hist):
                    year_vals = [v for v in unemp_hist[start_idx:] if v is not None]
                    unemp_grid.append(round(sum(year_vals) / len(year_vals), 1) if year_vals else 0)
                else:
                    unemp_grid.append(0)
        # Append 2026F Unemployment forecast
        fc_unemp = forecasts.get("Unemployment")
        unemp_grid.append(round(fc_unemp, 1) if fc_unemp is not None else 0)

        # Pull annual Budget Deficit actuals for 2020-2025 (index 10-15)
        budget_hist = hist_data.get("Budget Deficit", {}).get("v", [])
        if len(budget_hist) >= 16:
            budget_grid = [round(v, 1) if v is not None else 0 for v in budget_hist[10:16]]
        # Append 2026F Budget Deficit forecast
        fc_budget = forecasts.get("Budget Deficit")
        budget_grid.append(round(fc_budget, 1) if fc_budget is not None else 0)

        # Pull annual Current Account actuals for 2020-2025 (index 10-15)
        ca_hist = hist_data.get("Current Account", {}).get("v", [])
        if len(ca_hist) >= 16:
            ca_grid = [round(v, 1) if v is not None else 0 for v in ca_hist[10:16]]
        # Append 2026F Current Account forecast
        fc_ca = forecasts.get("Current Account")
        ca_grid.append(round(fc_ca, 1) if fc_ca is not None else 0)

    weather_grid = {
        "gdp": {"flag": cfg["flag"], "values": gdp_grid},
        "cpi": {"flag": cfg["flag"], "values": cpi_grid},
        "unemp": {"flag": cfg["flag"], "values": unemp_grid},
        "budget": {"flag": cfg["flag"], "values": budget_grid},
        "ca": {"flag": cfg["flag"], "values": ca_grid},
    }

    return {
        "code": code,
        "name": cfg["name"],
        "flag": cfg["flag"],
        "lat": cfg["lat"],
        "lon": cfg["lon"],
        "weather": weather,
        "metrics": {"macro": macro, "market": market},
        "forecasts": forecasts if forecasts else None,
        "stories": prev.get("stories", {"beginner": [], "moderate": [], "expert": []}),
        "fxRegime": prev.get("fxRegime", {}),
        "historical": hist_data,
        "weatherGrid": weather_grid,
    }, freshness


# ===================================================================
# Commodities builder
# ===================================================================

def assign_commodity_weather(items):
    """
    Assign weather icon for commodities based on aggregate price changes.
    Positive bias = sunny (rising demand/tightness), mixed = cloudy, mostly falling = stormy.
    """
    if not items:
        return "\u2601\ufe0f"
    changes = [i["change"] for i in items if i.get("change") is not None]
    if not changes:
        return "\u2601\ufe0f"
    avg = sum(changes) / len(changes)
    pos = sum(1 for c in changes if c > 0)
    neg = sum(1 for c in changes if c < 0)
    if avg > 2 and pos >= len(changes) * 0.6:
        return "\u2600\ufe0f"    # sunny
    elif avg < -2 and neg >= len(changes) * 0.6:
        return "\u26c8\ufe0f"    # stormy
    else:
        return "\u2601\ufe0f"    # cloudy


def build_commodities(prev_snapshot, skip_historical=False):
    """
    Fetch live commodity prices from Yahoo Finance.
    Returns dict matching the frontend's commodities data schema.
    """
    log.info("Building commodities data...")
    prev_comm = None
    if prev_snapshot and "commodities" in prev_snapshot:
        prev_comm = prev_snapshot["commodities"]

    items = []
    for cfg in COMMODITY_CONFIG:
        yahoo_sym = cfg["yahoo"]
        fb = COMMODITY_FALLBACK.get(yahoo_sym, {})
        log.info("  Fetching %s (%s)...", cfg["name"], yahoo_sym)

        price = fb.get("price")
        change = fb.get("change", 0)
        spark = fb.get("spark", [])
        annual = fb.get("annual", [])

        try:
            # Fetch ~400 days for sparkline + change calculation
            daily = fetch_yahoo(yahoo_sym, days_back=400)
            if daily and len(daily) >= 2:
                latest_price = daily[-1][1]
                # Day-over-day % change
                prev_close = daily[-2][1]
                if prev_close and prev_close != 0:
                    change = round((latest_price - prev_close) / prev_close * 100, 1)
                price = round(latest_price, 2)

                # Sparkline: monthly closes for last 12 months
                monthly = resample_monthly_last(daily)
                if len(monthly) >= 12:
                    spark = [round(v, 2) for (_, _, v) in monthly[-12:]]
                elif len(monthly) >= 2:
                    spark = [round(v, 2) for (_, _, v) in monthly]

                log.info("    %s: $%.2f (%+.1f%%)", cfg["name"], price, change)
            else:
                log.warning("    %s: Yahoo returned insufficient data, using fallback", cfg["name"])
        except Exception as e:
            log.warning("    %s: Yahoo fetch failed: %s - using fallback", cfg["name"], e)

        # Annual historical data
        if not skip_historical:
            try:
                hist_daily = fetch_yahoo_historical(yahoo_sym, start=HIST_START)
                if hist_daily and len(hist_daily) > 100:
                    annual_vals = resample_annual_avg(hist_daily)
                    annual = []
                    for yr in range(HIST_ANNUAL_START, HIST_ANNUAL_END + 1):
                        match = [v for (y, v) in annual_vals if y == yr]
                        annual.append(round(match[0], 2) if match else None)
                    # Filter out trailing Nones
                    while annual and annual[-1] is None:
                        annual.pop()
                    # Replace interior Nones with interpolation
                    for i in range(len(annual)):
                        if annual[i] is None:
                            # Simple carry-forward
                            annual[i] = annual[i-1] if i > 0 else 0
                    log.info("    %s: %d annual values (%d-%d)", cfg["name"], len(annual), HIST_ANNUAL_START, HIST_ANNUAL_START + len(annual) - 1)
                else:
                    log.warning("    %s: insufficient historical data, using fallback annual", cfg["name"])
            except Exception as e:
                log.warning("    %s: historical fetch failed: %s - using fallback annual", cfg["name"], e)
        else:
            # Carry forward from previous
            if prev_comm and prev_comm.get("items"):
                prev_item = next((i for i in prev_comm["items"] if i["symbol"] == cfg["symbol"]), None)
                if prev_item and prev_item.get("annual"):
                    annual = prev_item["annual"]

        items.append({
            "name": cfg["name"],
            "symbol": cfg["symbol"],
            "cat": cfg["cat"],
            "unit": cfg["unit"],
            "price": price,
            "change": change,
            "spark": spark,
            "annual": annual,
        })

    weather = assign_commodity_weather(items)

    # Stories: carry forward from previous snapshot (same pattern as country stories)
    stories = {"beginner": [], "moderate": [], "expert": []}
    if prev_comm and prev_comm.get("stories"):
        stories = prev_comm["stories"]

    # Item explanations: carry forward from previous snapshot
    item_explanations = {}
    if prev_comm and prev_comm.get("itemExplanations"):
        item_explanations = prev_comm["itemExplanations"]

    commodity_data = {
        "asOf": datetime.now().strftime("%b %d, %Y"),
        "source": "CME \u00b7 ICE \u00b7 COMEX \u00b7 CBOT \u00b7 Yahoo Finance",
        "weather": weather,
        "items": items,
        "stories": stories,
        "itemExplanations": item_explanations,
    }

    log.info("Commodities: %d items fetched, weather: %s", len(items), weather)
    return commodity_data


# ===================================================================
# Main orchestrator
# ===================================================================

def load_previous_snapshot(path):
    """Load previous snapshot for carry-forward. Returns dict or None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def compute_fetch_summary(all_freshness):
    """Compute summary counts from freshness data."""
    total = live = stale = fallback = missing = 0
    for country_metrics in all_freshness.values():
        for info in country_metrics.values():
            total += 1
            src = info.get("source", "missing")
            if src in ("fred", "yahoo", "weo"):
                live += 1
            elif src == "stale":
                stale += 1
            elif src == "fallback":
                fallback += 1
            else:
                missing += 1
    return {
        "total_metrics": total,
        "live_count": live,
        "stale_count": stale,
        "fallback_count": fallback,
        "missing_count": missing,
    }


def build_snapshot(output_path="snapshot.json", skip_historical=False):
    """
    Main entry point. Fetches all data, builds all 9 countries,
    writes snapshot.json. NEVER fails completely.
    """
    log.info("=" * 60)
    log.info("MacroSnaps snapshot builder starting")
    if skip_historical:
        log.info("Historical data: SKIPPED (carrying forward from previous)")
    else:
        log.info("Historical data: ENABLED (fetching from 2010)")
    log.info("=" * 60)

    if not FRED_API_KEY:
        log.warning("FRED_API_KEY not set - all FRED metrics will use fallbacks")

    if not HAS_IMF_READER:
        log.warning("imf_reader not installed - budget deficit will use fallbacks")

    prev = load_previous_snapshot(output_path)
    if prev:
        log.info("Loaded previous snapshot for carry-forward")
    else:
        log.info("No previous snapshot found - using hardcoded fallbacks only")

    # Fetch Google Sheet forecasts (absolute truth for macro)
    forecasts = fetch_forecasts()

    countries = {}
    all_freshness = {}

    for code, cfg in COUNTRY_CONFIG.items():
        log.info("Building %s (%s)...", code, cfg["name"])
        try:
            country_data, freshness = build_country(code, cfg, prev, skip_historical, forecasts.get(code, {}))
            countries[code] = country_data
            all_freshness[code] = freshness
        except Exception as e:
            log.error("FAILED building %s: %s - using empty placeholder", code, e)
            countries[code] = {
                "code": code,
                "name": cfg["name"],
                "flag": cfg["flag"],
                "lat": cfg["lat"],
                "lon": cfg["lon"],
                "weather": "\u2601\ufe0f",
                "metrics": {
                    "macro": {
                        "GDP Growth": "-", "Inflation (CPI)": "-",
                        "Unemployment": "-", "Budget Deficit": "-",
                        "Current Account": "-", "Policy Rate": "-",
                    },
                    "market": {
                        "Stock Market YTD": "-", "Equity Vol": "-",
                        "10Y Bond Yield": "-", "Yield Curve": "-",
                        "Corp Spread": "-", "Sov CDS": "-",
                        cfg["fx_key"]: "-", "FX Vol": "-",
                    },
                },
                "stories": {"beginner": [], "moderate": [], "expert": []},
                "forecasts": None,
                "fxRegime": {},
                "historical": None,
                "weatherGrid": {
                    "gdp": {"flag": cfg["flag"], "values": []},
                    "cpi": {"flag": cfg["flag"], "values": []},
                    "unemp": {"flag": cfg["flag"], "values": []},
                    "budget": {"flag": cfg["flag"], "values": []},
                    "ca": {"flag": cfg["flag"], "values": []},
                },
            }
            all_freshness[code] = {}

    summary = compute_fetch_summary(all_freshness)

    # Build commodities data
    try:
        commodity_data = build_commodities(prev, skip_historical)
    except Exception as e:
        log.error("FAILED building commodities: %s - using empty placeholder", e)
        commodity_data = None

    snapshot = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_freshness": all_freshness,
        "fetch_summary": summary,
        "countries": countries,
    }
    if commodity_data:
        snapshot["commodities"] = commodity_data

    # Atomic write: tmp file then rename
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, output_path)

    # Print summary
    log.info("=" * 60)
    log.info("Snapshot written to %s", output_path)
    log.info(
        "Metrics: %d total | %d live | %d fallback | %d missing",
        summary["total_metrics"],
        summary["live_count"],
        summary["fallback_count"],
        summary["missing_count"],
    )
    log.info("=" * 60)

    # Print per-country summary
    for code in COUNTRY_CONFIG:
        c = countries[code]
        macro_vals = list(c["metrics"]["macro"].values())
        market_vals = list(c["metrics"]["market"].values())
        live_count = sum(1 for v in macro_vals + market_vals if v != "-")
        log.info(
            "  %s %s: %s  %d/14 metrics live",
            c["flag"], code, c["weather"], live_count,
        )

    if commodity_data:
        live_comm = sum(1 for i in commodity_data["items"] if i["price"] is not None)
        log.info(
            "  \U0001f6e2\ufe0f COMM: %s  %d/%d commodities live",
            commodity_data.get("weather", "?"), live_comm, len(commodity_data["items"]),
        )

    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build MacroSnaps snapshot")
    parser.add_argument(
        "--output", "-o",
        default="snapshot.json",
        help="Output path for snapshot.json (default: snapshot.json)",
    )
    parser.add_argument(
        "--skip-historical",
        action="store_true",
        help="Skip historical data fetch (carries forward from previous snapshot)",
    )
    args = parser.parse_args()
    build_snapshot(args.output, skip_historical=args.skip_historical)
