#!/usr/bin/env python3
"""
update_monthly_actuals.py  (v2)
Reads the last date in each MACRO-MONTHLY tab and appends any new months.
Safe to run daily — exits cleanly when nothing new is available.

Sources: identical to populate_monthly_actuals.py v2.
  CPI           IMF IFS PCPI_IX  (all 12 countries, single API call)
  Unemployment  IMF IFS LUR      (all 12 countries, single API call)
  Policy Rate   FRED (USA, EUR zone) + BIS (CAN/GBR/JPN/IND/ZAF/BRA)
                CHN and RUS: blank

--dry-run  preview without writing.
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

FRED_API_KEY           = os.getenv("FRED_API_KEY")
MACRO_MONTHLY_SHEET_ID = os.getenv("MACRO_MONTHLY_SHEET_ID")
KEY_FILE               = os.path.join(os.path.dirname(__file__), "market-stats-key.json")

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

IMF_COUNTRY_CODES = {
    "USA": "US", "CAN": "CA", "GBR": "GB", "JPN": "JP",
    "DEU": "DE", "FRA": "FR", "ITA": "IT", "CHN": "CN",
    "IND": "IN", "ZAF": "ZA", "BRA": "BR", "RUS": "RU",
}

# RUS excluded: BIS stopped publishing after Feb 2022
BIS_RATE_COUNTRIES = {
    "CAN": "CA", "GBR": "GB", "JPN": "JP",
    "IND": "IN", "ZAF": "ZA", "BRA": "BR",
}

RATE_SERIES = {
    "USA": "FRED:FEDFUNDS",
    "CAN": "BIS",
    "GBR": "BIS",
    "JPN": "BIS",
    "DEU": "FRED:ECBMRRFR",
    "FRA": "FRED:ECBMRRFR",
    "ITA": "FRED:ECBMRRFR",
    "CHN": None,
    "IND": "BIS",
    "ZAF": "BIS",
    "BRA": "BIS",
    "RUS": None,   # BIS sanctions gap from Mar 2022; no reliable free alternative
}


# ---------------------------------------------------------------------------
# IMF IFS
# ---------------------------------------------------------------------------

def imf_fetch(indicator, start_period):
    """
    Fetch a monthly IMF IFS indicator for all 12 countries in a single API call.

    indicator    e.g. "PCPI_IX" or "LUR"
    start_period YYYY-MM string

    Returns {country_3letter: {YYYY-MM-01: float}}
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

    return result


# ---------------------------------------------------------------------------
# FRED  (Policy Rate only)
# ---------------------------------------------------------------------------

def fred_fetch(series_id, observation_start):
    """Fetch a FRED series.  Returns {YYYY-MM-01: float}."""
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

    return result


# ---------------------------------------------------------------------------
# CPI helpers
# ---------------------------------------------------------------------------

def compute_cpi_yoy_incremental(new_date, new_val, raw_base):
    """
    Compute CPI YoY for a single new month given a dict of historical index values.
    raw_base must contain the value 12 months prior to new_date.
    """
    dt    = datetime.strptime(new_date, "%Y-%m-%d")
    prior = (dt - relativedelta(months=12)).strftime("%Y-%m-%d")
    prior_val = raw_base.get(prior)
    if new_val and prior_val:
        return round((new_val / prior_val - 1) * 100, 2)
    return None


# ---------------------------------------------------------------------------
# Sheets helpers
# ---------------------------------------------------------------------------

def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def get_last_date_in_tab(service, sheet_id, tab_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{tab_name}!A:A"
    ).execute()
    data_rows = [r[0] for r in result.get("values", [])[1:] if r]
    return data_rows[-1] if data_rows else None


def dates_to_append(last_date_str):
    """Return list of YYYY-MM-01 strings from the month after last_date through today."""
    last    = datetime.strptime(last_date_str, "%Y-%m-%d")
    today   = date.today()
    end     = date(today.year, today.month, 1)
    new_dates = []
    current   = last + relativedelta(months=1)
    while current.date() <= end:
        new_dates.append(current.strftime("%Y-%m-%d"))
        current += relativedelta(months=1)
    return new_dates


def append_rows(service, sheet_id, tab_name, rows, dry_run=False):
    if not rows:
        print(f"  {tab_name}: nothing to append")
        return
    if dry_run:
        print(f"  [DRY RUN] {tab_name}: would append {len(rows)} row(s): {[r[0] for r in rows]}")
        return
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()
    print(f"  {tab_name}: appended {len(rows)} row(s): {[r[0] for r in rows]}")


# ---------------------------------------------------------------------------
# Updaters
# ---------------------------------------------------------------------------

def update_inflation(service, dry_run):
    print("Inflation:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Inflation")
    if not last_date:
        print("  No data — run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return
    print(f"  Last: {last_date}  →  fetching to {new_dates[-1]}")

    # Fetch from 13 months before the first new date to support YoY computation
    base_start = (
        datetime.strptime(new_dates[0], "%Y-%m-%d") - relativedelta(months=13)
    ).strftime("%Y-%m")
    raw_by_country = imf_fetch("PCPI_IX", base_start)

    rows = []
    for d in new_dates:
        row = [d]
        for c in COUNTRIES:
            raw  = raw_by_country[c]
            yoy  = compute_cpi_yoy_incremental(d, raw.get(d), raw)
            row.append(yoy if yoy is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Inflation", rows, dry_run)


def update_unemployment(service, dry_run):
    print("Unemployment:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Unemployment")
    if not last_date:
        print("  No data — run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return
    print(f"  Last: {last_date}  →  fetching to {new_dates[-1]}")

    data = imf_fetch("LUR", new_dates[0][:7])   # YYYY-MM

    rows = []
    for d in new_dates:
        row = [d]
        for c in COUNTRIES:
            v = data[c].get(d)
            row.append(round(v, 2) if v is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Unemployment", rows, dry_run)


def update_policy_rate(service, dry_run):
    print("Policy Rate:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate")
    if not last_date:
        print("  No data — run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return
    print(f"  Last: {last_date}  →  fetching to {new_dates[-1]}")

    data_by_country = {}
    fetched_ecb     = None
    bis_data        = None

    for country in COUNTRIES:
        spec = RATE_SERIES[country]

        if spec is None:
            data_by_country[country] = {}

        elif spec == "BIS":
            if bis_data is None:
                try:
                    bis_data = bis_fetch_policy_rates(new_dates[0])
                except Exception as e:
                    print(f"  BIS: FAILED ({e})")
                    bis_data = {c: {} for c in BIS_RATE_COUNTRIES}
            data_by_country[country] = bis_data.get(country, {})

        elif spec == "FRED:ECBMRRFR":
            if fetched_ecb is None:
                try:
                    raw = fred_fetch("ECBMRRFR", new_dates[0])
                    fetched_ecb = {k: round(v, 2) for k, v in raw.items()}
                except Exception as e:
                    print(f"  ECB: FAILED ({e})")
                    fetched_ecb = {}
            data_by_country[country] = fetched_ecb

        else:
            fred_series = spec.split(":")[1]
            try:
                raw = fred_fetch(fred_series, new_dates[0])
                data_by_country[country] = {k: round(v, 2) for k, v in raw.items()}
            except Exception as e:
                print(f"  {country}: FAILED ({e})")
                data_by_country[country] = {}

    rows = []
    for d in new_dates:
        row = [d]
        for c in COUNTRIES:
            v = data_by_country[c].get(d)
            row.append(v if v is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate", rows, dry_run)


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

    print(f"{'[DRY RUN] ' if dry_run else ''}update_monthly_actuals.py  v2")
    print()

    service = get_sheets_service()

    update_inflation(service, dry_run)
    print()
    update_unemployment(service, dry_run)
    print()
    update_policy_rate(service, dry_run)
    print()
    print("Done.")


if __name__ == "__main__":
    main()
