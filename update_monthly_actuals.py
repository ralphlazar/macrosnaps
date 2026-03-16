#!/usr/bin/env python3
"""
update_monthly_actuals.py — Incremental update to MACRO-MONTHLY sheet.
Reads the last date in each tab, fetches only new months, appends new rows.
Safe to run daily — idempotent, skips rows that already exist.

Sources: same as populate_monthly_actuals.py.

Usage:
  python3 update_monthly_actuals.py           # dry run — print preview only
  python3 update_monthly_actuals.py --apply   # append new rows to sheet
"""

import os, sys, csv, io, warnings
from datetime import date
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

warnings.filterwarnings('ignore', message='.*structure.*')
import sdmx

# ── Config ────────────────────────────────────────────────────────────────────

APPLY       = '--apply' in sys.argv
TODAY       = date.today()

COUNTRIES   = ['USA', 'CAN', 'GBR', 'JPN', 'DEU', 'FRA', 'ITA', 'CHN', 'IND', 'ZAF', 'BRA', 'RUS']

SHEET_ID    = os.environ.get('MACRO_MONTHLY_SHEET_ID')
KEY_FILE    = os.path.join(os.path.dirname(__file__), 'market-stats-key.json')
FRED_KEY    = os.environ.get('FRED_API_KEY', '')

UNEMP_IMF   = ['USA', 'CAN', 'JPN', 'DEU', 'FRA', 'ITA', 'BRA', 'RUS']
UNEMP_BLANK = ['CHN', 'IND', 'ZAF']

BIS_RATE_COUNTRIES = {
    'CAN': 'CA',
    'GBR': 'GB',
    'JPN': 'JP',
    'IND': 'IN',
    'ZAF': 'ZA',
    'BRA': 'BR',
    'RUS': 'RU',
}

RATE_SERIES_FRED = {
    'USA': 'FEDFUNDS',
    'DEU': 'ECBMRRFR',
    'FRA': 'ECBMRRFR',
    'ITA': 'ECBMRRFR',
    'CHN': None,
}

# ── Utilities ─────────────────────────────────────────────────────────────────

def months_between(start, end):
    result, d = [], start.replace(day=1)
    while d <= end.replace(day=1):
        result.append(d)
        d += relativedelta(months=1)
    return result

def fmt(d):
    return d.strftime('%d/%m/%Y')

def parse_sheet_date(s):
    from datetime import datetime
    return datetime.strptime(s.strip(), '%d/%m/%Y').date()

def parse_imf_period(tp):
    y, m = tp.split('-M')
    return date(int(y), int(m), 1)

def fred_fetch(series_id, start):
    url = 'https://api.stlouisfed.org/fred/series/observations'
    r = requests.get(url, params={
        'series_id':          series_id,
        'api_key':            FRED_KEY,
        'file_type':          'json',
        'frequency':          'm',
        'aggregation_method': 'avg',
        'observation_start':  start.strftime('%Y-%m-%d'),
    }, timeout=30)
    r.raise_for_status()
    from datetime import datetime
    out = {}
    for obs in r.json().get('observations', []):
        if obs['value'] == '.':
            continue
        d = datetime.strptime(obs['date'], '%Y-%m-%d').date().replace(day=1)
        out[d] = float(obs['value'])
    return out

def bis_fetch_policy_rates(start):
    bis_codes = '+'.join(BIS_RATE_COUNTRIES.values())
    url = f'https://stats.bis.org/api/v1/data/WS_CBPOL/M.{bis_codes}/all'
    params = {'format': 'csv', 'startPeriod': start.strftime('%Y-%m')}
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    bis_to_country = {v: k for k, v in BIS_RATE_COUNTRIES.items()}
    result = {c: {} for c in BIS_RATE_COUNTRIES}
    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        ref_area    = row.get('REF_AREA',    '').strip()
        time_period = row.get('TIME_PERIOD', '').strip()
        obs_value   = row.get('OBS_VALUE',   '').strip()
        country = bis_to_country.get(ref_area)
        if country and time_period and obs_value:
            try:
                d = date(int(time_period[:4]), int(time_period[5:7]), 1)
                result[country][d] = round(float(obs_value), 2)
            except (ValueError, TypeError):
                pass
    return result

def imf_fetch(dataset, key, start):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        c = sdmx.Client('IMF_DATA')
        msg = c.data(dataset, key=key, params={'startPeriod': start.strftime('%Y-%m')})
    df = sdmx.to_pandas(msg).reset_index()
    return df[df['value'].notna()]

# ── Sheet helpers ─────────────────────────────────────────────────────────────

def get_workbook():
    creds = Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def get_last_date(wb, tab_name):
    ws = wb.worksheet(tab_name)
    col = ws.col_values(1)
    dates = []
    for v in col[1:]:
        v = v.strip()
        if v:
            try:
                dates.append(parse_sheet_date(v))
            except ValueError:
                pass
    return max(dates) if dates else None

def append_rows(wb, tab_name, new_rows):
    ws = wb.worksheet(tab_name)
    ws.append_rows(new_rows, value_input_option='RAW')
    print(f'  {tab_name}: appended {len(new_rows)} rows')

# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_inflation(fetch_start, new_dates):
    print('Fetching CPI from IMF (dataset: CPI)...')
    key = '+'.join(COUNTRIES) + '.CPI._T.IX.M'
    df = imf_fetch('CPI', key, fetch_start)
    result = {}
    for country in COUNTRIES:
        cdf = df[df['COUNTRY'] == country].copy()
        if cdf.empty:
            result[country] = {}
            continue
        cdf['date'] = cdf['TIME_PERIOD'].apply(parse_imf_period)
        cdf = cdf.sort_values('date').set_index('date')['value']
        yoy = {}
        for d in new_dates:
            prev = d - relativedelta(years=1)
            if d in cdf.index and prev in cdf.index and cdf[prev] != 0:
                yoy[d] = round((cdf[d] / cdf[prev] - 1) * 100, 2)
        result[country] = yoy
    any_new = {c: v for c, v in result.items() if v}
    for country, yoy in any_new.items():
        print(f'  {country}: {len(yoy)} new months  last={max(yoy)}')
    if not any_new:
        print('  No new data found.')
    return result

def fetch_unemployment(fetch_start, new_dates):
    print('Fetching Unemployment from IMF (dataset: LS)...')
    key = '+'.join(UNEMP_IMF) + '.U.PT.M'
    df = imf_fetch('LS', key, fetch_start)
    result = {}
    for country in UNEMP_IMF:
        cdf = df[df['COUNTRY'] == country].copy()
        if cdf.empty:
            result[country] = {}
            continue
        cdf['date'] = cdf['TIME_PERIOD'].apply(parse_imf_period)
        series = {r['date']: round(r['value'], 2)
                  for _, r in cdf.iterrows() if r['date'] in new_dates}
        if series:
            print(f'  {country}: {len(series)} new months  last={max(series)}')
        result[country] = series
    try:
        gbr_all = fred_fetch('LRHUTTTTGBM156S', fetch_start)
        gbr = {k: round(v, 2) for k, v in gbr_all.items() if k in new_dates}
        if gbr:
            print(f'  GBR: {len(gbr)} new months  last={max(gbr)}')
        result['GBR'] = gbr
    except Exception as e:
        print(f'  GBR: FRED error — {e}')
        result['GBR'] = {}
    for country in UNEMP_BLANK:
        result[country] = {}
    return result

def fetch_policy_rate(fetch_start, new_dates):
    print('Fetching Policy Rates...')
    result = {}
    try:
        bis_data = bis_fetch_policy_rates(fetch_start)
        for country in BIS_RATE_COUNTRIES:
            new = {k: v for k, v in bis_data.get(country, {}).items() if k in new_dates}
            if new:
                print(f'  BIS {country}: {len(new)} new months  last={max(new)}')
            result[country] = new
    except Exception as e:
        print(f'  BIS: FAILED — {e}')
        for country in BIS_RATE_COUNTRIES:
            result[country] = {}
    cache = {}
    for country, sid in RATE_SERIES_FRED.items():
        if sid is None:
            result[country] = {}
            continue
        if sid not in cache:
            try:
                cache[sid] = fred_fetch(sid, fetch_start)
            except Exception as e:
                print(f'  {sid}: FRED error — {e}')
                cache[sid] = {}
        new = {k: round(v, 4) for k, v in cache[sid].items() if k in new_dates}
        if new:
            print(f'  {country} ({sid}): {len(new)} new months  last={max(new)}')
        result[country] = new
    return result

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'update_monthly_actuals.py  [{"APPLY" if APPLY else "DRY run"}]\n')

    if not SHEET_ID:
        print('ERROR: MACRO_MONTHLY_SHEET_ID env var not set.')
        sys.exit(1)

    wb = get_workbook()

    last_dates = {}
    for tab in ['Inflation', 'Unemployment', 'Policy_Rate']:
        last_dates[tab] = get_last_date(wb, tab)
        print(f'{tab}: last date = {last_dates[tab]}')

    ref_last = min(d for d in last_dates.values() if d is not None)
    first_new = ref_last + relativedelta(months=1)

    if first_new.replace(day=1) > TODAY.replace(day=1):
        print('\nAll tabs up to date. Nothing to do.')
        return

    new_dates = months_between(first_new, TODAY)
    print(f'\nNew dates to add: {fmt(new_dates[0])} → {fmt(new_dates[-1])} ({len(new_dates)} months)\n')

    fetch_start = first_new - relativedelta(months=13)

    inflation    = fetch_inflation(fetch_start, set(new_dates));    print()
    unemployment = fetch_unemployment(fetch_start, set(new_dates)); print()
    policy_rate  = fetch_policy_rate(fetch_start, set(new_dates));  print()

    def build_rows(data, dates):
        rows = []
        for d in dates:
            row = [fmt(d)]
            for c in COUNTRIES:
                v = data.get(c, {}).get(d, '')
                row.append('' if v == '' else str(v))
            rows.append(row)
        return rows

    rows_inf   = build_rows(inflation,    new_dates)
    rows_unemp = build_rows(unemployment, new_dates)
    rows_rate  = build_rows(policy_rate,  new_dates)

    print('Preview (new rows):')
    header = ['Date'] + COUNTRIES
    for name, rows in [('Inflation', rows_inf), ('Unemployment', rows_unemp), ('Policy_Rate', rows_rate)]:
        print(f'\n{name}:')
        df = pd.DataFrame(rows, columns=header)
        print(df.to_string(index=False))

    if not APPLY:
        print('\nDry run complete — pass --apply to write to sheet.')
        return

    print('\nAppending to MACRO-MONTHLY sheet...')
    append_rows(wb, 'Inflation',    rows_inf)
    append_rows(wb, 'Unemployment', rows_unemp)
    append_rows(wb, 'Policy_Rate',  rows_rate)
    print('\nDone.')

if __name__ == '__main__':
    main()
