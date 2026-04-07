#!/usr/bin/env python3
"""
rebuild_unemployment_historical.py
====================================
Rebuilds _frozen_historical['Unemployment'] for all 12 countries by
reading the full MACRO-MONTHLY Unemployment tab directly from Google Sheets.

The sheet is the source of truth. startDate is derived from the first
non-null row per country — no hardcoded dates, no patch assumptions.

Countries with no data (CHN, and any others with empty columns) are skipped
— their existing entries in data.json are left untouched.

Run from the macrosnaps repo directory:
    python3 ~/Downloads/rebuild_unemployment_historical.py          # dry run
    python3 ~/Downloads/rebuild_unemployment_historical.py --apply  # write to data.json
"""

import os, sys, json
from datetime import date
from dateutil.relativedelta import relativedelta

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

APPLY     = '--apply' in sys.argv
SHEET_ID  = os.getenv('MACRO_MONTHLY_SHEET_ID')
KEY_FILE  = os.path.join(os.path.dirname(__file__), 'market-stats-key.json')
DATA_JSON = os.path.join(os.path.dirname(__file__), 'data.json')

COUNTRIES = ['USA', 'CAN', 'GBR', 'JPN', 'DEU', 'FRA', 'ITA', 'CHN', 'IND', 'ZAF', 'BRA', 'RUS']

# CHN has no free programmatic unemployment source — permanent blank.
# IND and ZAF have annual data interpolated quarterly; they will rebuild
# from whatever is in the sheet.
KNOWN_BLANKS = {'CHN'}


def get_service():
    creds = Credentials.from_service_account_file(
        KEY_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return build('sheets', 'v4', credentials=creds)


def parse_date(s):
    from datetime import datetime
    return datetime.strptime(s.strip(), '%d/%m/%Y').date().replace(day=1)


def read_tab(service):
    """
    Returns {country: {date: float}} for all countries, all rows.
    Sheet is oldest-first. Dates are DD/MM/YYYY.
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range='Unemployment'
    ).execute()
    rows = result.get('values', [])
    if len(rows) < 2:
        print('ERROR: Unemployment tab is empty.')
        sys.exit(1)

    header = rows[0]
    col = {}
    for country in COUNTRIES:
        if country in header:
            col[country] = header.index(country)

    data = {c: {} for c in COUNTRIES}
    skipped = 0

    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        try:
            d = parse_date(row[0])
        except ValueError:
            skipped += 1
            continue
        for country in COUNTRIES:
            idx = col.get(country)
            if idx is None or idx >= len(row):
                continue
            cell = row[idx].strip()
            if cell in ('', '-', 'N/A', 'n/a'):
                continue
            try:
                data[country][d] = round(float(cell), 2)
            except ValueError:
                pass

    if skipped:
        print(f'  Skipped {skipped} rows with unparseable dates.')
    return data


def build_series(country_data):
    """
    Given {date: float}, return (startDate_str, v_list).
    Builds a continuous monthly array from first to last data point.
    Gaps filled with None.
    """
    if not country_data:
        return None, []

    dates = sorted(country_data.keys())
    start = dates[0]
    end   = dates[-1]

    v = []
    d = start
    while d <= end:
        v.append(country_data.get(d))
        d += relativedelta(months=1)

    return start.strftime('%Y-%m'), v


def main():
    mode = 'APPLY' if APPLY else 'DRY RUN'
    print(f'\nrebuild_unemployment_historical.py  [{mode}]\n')

    if not SHEET_ID:
        print('ERROR: MACRO_MONTHLY_SHEET_ID not set in .env')
        sys.exit(1)

    print('Reading MACRO-MONTHLY Unemployment tab...')
    service      = get_service()
    country_data = read_tab(service)
    print()

    print(f'  {"Country":<6}  {"Points":>6}  {"Start":>10}  {"End":>10}  {"Nulls":>6}')
    print(f'  {"-"*46}')

    results = {}
    for country in COUNTRIES:
        if country in KNOWN_BLANKS:
            print(f'  {country:<6}  (known blank — skipped)')
            continue
        start_str, v = build_series(country_data[country])
        if not v:
            print(f'  {country:<6}  NO DATA (skipped)')
            continue
        nulls = sum(1 for x in v if x is None)
        sy, sm = map(int, start_str.split('-'))
        total  = sy * 12 + (sm - 1) + len(v) - 1
        ey, em = total // 12, total % 12 + 1
        end_str = f'{ey}-{em:02d}'
        print(f'  {country:<6}  {len(v):>6}  {start_str:>10}  {end_str:>10}  {nulls:>6}')
        results[country] = (start_str, v)

    print()

    if not APPLY:
        print('Dry run complete. Run with --apply to write to data.json.')
        return

    print('Writing to data.json...')
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    for country, (start_str, v) in results.items():
        c = data.get('countries', {}).get(country)
        if not c:
            print(f'  WARNING: {country} not found in data.json')
            continue
        fh = c.setdefault('_frozen_historical', {})
        fh['Unemployment'] = {
            'type':      'line',
            'startDate': start_str,
            'v':         v
        }
        updated += 1

    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'  Updated _frozen_historical Unemployment for {updated} countries.')
    print('\n  Done. Run build.py to rebuild.\n')


if __name__ == '__main__':
    main()
