#!/usr/bin/env python3
"""
sync_monthly_actuals.py
Reads the last 6 non-null values per country per series from the MACRO-MONTHLY
Google Sheet and writes a monthly_actuals block into each country in data.json.

The monthly_actuals field is story context only - it is never displayed in the UI.

Run with --preview to print what would be written without touching data.json.
Run with --apply to write to data.json.
"""

import os
import sys
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

MACRO_MONTHLY_SHEET_ID = os.getenv("MACRO_MONTHLY_SHEET_ID")
KEY_FILE = os.path.join(os.path.dirname(__file__), "market-stats-key.json")
DATA_JSON = os.path.join(os.path.dirname(__file__), "data.json")

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]
MONTHS_TO_KEEP = 6


def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def read_tab(service, sheet_id, tab_name):
    """
    Read a full tab and return a dict of:
    {country_code: [(month_str, value), ...]} newest first, nulls excluded.
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=tab_name
    ).execute()
    values = result.get("values", [])
    if not values or len(values) < 2:
        return {c: [] for c in COUNTRIES}

    header = values[0]  # ["Date", "USA", "CAN", ...]
    country_cols = {}
    for country in COUNTRIES:
        if country in header:
            country_cols[country] = header.index(country)
        else:
            country_cols[country] = None

    # build per-country lists (all rows, newest first)
    per_country = {c: [] for c in COUNTRIES}
    for row in reversed(values[1:]):
        if not row:
            continue
        date_str = row[0] if row else None
        if not date_str:
            continue
        month_str = date_str[:7]  # YYYY-MM
        for country in COUNTRIES:
            col = country_cols[country]
            if col is None:
                continue
            if col < len(row) and row[col] not in ("", None):
                try:
                    val = round(float(row[col]), 2)
                    per_country[country].append({"month": month_str, "value": val})
                except (ValueError, TypeError):
                    pass

    # trim to last 6 non-null entries
    return {c: per_country[c][:MONTHS_TO_KEEP] for c in COUNTRIES}


def main():
    preview = "--preview" in sys.argv
    apply = "--apply" in sys.argv

    if not preview and not apply:
        print("Usage: python3 sync_monthly_actuals.py --preview | --apply")
        sys.exit(1)

    if not MACRO_MONTHLY_SHEET_ID:
        print("ERROR: MACRO_MONTHLY_SHEET_ID not found in .env")
        sys.exit(1)

    mode = "[PREVIEW]" if preview else "[APPLY]"
    print(f"{mode} sync_monthly_actuals.py")
    print()

    service = get_sheets_service()

    print("Reading Inflation tab...")
    inflation = read_tab(service, MACRO_MONTHLY_SHEET_ID, "Inflation")
    print("Reading Unemployment tab...")
    unemployment = read_tab(service, MACRO_MONTHLY_SHEET_ID, "Unemployment")
    print("Reading Policy_Rate tab...")
    policy_rate = read_tab(service, MACRO_MONTHLY_SHEET_ID, "Policy_Rate")
    print()

    # build the monthly_actuals block per country
    monthly_actuals = {}
    for country in COUNTRIES:
        monthly_actuals[country] = {
            "inflation": inflation[country],
            "unemployment": unemployment[country],
            "policy_rate": policy_rate[country],
        }

    # preview output
    print("Monthly actuals (last 6 non-null per series):")
    print("-" * 60)
    for country in COUNTRIES:
        ma = monthly_actuals[country]
        inf_latest = ma["inflation"][0] if ma["inflation"] else None
        unemp_latest = ma["unemployment"][0] if ma["unemployment"] else None
        rate_latest = ma["policy_rate"][0] if ma["policy_rate"] else None
        inf_str = f"{inf_latest['month']} {inf_latest['value']}%" if inf_latest else "no data"
        unemp_str = f"{unemp_latest['month']} {unemp_latest['value']}%" if unemp_latest else "no data"
        rate_str = f"{rate_latest['month']} {rate_latest['value']}%" if rate_latest else "no data"
        print(f"  {country}  inflation: {inf_str}  unemployment: {unemp_str}  policy_rate: {rate_str}")
    print()

    if preview:
        print("Preview complete. Run with --apply to write to data.json.")
        return

    # apply: write to data.json
    print("Writing to data.json...")
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for country in COUNTRIES:
        if country in data.get("countries", {}):
            data["countries"][country]["monthly_actuals"] = monthly_actuals[country]
            updated += 1
        else:
            print(f"  WARNING: {country} not found in data.json countries - skipped")

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Updated monthly_actuals for {updated} countries.")
    print()
    print("Done. Run python3 build.py to rebuild the output.")


if __name__ == "__main__":
    main()
