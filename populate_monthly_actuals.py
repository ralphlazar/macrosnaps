#!/usr/bin/env python3
"""
populate_monthly_actuals.py
One-time backfill of the MACRO-MONTHLY Google Sheet with monthly actuals
for Inflation (CPI YoY %), Unemployment (%), and Policy Rate (%) from Jan 2000.

Run with --dry-run to preview row counts without writing to the sheet.

Policy rate sources:
  USA: FRED FEDFUNDS
  DEU/FRA/ITA: FRED ECBMRRFR (ECB daily, last obs per month)
  CAN/GBR/JPN/IND/ZAF/BRA/RUS: BIS CBPOL dataset (IRSTCB01 family frozen on FRED)
  CHN: no reliable source, column left blank

CPI sources:
  JPN: FRED CPALTT01JPM657N (pre-computed YoY rate, avoids OECD index gap)
  All others: FRED OECD index series, YoY computed from index levels

Unemployment sources:
  BRA: PME series discontinued 2016, no monthly FRED replacement, column left blank
  CHN/IND/ZAF/RUS: no reliable monthly source, columns left blank
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

FRED_API_KEY = os.getenv("FRED_API_KEY")
MACRO_MONTHLY_SHEET_ID = os.getenv("MACRO_MONTHLY_SHEET_ID")
KEY_FILE = os.path.join(os.path.dirname(__file__), "market-stats-key.json")

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

# Countries routed to BIS CBPOL for policy rates (IRSTCB01 family frozen on FRED)
# Values are BIS REF_AREA codes (ISO 2-letter)
BIS_RATE_COUNTRIES = {
    "CAN": "CA",
    "GBR": "GB",
    "JPN": "JP",
    "IND": "IN",
    "ZAF": "ZA",
    "BRA": "BR",
    "RUS": "RU",
}

# CPI index series - YoY computed as (current / 12-months-ago - 1) * 100
# JPN is excluded here; it uses CPI_YOY_SERIES below
CPI_SERIES = {
    "USA": "CPIAUCSL",
    "CAN": "CANCPIALLMINMEI",
    "GBR": "GBRCPIALLMINMEI",
    "DEU": "DEUCPIALLMINMEI",
    "FRA": "FRACPIALLMINMEI",
    "ITA": "ITACPIALLMINMEI",
    "CHN": "CHNCPIALLMINMEI",
    "IND": "INDCPIALLMINMEI",
    "ZAF": "ZAFCPIALLMINMEI",
    "BRA": "BRACPIALLMINMEI",
    "RUS": "RUSCPIALLMINMEI",
}

# Countries where FRED provides a pre-computed YoY CPI rate directly.
# No index-level computation needed - use observations as-is.
# JPN: JPNCPIALLMINMEI (OECD index) has a data gap that breaks YoY from mid-2021.
#      CPALTT01JPM657N is the OECD growth rate series, current and clean.
CPI_YOY_SERIES = {
    "JPN": "CPALTT01JPM657N",
}

# Unemployment - monthly harmonised series where available
# BRA: LRUNTTTTBRM156S is the discontinued PME series (stopped 2016). No monthly replacement.
UNEMP_SERIES = {
    "USA": "UNRATE",
    "CAN": "LRUNTTTTCAM156S",
    "GBR": "LRHUTTTTGBM156S",
    "JPN": "LRUNTTTTJPM156S",
    "DEU": "LRHUTTTTDEM156S",
    "FRA": "LRHUTTTTFRM156S",
    "ITA": "LRHUTTTTITM156S",
    "CHN": None,
    "IND": None,
    "ZAF": None,
    "BRA": None,
    "RUS": None,
}

# Policy rate series - "BIS" means use bis_fetch_policy_rates(), None means no data
RATE_SERIES = {
    "USA": "FEDFUNDS",
    "CAN": "BIS",
    "GBR": "BIS",
    "JPN": "BIS",
    "DEU": "ECBMRRFR",
    "FRA": "ECBMRRFR",
    "ITA": "ECBMRRFR",
    "CHN": None,
    "IND": "BIS",
    "ZAF": "BIS",
    "BRA": "BIS",
    "RUS": "BIS",
}


def fred_fetch(series_id, observation_start):
    """
    Fetch a FRED series and return a dict of {YYYY-MM-01: float or None}.
    For daily series, later dates in the same month overwrite earlier ones,
    giving the last observation of each month.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": observation_start,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    result = {}
    for obs in data.get("observations", []):
        d = obs["date"]
        month_key = d[:7] + "-01"
        val = obs["value"]
        if val != ".":
            try:
                result[month_key] = float(val)
            except ValueError:
                result[month_key] = None
    return result


def bis_fetch_policy_rates(observation_start):
    """
    Fetch monthly central bank policy rates from the BIS WS_CBPOL dataset.
    Returns {country_code: {YYYY-MM-01: float}}.

    Row-based CSV format: FREQ, REF_AREA, ..., TIME_PERIOD, OBS_VALUE per row.
    observation_start should be a YYYY-MM-DD or YYYY-MM string.
    """
    bis_codes = "+".join(BIS_RATE_COUNTRIES.values())
    url = f"https://stats.bis.org/api/v1/data/WS_CBPOL/M.{bis_codes}/all"
    start_period = observation_start[:7]  # YYYY-MM
    params = {"format": "csv", "startPeriod": start_period}
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()

    bis_to_country = {v: k for k, v in BIS_RATE_COUNTRIES.items()}
    result = {c: {} for c in BIS_RATE_COUNTRIES}

    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        ref_area = row.get("REF_AREA", "").strip()
        time_period = row.get("TIME_PERIOD", "").strip()
        obs_value = row.get("OBS_VALUE", "").strip()
        country = bis_to_country.get(ref_area)
        if country and time_period and obs_value:
            try:
                month_key = time_period + "-01"
                result[country][month_key] = round(float(obs_value), 2)
            except (ValueError, TypeError):
                pass

    for country in BIS_RATE_COUNTRIES:
        count = len(result[country])
        print(f"  BIS {country}: {count} months fetched")

    return result


def compute_cpi_yoy(raw):
    """
    Given {YYYY-MM-01: index_level}, return {YYYY-MM-01: yoy_pct} from Jan 2000.
    Requires Dec 1999 in raw as the base for Jan 2000.
    """
    yoy = {}
    for d in sorted(raw.keys()):
        dt = datetime.strptime(d, "%Y-%m-%d")
        prior_key = (dt - relativedelta(months=12)).strftime("%Y-%m-%d")
        if raw.get(d) is not None and raw.get(prior_key) is not None and raw[prior_key] != 0:
            yoy[d] = round((raw[d] / raw[prior_key] - 1) * 100, 2)
        else:
            yoy[d] = None
    return {k: v for k, v in yoy.items() if k >= "2000-01-01"}


def build_date_index(start="2000-01-01"):
    """Build list of YYYY-MM-01 strings from start to current month."""
    dates = []
    current = datetime.strptime(start, "%Y-%m-%d")
    today = date.today()
    end = date(today.year, today.month, 1)
    while current.date() <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += relativedelta(months=1)
    return dates


def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def ensure_tab(service, sheet_id, tab_name):
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]
    if tab_name not in existing:
        body = {"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        print(f"  Created tab: {tab_name}")
    else:
        print(f"  Tab exists: {tab_name}")


def write_tab(service, sheet_id, tab_name, rows, dry_run=False):
    if dry_run:
        print(f"  [DRY RUN] {tab_name}: would write {len(rows) - 1} data rows")
        return
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=tab_name
    ).execute()
    body = {"values": rows}
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        body=body,
    ).execute()
    print(f"  {tab_name}: wrote {len(rows) - 1} data rows")


def build_inflation_rows(dry_run=False):
    print("Fetching CPI data from FRED (from Dec 1999 for YoY base)...")
    date_index = build_date_index("2000-01-01")
    yoy_by_country = {}

    # Standard index series - compute YoY from monthly index levels
    for country, series in CPI_SERIES.items():
        print(f"  {country}: {series}")
        try:
            raw = fred_fetch(series, "1999-12-01")
            yoy_by_country[country] = compute_cpi_yoy(raw)
        except Exception as e:
            print(f"  {country}: FAILED ({e})")
            yoy_by_country[country] = {}

    # Pre-computed YoY series - use FRED observations directly, no calculation needed
    for country, series in CPI_YOY_SERIES.items():
        print(f"  {country}: {series} (pre-computed YoY)")
        try:
            raw = fred_fetch(series, "2000-01-01")
            yoy_by_country[country] = {
                k: round(v, 2) if v is not None else None for k, v in raw.items()
            }
        except Exception as e:
            print(f"  {country}: FAILED ({e})")
            yoy_by_country[country] = {}

    header = ["Date"] + COUNTRIES
    rows = [header]
    for d in date_index:
        row = [d]
        for country in COUNTRIES:
            val = yoy_by_country.get(country, {}).get(d)
            row.append(val if val is not None else "")
        rows.append(row)
    return rows


def build_unemployment_rows(dry_run=False):
    print("Fetching Unemployment data from FRED...")
    date_index = build_date_index("2000-01-01")
    data_by_country = {}
    for country in COUNTRIES:
        series = UNEMP_SERIES[country]
        if series is None:
            print(f"  {country}: no reliable series (column will be blank)")
            data_by_country[country] = {}
            continue
        print(f"  {country}: {series}")
        try:
            raw = fred_fetch(series, "2000-01-01")
            data_by_country[country] = {k: round(v, 2) if v is not None else None for k, v in raw.items()}
        except Exception as e:
            print(f"  {country}: FAILED ({e})")
            data_by_country[country] = {}

    header = ["Date"] + COUNTRIES
    rows = [header]
    for d in date_index:
        row = [d]
        for country in COUNTRIES:
            val = data_by_country[country].get(d)
            row.append(val if val is not None else "")
        rows.append(row)
    return rows


def build_policy_rate_rows(dry_run=False):
    print("Fetching Policy Rate data from FRED and BIS...")
    date_index = build_date_index("2000-01-01")
    data_by_country = {}
    fetched_ecb = None
    bis_data = None

    for country in COUNTRIES:
        series = RATE_SERIES[country]
        if series is None:
            print(f"  {country}: no reliable series (column will be blank)")
            data_by_country[country] = {}
        elif series == "BIS":
            if bis_data is None:
                print(f"  BIS (CAN/GBR/JPN/IND/ZAF/BRA/RUS): fetching CBPOL dataset from 2000-01-01")
                try:
                    bis_data = bis_fetch_policy_rates("2000-01-01")
                except Exception as e:
                    print(f"  BIS: FAILED ({e})")
                    bis_data = {c: {} for c in BIS_RATE_COUNTRIES}
            data_by_country[country] = bis_data.get(country, {})
        elif series == "ECBMRRFR":
            if fetched_ecb is None:
                print(f"  ECB (DEU/FRA/ITA): {series} (daily, last obs per month)")
                try:
                    raw = fred_fetch(series, "2000-01-01")
                    fetched_ecb = {k: round(v, 2) if v is not None else None for k, v in raw.items()}
                except Exception as e:
                    print(f"  ECB: FAILED ({e})")
                    fetched_ecb = {}
            data_by_country[country] = fetched_ecb
        else:
            print(f"  {country}: {series}")
            try:
                raw = fred_fetch(series, "2000-01-01")
                data_by_country[country] = {k: round(v, 2) if v is not None else None for k, v in raw.items()}
            except Exception as e:
                print(f"  {country}: FAILED ({e})")
                data_by_country[country] = {}

    header = ["Date"] + COUNTRIES
    rows = [header]
    for d in date_index:
        row = [d]
        for country in COUNTRIES:
            val = data_by_country[country].get(d)
            row.append(val if val is not None else "")
        rows.append(row)
    return rows


def main():
    dry_run = "--dry-run" in sys.argv

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not found in .env")
        sys.exit(1)
    if not MACRO_MONTHLY_SHEET_ID:
        print("ERROR: MACRO_MONTHLY_SHEET_ID not found in .env")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}populate_monthly_actuals.py")
    print(f"Sheet ID: {MACRO_MONTHLY_SHEET_ID}")
    print()

    service = get_sheets_service()

    if not dry_run:
        print("Ensuring tabs exist...")
        for tab in ["Inflation", "Unemployment", "Policy_Rate"]:
            ensure_tab(service, MACRO_MONTHLY_SHEET_ID, tab)
        print()

    print("--- Inflation ---")
    inflation_rows = build_inflation_rows(dry_run)
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Inflation", inflation_rows, dry_run)
    print()

    print("--- Unemployment ---")
    unemp_rows = build_unemployment_rows(dry_run)
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Unemployment", unemp_rows, dry_run)
    print()

    print("--- Policy Rate ---")
    rate_rows = build_policy_rate_rows(dry_run)
    write_tab(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate", rate_rows, dry_run)
    print()

    print("Done.")


if __name__ == "__main__":
    main()
