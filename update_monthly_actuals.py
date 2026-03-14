#!/usr/bin/env python3
"""
update_monthly_actuals.py
Reads the last date in each MACRO-MONTHLY tab and appends any new months.
Safe to run daily - exits cleanly if nothing new is available.

Run with --dry-run to preview without writing.

Policy rate sources:
  USA: FRED FEDFUNDS
  DEU/FRA/ITA: FRED ECBMRRFR (ECB daily, last obs per month)
  CAN/GBR/JPN/IND/ZAF/BRA/RUS: BIS CBPOL dataset
  CHN: no reliable source, column left blank

CPI sources:
  JPN: FRED CPALTT01JPM657N (pre-computed YoY, no index computation needed)
  All others: FRED OECD index series, YoY computed from index levels

Unemployment sources:
  BRA/CHN/IND/ZAF/RUS: no reliable monthly source, columns left blank
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

# Countries routed to BIS CBPOL for policy rates
BIS_RATE_COUNTRIES = {
    "CAN": "CA",
    "GBR": "GB",
    "JPN": "JP",
    "IND": "IN",
    "ZAF": "ZA",
    "BRA": "BR",
    "RUS": "RU",
}

# CPI index series - YoY computed from index levels
# JPN excluded - uses CPI_YOY_SERIES
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

# Countries where FRED provides a pre-computed YoY CPI rate directly
CPI_YOY_SERIES = {
    "JPN": "CPALTT01JPM657N",
}

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

# "BIS" = use bis_fetch_policy_rates(), None = no data
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

    return result


def compute_cpi_yoy_incremental(new_date, new_val, raw_base):
    """Compute YoY for a single new month given base data dict."""
    dt = datetime.strptime(new_date, "%Y-%m-%d")
    prior_key = (dt - relativedelta(months=12)).strftime("%Y-%m-%d")
    prior_val = raw_base.get(prior_key)
    if new_val is not None and prior_val is not None and prior_val != 0:
        return round((new_val / prior_val - 1) * 100, 2)
    return None


def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def get_last_date_in_tab(service, sheet_id, tab_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A:A"
    ).execute()
    values = result.get("values", [])
    data_rows = [r[0] for r in values[1:] if r]
    return data_rows[-1] if data_rows else None


def dates_to_append(last_date_str):
    last = datetime.strptime(last_date_str, "%Y-%m-%d")
    today = date.today()
    end = date(today.year, today.month, 1)
    new_dates = []
    current = last + relativedelta(months=1)
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
    body = {"values": rows}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    print(f"  {tab_name}: appended {len(rows)} row(s): {[r[0] for r in rows]}")


def update_inflation(service, dry_run):
    print("Inflation:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Inflation")
    if not last_date:
        print("  No data found - run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return

    print(f"  Last date: {last_date}, fetching up to {new_dates[-1]}")
    base_start = (datetime.strptime(new_dates[0], "%Y-%m-%d") - relativedelta(months=13)).strftime("%Y-%m-%d")

    # Standard index series - need 13 months of history to compute YoY for the new month
    raw_by_country = {}
    for country, series in CPI_SERIES.items():
        try:
            raw_by_country[country] = fred_fetch(series, base_start)
        except Exception as e:
            print(f"  {country}: FAILED ({e})")
            raw_by_country[country] = {}

    # Pre-computed YoY series - fetch from new_dates[0] directly, no base needed
    yoy_precomputed = {}
    for country, series in CPI_YOY_SERIES.items():
        try:
            raw = fred_fetch(series, new_dates[0])
            yoy_precomputed[country] = {
                k: round(v, 2) if v is not None else None for k, v in raw.items()
            }
        except Exception as e:
            print(f"  {country} (pre-computed YoY): FAILED ({e})")
            yoy_precomputed[country] = {}

    rows = []
    for d in new_dates:
        row = [d]
        for country in COUNTRIES:
            if country in CPI_YOY_SERIES:
                val = yoy_precomputed.get(country, {}).get(d)
                row.append(val if val is not None else "")
            else:
                raw = raw_by_country.get(country, {})
                new_val = raw.get(d)
                yoy = compute_cpi_yoy_incremental(d, new_val, raw)
                row.append(yoy if yoy is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Inflation", rows, dry_run)


def update_unemployment(service, dry_run):
    print("Unemployment:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Unemployment")
    if not last_date:
        print("  No data found - run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return

    print(f"  Last date: {last_date}, fetching up to {new_dates[-1]}")

    data_by_country = {}
    for country in COUNTRIES:
        series = UNEMP_SERIES[country]
        if series is None:
            data_by_country[country] = {}
            continue
        try:
            data_by_country[country] = fred_fetch(series, new_dates[0])
        except Exception as e:
            print(f"  {country}: FAILED ({e})")
            data_by_country[country] = {}

    rows = []
    for d in new_dates:
        row = [d]
        for country in COUNTRIES:
            val = data_by_country[country].get(d)
            row.append(round(val, 2) if val is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Unemployment", rows, dry_run)


def update_policy_rate(service, dry_run):
    print("Policy Rate:")
    last_date = get_last_date_in_tab(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate")
    if not last_date:
        print("  No data found - run populate_monthly_actuals.py first")
        return
    new_dates = dates_to_append(last_date)
    if not new_dates:
        print(f"  Up to date (last: {last_date})")
        return

    print(f"  Last date: {last_date}, fetching up to {new_dates[-1]}")

    data_by_country = {}
    fetched_ecb = None
    bis_data = None

    for country in COUNTRIES:
        series = RATE_SERIES[country]
        if series is None:
            data_by_country[country] = {}
        elif series == "BIS":
            if bis_data is None:
                try:
                    bis_data = bis_fetch_policy_rates(new_dates[0])
                except Exception as e:
                    print(f"  BIS: FAILED ({e})")
                    bis_data = {c: {} for c in BIS_RATE_COUNTRIES}
            data_by_country[country] = bis_data.get(country, {})
        elif series == "ECBMRRFR":
            if fetched_ecb is None:
                try:
                    raw = fred_fetch(series, new_dates[0])
                    fetched_ecb = {k: round(v, 2) if v is not None else None for k, v in raw.items()}
                except Exception as e:
                    print(f"  ECB: FAILED ({e})")
                    fetched_ecb = {}
            data_by_country[country] = fetched_ecb
        else:
            try:
                raw = fred_fetch(series, new_dates[0])
                data_by_country[country] = {k: round(v, 2) if v is not None else None for k, v in raw.items()}
            except Exception as e:
                print(f"  {country}: FAILED ({e})")
                data_by_country[country] = {}

    rows = []
    for d in new_dates:
        row = [d]
        for country in COUNTRIES:
            val = data_by_country[country].get(d)
            row.append(val if val is not None else "")
        rows.append(row)

    append_rows(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate", rows, dry_run)


def main():
    dry_run = "--dry-run" in sys.argv

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not found in .env")
        sys.exit(1)
    if not MACRO_MONTHLY_SHEET_ID:
        print("ERROR: MACRO_MONTHLY_SHEET_ID not found in .env")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}update_monthly_actuals.py")
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
