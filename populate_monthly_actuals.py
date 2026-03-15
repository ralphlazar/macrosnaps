#!/usr/bin/env python3
"""
populate_monthly_actuals.py  (v2)
One-time backfill of the MACRO-MONTHLY Google Sheet with monthly actuals
for Inflation (CPI YoY %), Unemployment (%), and Policy Rate (%) from Jan 2000.

Run with --dry-run to preview row counts without writing to the sheet.

Sources
-------
CPI           IMF IFS, indicator PCPI_IX (monthly index, all 12 countries, single API call)
              YoY computed from index levels: (index_t / index_t-12 − 1) × 100
              Replaces FRED OECD MINMEI family, which froze at various dates.

Unemployment  IMF IFS, indicator LUR (monthly %, all 12 countries, single API call)
              Countries with no IMF LUR coverage produce blank columns.
              Replaces FRED OECD harmonised series for the same reason.

Policy Rate   USA              FRED FEDFUNDS
              DEU / FRA / ITA  FRED ECBMRRFR (ECB main refinancing rate, last obs per month)
              CAN / GBR / JPN / IND / ZAF / BRA  BIS WS_CBPOL dataset
              CHN              no reliable free source → blank
              RUS              BIS ceased publishing after Feb 2022 (sanctions) → blank
"""

import csv
import io
import os
import sys
import requests
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

FRED_API_KEY          = os.getenv("FRED_API_KEY")           # required for Policy Rate only
MACRO_MONTHLY_SHEET_ID = os.getenv("MACRO_MONTHLY_SHEET_ID")
KEY_FILE              = os.path.join(os.path.dirname(__file__), "market-stats-key.json")

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

# IMF IFS uses ISO 2-letter REF_AREA codes
IMF_COUNTRY_CODES = {
    "USA": "US", "CAN": "CA", "GBR": "GB", "JPN": "JP",
    "DEU": "DE", "FRA": "FR", "ITA": "IT", "CHN": "CN",
    "IND": "IN", "ZAF": "ZA", "BRA": "BR", "RUS": "RU",
}

# BIS CBPOL countries.  RUS excluded: BIS stopped publishing after Feb 2022.
BIS_RATE_COUNTRIES = {
    "CAN": "CA", "GBR": "GB", "JPN": "JP",
    "IND": "IN", "ZAF": "ZA", "BRA": "BR",
}

# Policy rate routing.  Format: "FRED:<series_id>", "BIS", or None.
RATE_SERIES = {
    "USA": "FRED:FEDFUNDS",
    "CAN": "BIS",
    "GBR": "BIS",
    "JPN": "BIS",
    "DEU": "FRED:ECBMRRFR",
    "FRA": "FRED:ECBMRRFR",
    "ITA": "FRED:ECBMRRFR",
    "CHN": None,                  # no reliable free source
    "IND": "BIS",
    "ZAF": "BIS",
    "BRA": "BIS",
    "RUS": None,                  # BIS sanctions gap from Mar 2022; no reliable free alternative
}


# ---------------------------------------------------------------------------
# IMF IFS  (CPI + Unemployment)
# ---------------------------------------------------------------------------

def imf_fetch(indicator, start_period):
    """
    Fetch a monthly IMF IFS indicator for all 12 countries in a single API call.

    indicator    e.g. "PCPI_IX" (CPI index) or "LUR" (unemployment rate)
    start_period YYYY-MM string

    Returns {country_3letter: {YYYY-MM-01: float}}

    The IFS SDMX-JSON response returns Series as a list when multiple countries
    are present, or a bare dict when only one matches.  Both cases are handled.
    """
    codes = "+".join(IMF_COUNTRY_CODES.values())
    url   = (
        "https://dataservices.imf.org/REST/SDMX_JSON.svc/"
        f"CompactData/IFS/M.{codes}.{indicator}"
    )
    resp = requests.get(url, params={"startPeriod": start_period}, timeout=60)
    resp.raise_for_status()

    imf_to_country = {v: k for k, v in IMF_COUNTRY_CODES.items()}
    result = {c: {} for c in COUNTRIES}

    series = resp.json()["CompactData"]["DataSet"].get("Series", [])
    if isinstance(series, dict):
        series = [series]

    for s in series:
        country = imf_to_country.get(s.get("@REF_AREA", ""))
        if not country:
            continue
        obs_list = s.get("Obs", [])
        if isinstance(obs_list, dict):
            obs_list = [obs_list]
        for o in obs_list:
            tp  = o.get("@TIME_PERIOD", "")   # "YYYY-MM"
            val = o.get("@OBS_VALUE")
            if tp and val is not None:
                try:
                    result[country][tp + "-01"] = float(val)
                except (ValueError, TypeError):
                    pass

    for c in COUNTRIES:
        n = len(result[c])
        flag = "" if n > 0 else "  ← NO DATA"
        print(f"  IMF {indicator} {c}: {n} months{flag}")

    return result


# ---------------------------------------------------------------------------
# FRED  (Policy Rate only)
# ---------------------------------------------------------------------------

def fred_fetch(series_id, observation_start):
    """
    Fetch a FRED series.  Returns {YYYY-MM-01: float}.
    For daily series, later dates in the same month overwrite earlier ones,
    giving the last observation of each calendar month.
    """
    params = {
        "series_id":        series_id,
        "api_key":          FRED_API_KEY,
        "file_type":        "json",
        "observation_start": observation_start,
    }
    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params=params, timeout=30,
    )
    resp.raise_for_status()
    result = {}
    for obs in resp.json().get("observations", []):
        month_key = obs["date"][:7] + "-01"
        val = obs["value"]
        if val != ".":
            try:
                result[month_key] = float(val)
            except ValueError:
                pass
    return result


# ---------------------------------------------------------------------------
# BIS  (Policy Rate)
# ---------------------------------------------------------------------------

def bis_fetch_policy_rates(observation_start):
    """
    Fetch monthly central bank policy rates from BIS WS_CBPOL.
    Returns {country_3letter: {YYYY-MM-01: float}}.
    Row-based CSV: columns include REF_AREA, TIME_PERIOD, OBS_VALUE.
    """
    codes = "+".join(BIS_RATE_COUNTRIES.values())
    url   = f"https://stats.bis.org/api/v1/data/WS_CBPOL/M.{codes}/all"
    params = {"format": "csv", "startPeriod": observation_start[:7]}
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()

    bis_to_country = {v: k for k, v in BIS_RATE_COUNTRIES.items()}
    result = {c: {} for c in BIS_RATE_COUNTRIES}

    for row in csv.DictReader(io.StringIO(resp.text)):
        ref_area    = row.get("REF_AREA",    "").strip()
        time_period = row.get("TIME_PERIOD", "").strip()
        obs_value   = row.get("OBS_VALUE",   "").strip()
        country = bis_to_country.get(ref_area)
        if country and time_period and obs_value:
            try:
                result[country][time_period + "-01"] = round(float(obs_value), 2)
            except (ValueError, TypeError):
                pass

    for c in BIS_RATE_COUNTRIES:
        print(f"  BIS {c}: {len(result[c])} months")

    return result


# ---------------------------------------------------------------------------
# CPI helpers
# ---------------------------------------------------------------------------

def compute_cpi_yoy(raw):
    """
    {YYYY-MM-01: index_level} → {YYYY-MM-01: yoy_pct} for all dates ≥ 2000-01-01.
    Requires the Dec 1999 index value in raw to produce Jan 2000.
    """
    yoy = {}
    for d in sorted(raw):
        dt    = datetime.strptime(d, "%Y-%m-%d")
        prior = (dt - relativedelta(months=12)).strftime("%Y-%m-%d")
        if raw.get(d) and raw.get(prior):
            yoy[d] = round((raw[d] / raw[prior] - 1) * 100, 2)
        else:
            yoy[d] = None
    return {k: v for k, v in yoy.items() if k >= "2000-01-01"}


# ---------------------------------------------------------------------------
# Date utilities
# ---------------------------------------------------------------------------

def build_date_index(start="2000-01-01"):
    """List of YYYY-MM-01 strings from start through the current month."""
    dates   = []
    current = datetime.strptime(start, "%Y-%m-%d")
    today   = date.today()
    end     = date(today.year, today.month, 1)
    while current.date() <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += relativedelta(months=1)
    return dates


# ---------------------------------------------------------------------------
# Sheets helpers
# ---------------------------------------------------------------------------

def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def ensure_tab(service, sheet_id, tab_name):
    meta     = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]
    if tab_name not in existing:
        body = {"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        print(f"  Created tab: {tab_name}")
    else:
        print(f"  Tab exists:  {tab_name}")


def write_tab(service, sheet_id, tab_name, rows, dry_run=False):
    if dry_run:
        print(f"  [DRY RUN] {tab_name}: would write {len(rows) - 1} data rows")
        return
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=tab_name
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()
    print(f"  {tab_name}: wrote {len(rows) - 1} data rows")


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def build_inflation_rows():
    print("Fetching CPI index from IMF IFS (PCPI_IX) — from Dec 1999 for YoY base...")
    raw_by_country = imf_fetch("PCPI_IX", "1999-12")
    date_index     = build_date_index("2000-01-01")

    yoy_by_country = {c: compute_cpi_yoy(raw_by_country[c]) for c in COUNTRIES}

    header = ["Date"] + COUNTRIES
    rows   = [header]
    for d in date_index:
        row = [d]
        for c in COUNTRIES:
            v = yoy_by_country[c].get(d)
            row.append(v if v is not None else "")
        rows.append(row)
    return rows


def build_unemployment_rows():
    print("Fetching Unemployment from IMF IFS (LUR)...")
    data       = imf_fetch("LUR", "2000-01")
    date_index = build_date_index("2000-01-01")

    header = ["Date"] + COUNTRIES
    rows   = [header]
    for d in date_index:
        row = [d]
        for c in COUNTRIES:
            v = data[c].get(d)
            row.append(round(v, 2) if v is not None else "")
        rows.append(row)
    return rows


def build_policy_rate_rows():
    print("Fetching Policy Rate (FRED + BIS)...")
    date_index     = build_date_index("2000-01-01")
    data_by_country = {}
    fetched_ecb    = None
    bis_data       = None

    for country in COUNTRIES:
        spec = RATE_SERIES[country]

        if spec is None:
            print(f"  {country}: no source → blank")
            data_by_country[country] = {}

        elif spec == "BIS":
            if bis_data is None:
                print("  BIS: fetching WS_CBPOL from 2000-01-01...")
                try:
                    bis_data = bis_fetch_policy_rates("2000-01-01")
                except Exception as e:
                    print(f"  BIS: FAILED ({e})")
                    bis_data = {c: {} for c in BIS_RATE_COUNTRIES}
            data_by_country[country] = bis_data.get(country, {})

        elif spec == "FRED:ECBMRRFR":
            if fetched_ecb is None:
                print("  ECB (DEU/FRA/ITA): FRED ECBMRRFR (daily → last obs per month)...")
                try:
                    raw = fred_fetch("ECBMRRFR", "2000-01-01")
                    fetched_ecb = {k: round(v, 2) for k, v in raw.items()}
                except Exception as e:
                    print(f"  ECB: FAILED ({e})")
                    fetched_ecb = {}
            data_by_country[country] = fetched_ecb

        else:
            fred_series = spec.split(":")[1]
            print(f"  {country}: FRED {fred_series}")
            try:
                raw = fred_fetch(fred_series, "2000-01-01")
                data_by_country[country] = {k: round(v, 2) for k, v in raw.items()}
            except Exception as e:
                print(f"  {country}: FAILED ({e})")
                data_by_country[country] = {}

    header = ["Date"] + COUNTRIES
    rows   = [header]
    for d in date_index:
        row = [d]
        for c in COUNTRIES:
            v = data_by_country[c].get(d)
            row.append(v if v is not None else "")
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    dry_run = "--dry-run" in sys.argv

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not set (required for Policy Rate)")
        sys.exit(1)
    if not MACRO_MONTHLY_SHEET_ID:
        print("ERROR: MACRO_MONTHLY_SHEET_ID not set")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}populate_monthly_actuals.py  v2")
    print(f"Sheet: {MACRO_MONTHLY_SHEET_ID}")
    print()

    service = get_sheets_service()

    if not dry_run:
        print("Ensuring tabs exist...")
        for tab in ["Inflation", "Unemployment", "Policy_Rate"]:
            ensure_tab(service, MACRO_MONTHLY_SHEET_ID, tab)
        print()

    print("--- Inflation ---")
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Inflation",
              build_inflation_rows(), dry_run)
    print()

    print("--- Unemployment ---")
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Unemployment",
              build_unemployment_rows(), dry_run)
    print()

    print("--- Policy Rate ---")
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate",
              build_policy_rate_rows(), dry_run)
    print()

    print("Done.")


if __name__ == "__main__":
    main()
