#!/usr/bin/env python3
"""
populate_monthly_actuals.py — Full historical backfill to MACRO-MONTHLY sheet.
Clears and rewrites all three tabs: Inflation, Unemployment, Policy_Rate.
Range: Jan 2000 → present.

Sources:
  Inflation:    IMF new SDMX API — dataset CPI, key COUNTRY.CPI._T.IX.M
                YoY % computed from monthly index levels (fetched from Jan 1999).
  Unemployment: IMF new SDMX API — dataset LS, key COUNTRY.U.PT.M
                GBR fallback: FRED LRHUTTTTGBM156S
                CHN, IND, ZAF: permanent blanks (no coverage)
  Policy_Rate:  USA: FRED FEDFUNDS
                DEU/FRA/ITA: FRED ECBMRRFR
                CAN/GBR/JPN/IND/ZAF/BRA/RUS: BIS WS_CBPOL API
                CHN, RUS: permanent blanks

Usage:
  python3 populate_monthly_actuals.py           # dry run — print preview only
  python3 populate_monthly_actuals.py --apply   # write to sheet
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

APPLY           = '--apply' in sys.argv
START           = date(2000, 1, 1)
CPI_FETCH_START = date(1999, 1, 1)   # 12 extra months for YoY computation
TODAY           = date.today()

COUNTRIES   = ['USA', 'CAN', 'GBR', 'JPN', 'DEU', 'FRA', 'ITA', 'CHN', 'IND', 'ZAF', 'BRA', 'RUS']

SHEET_ID    = os.environ.get('MACRO_MONTHLY_SHEET_ID')
KEY_FILE    = os.path.join(os.path.dirname(__file__), 'market-stats-key.json')
FRED_KEY    = os.environ.get('FRED_API_KEY', '')

# Unemployment sources
UNEMP_IMF   = ['USA', 'CAN', 'JPN', 'DEU', 'FRA', 'ITA', 'BRA', 'RUS']
UNEMP_BLANK = ['CHN', 'IND', 'ZAF']

# Policy rate: BIS WS_CBPOL country codes
BIS_RATE_COUNTRIES = {
    'CAN': 'CA',
    'GBR': 'GB',
    'JPN': 'JP',
    'IND': 'IN',
    'ZAF': 'ZA',
    'BRA': 'BR',
    'RUS': 'RU',
}

# Policy rate: FRED series (non-BIS). None = permanent blank.
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
    for country in BIS_RATE_COUNTRIES:
        last = max(result[country]) if result[country] else None
        print(f'  BIS {country}: {len(result[country])} months  last={last}')
    return result

def imf_fetch(dataset, key, start):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        c = sdmx.Client('IMF_DATA')
        msg = c.data(dataset, key=key, params={'startPeriod': start.strftime('%Y-%m')})
    df = sdmx.to_pandas(msg).reset_index()
    return df[df['value'].notna()]

def build_sheet_df(dates, data):
    rows = []
    for d in dates:
        row = {'Date': fmt(d)}
        for c in COUNTRIES:
            v = data.get(c, {}).get(d, '')
            row[c] = v
        rows.append(row)
    return pd.DataFrame(rows, columns=['Date'] + COUNTRIES)

# ── Inflation ─────────────────────────────────────────────────────────────────

def fetch_inflation():
    print('Fetching CPI from IMF (dataset: CPI)...')
    key = '+'.join(COUNTRIES) + '.CPI._T.IX.M'
    df = imf_fetch('CPI', key, CPI_FETCH_START)
    result = {}
    for country in COUNTRIES:
        cdf = df[df['COUNTRY'] == country].copy()
        if cdf.empty:
            print(f'  {country}: NO DATA')
            result[country] = {}
            continue
        cdf['date'] = cdf['TIME_PERIOD'].apply(parse_imf_period)
        cdf = cdf.sort_values('date').set_index('date')['value']
        yoy = {}
        for d in months_between(START, TODAY):
            prev = d - relativedelta(years=1)
            if d in cdf.index and prev in cdf.index and cdf[prev] != 0:
                yoy[d] = round((cdf[d] / cdf[prev] - 1) * 100, 2)
        last = max(yoy) if yoy else None
        print(f'  {country}: {len(yoy)} months  last={last}')
        result[country] = yoy
    return result

# ── Unemployment ──────────────────────────────────────────────────────────────

def fetch_unemployment():
    print('Fetching Unemployment from IMF (dataset: LS)...')
    key = '+'.join(UNEMP_IMF) + '.U.PT.M'
    df = imf_fetch('LS', key, START)
    result = {}
    for country in UNEMP_IMF:
        cdf = df[df['COUNTRY'] == country].copy()
        if cdf.empty:
            print(f'  {country}: NO DATA')
            result[country] = {}
            continue
        cdf['date'] = cdf['TIME_PERIOD'].apply(parse_imf_period)
        series = dict(zip(cdf['date'], cdf['value'].round(2)))
        last = max(series) if series else None
        print(f'  {country}: {len(series)} months  last={last}')
        result[country] = series
    print('  GBR: fetching from FRED...')
    try:
        gbr = {k: round(v, 2) for k, v in fred_fetch('LRHUTTTTGBM156S', START).items()}
        print(f'  GBR: {len(gbr)} months  last={max(gbr) if gbr else None}')
        result['GBR'] = gbr
    except Exception as e:
        print(f'  GBR: FRED error — {e}')
        result['GBR'] = {}
    for country in UNEMP_BLANK:
        result[country] = {}
        print(f'  {country}: permanent blank')
    return result

# ── Policy Rate ───────────────────────────────────────────────────────────────

def fetch_policy_rate():
    print('Fetching Policy Rates...')
    result = {}
    print('  BIS (CAN/GBR/JPN/IND/ZAF/BRA/RUS): fetching WS_CBPOL...')
    try:
        bis_data = bis_fetch_policy_rates(START)
        for country in BIS_RATE_COUNTRIES:
            result[country] = bis_data.get(country, {})
    except Exception as e:
        print(f'  BIS: FAILED — {e}')
        for country in BIS_RATE_COUNTRIES:
            result[country] = {}
    cache = {}
    for country, sid in RATE_SERIES_FRED.items():
        if sid is None:
            result[country] = {}
            print(f'  {country}: permanent blank')
            continue
        if sid not in cache:
            try:
                data = {k: round(v, 4) for k, v in fred_fetch(sid, START).items()}
                cache[sid] = data
                print(f'  {sid} ({country}): {len(data)} months  last={max(data) if data else None}')
            except Exception as e:
                print(f'  {sid}: FRED error — {e}')
                cache[sid] = {}
        result[country] = cache[sid]
    return result

# ── Sheet ─────────────────────────────────────────────────────────────────────

def get_workbook():
    creds = Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def write_tab(wb, tab_name, df):
    ws = wb.worksheet(tab_name)
    ws.clear()
    values = [df.columns.tolist()] + [
        [str(v) if v != '' else '' for v in row]
        for row in df.values.tolist()
    ]
    ws.update(values, 'A1')
    print(f'  {tab_name}: wrote {len(df)} rows')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'populate_monthly_actuals.py  [{"APPLY" if APPLY else "DRY run"}]')
    print(f'Range: {fmt(START)} → {fmt(TODAY)}\n')

    dates = months_between(START, TODAY)

    inflation    = fetch_inflation();    print()
    unemployment = fetch_unemployment(); print()
    policy_rate  = fetch_policy_rate();  print()

    df_inf   = build_sheet_df(dates, inflation)
    df_unemp = build_sheet_df(dates, unemployment)
    df_rate  = build_sheet_df(dates, policy_rate)

    print('Preview (last 3 rows):')
    for name, df in [('Inflation', df_inf), ('Unemployment', df_unemp), ('Policy_Rate', df_rate)]:
        print(f'\n{name}:')
        print(df.tail(3).to_string(index=False))

    if not APPLY:
        print('\nDry run complete — pass --apply to write to sheet.')
        return

    if not SHEET_ID:
        print('\nERROR: MACRO_MONTHLY_SHEET_ID env var not set.')
        sys.exit(1)

    print('\nWriting to MACRO-MONTHLY sheet...')
    wb = get_workbook()
    write_tab(wb, 'Inflation',    df_inf)
    write_tab(wb, 'Unemployment', df_unemp)
    write_tab(wb, 'Policy_Rate',  df_rate)
    print('\nDone.')

if __name__ == '__main__':
    main()
