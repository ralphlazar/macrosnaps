#!/usr/bin/env python3
"""
update_monthly_actuals.py — Incremental update to MACRO-MONTHLY sheet.
Reads the last date in each tab, fetches only new months, appends new rows.
Safe to run daily — idempotent, skips rows that already exist.

Sources: same as populate_monthly_actuals.py.

Usage:
  python3 update_monthly_actuals.py                     # dry run — print preview only
  python3 update_monthly_actuals.py --apply             # append new rows to sheet
  python3 update_monthly_actuals.py --backfill          # scan for blank cells in existing rows, preview fills
  python3 update_monthly_actuals.py --backfill --apply  # scan and write blank cell fills to sheet
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

APPLY       = '--apply'    in sys.argv
BACKFILL    = '--backfill' in sys.argv
TODAY       = date.today()

COUNTRIES   = ['USA', 'CAN', 'GBR', 'JPN', 'DEU', 'FRA', 'ITA', 'CHN', 'IND', 'ZAF', 'BRA', 'RUS']

SHEET_ID    = os.environ.get('MACRO_MONTHLY_SHEET_ID')
KEY_FILE    = os.path.join(os.path.dirname(__file__), 'market-stats-key.json')
FRED_KEY    = os.environ.get('FRED_API_KEY', '')

# USA and BRA removed from IMF LS — USA uses FRED instead (BRA has no viable monthly source)
UNEMP_IMF   = ['CAN', 'JPN', 'DEU', 'FRA', 'ITA', 'RUS']
UNEMP_BLANK = ['CHN', 'IND', 'ZAF']  # BRA now fetched from IBGE SIDRA

# IBGE SIDRA API — PNAD Contínua monthly unemployment (table 6381, variable 4099)
IBGE_SIDRA_URL = (
    'https://apisidra.ibge.gov.br/values/t/6381/n1/all/v/4099'
    '/p/all/d/v4099%201'
)

# FRED series for unemployment countries not covered by IMF LS
UNEMP_FRED = {
    'USA': 'UNRATE',              # BLS — current to within weeks
    'GBR': 'LRHUTTTTGBM156S',    # ONS via FRED — ~5mo lag
}

BIS_RATE_COUNTRIES = {
    'CAN': 'CA',
    'GBR': 'GB',
    'JPN': 'JP',
    'ZAF': 'ZA',
    'BRA': 'BR',
    'RUS': 'RU',
    # IND removed — BIS WS_CBPOL stops Aug 2016, FRED INTDSRINM193N also stops 2016. No current source.
}

RATE_SERIES_FRED = {
    'USA': 'FEDFUNDS',
    'DEU': 'ECBMRRFR',
    'FRA': 'ECBMRRFR',
    'ITA': 'ECBMRRFR',
    # IND: RBI repo rate not available as a live monthly series from BIS or FRED — permanent blank
    'CHN': None,
}

# ONS public API — CPI All Items 12-month rate (not CPIH).
# Series D7G7 in dataset MM23 is the figure on every AQA mark scheme.
# Used to override the IMF CPI feed for GBR (IMF returns CPIH for UK).
ONS_CPI_URL = 'https://api.ons.gov.uk/v1/timeseries/D7BT/dataset/MM23/data'

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

def fetch_gbr_cpi_ons():
    """
    Fetch UK CPI All Items 12-month rate from ONS public API.
    Series D7G7 / dataset MM23. Returns {date: float} for all available months.
    Values are already annual % change — e.g. 11.1 for Oct 2022.
    """
    from datetime import datetime
    r = requests.get(ONS_CPI_URL, timeout=30)
    r.raise_for_status()
    months = r.json().get('months', [])
    out = {}
    for item in months:
        raw   = item.get('date', '').strip()   # e.g. "2022 OCT"
        value = item.get('value', '').strip()
        if not raw or not value or value == '-':
            continue
        try:
            d = datetime.strptime(raw.title(), '%Y %b').date().replace(day=1)
            out[d] = round(float(value), 2)
        except (ValueError, TypeError):
            pass
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
    # ONS fallback: GBR (IMF dataset returns CPIH for UK, not CPI)
    try:
        all_gbr = fetch_gbr_cpi_ons()
        gbr_yoy = {d: v for d, v in all_gbr.items() if d in new_dates}
        result['GBR'] = gbr_yoy
        if gbr_yoy:
            print(f'  GBR (ONS D7G7/MM23): {len(gbr_yoy)} new months  last={max(gbr_yoy.values()):.2f}')
        else:
            print(f'  GBR (ONS D7G7/MM23): no new data')
    except Exception as e:
        print(f'  GBR (ONS D7G7/MM23): error — {e}  (IMF CPIH value retained)')

    any_new = {c: v for c, v in result.items() if v}
    if not any_new:
        print('  No new data found.')
    return result

def fetch_ibge_bra(new_dates):
    """
    Fetch BRA unemployment from IBGE SIDRA table 6381 (PNAD Contínua).
    Period key D3C format: '202503' = rolling quarter ending March 2025.
    Returns dict of {date: float} for dates in new_dates.
    """
    try:
        r = requests.get(IBGE_SIDRA_URL, timeout=30)
        r.raise_for_status()
        data = r.json()
        result = {}
        for item in data[1:]:  # skip header row
            period = item.get('D3C', '')
            value  = item.get('V', '')
            if len(period) != 6 or not value or value.strip() in ('-', '...', ''):
                continue
            try:
                d = date(int(period[:4]), int(period[4:6]), 1)
                if d in new_dates:
                    result[d] = round(float(value), 2)
            except (ValueError, IndexError):
                continue
        return result
    except Exception as e:
        print(f'  BRA (IBGE SIDRA): error — {e}')
        return {}


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

    # FRED fallbacks: USA (BLS), GBR (ONS)
    for country, sid in UNEMP_FRED.items():
        try:
            all_data = fred_fetch(sid, fetch_start)
            new = {k: round(v, 2) for k, v in all_data.items() if k in new_dates}
            if new:
                print(f'  {country} ({sid}): {len(new)} new months  last={max(new)}')
            result[country] = new
        except Exception as e:
            print(f'  {country} ({sid}): FRED error — {e}')

    # IBGE SIDRA: BRA (PNAD Contínua monthly)
    bra_data = fetch_ibge_bra(set(new_dates))
    if bra_data:
        print(f'  BRA (IBGE SIDRA): {len(bra_data)} new months  last={max(bra_data)}')
    result['BRA'] = bra_data

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

# ── Backfill helpers ──────────────────────────────────────────────────────────

# Maps tab name → which countries are permanently blank (never fill these)
KNOWN_BLANKS = {
    'Inflation':    [],
    'Unemployment': ['CHN', 'IND', 'ZAF'],           # BRA now fetched from IBGE SIDRA
    'Policy_Rate':  ['CHN', 'IND'],                  # IND: RBI repo rate not available monthly from BIS/FRED
}

def col_letter(n):
    """Convert 1-based column index to A1 letter notation."""
    result = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

def scan_blanks(wb):
    """
    Scan all three tabs for blank cells in existing rows.
    Returns dict: { tab_name: { country: [(sheet_row_1based, date), ...] } }
    Skips countries in KNOWN_BLANKS for that tab.
    """
    print('\nScanning MACRO-MONTHLY for blank cells in existing rows...')
    gaps = {}

    for tab_name in ['Inflation', 'Unemployment', 'Policy_Rate']:
        ws        = wb.worksheet(tab_name)
        all_vals  = ws.get_all_values()
        if not all_vals:
            continue

        headers   = all_vals[0]
        data_rows = all_vals[1:]

        col_idx = {}
        for country in COUNTRIES:
            if country in headers:
                col_idx[country] = headers.index(country)

        tab_gaps = {}
        skip     = KNOWN_BLANKS.get(tab_name, [])

        for country in COUNTRIES:
            if country in skip:
                continue
            if country not in col_idx:
                continue
            cidx         = col_idx[country]
            country_gaps = []
            for i, row in enumerate(data_rows):
                cell_val = row[cidx].strip() if cidx < len(row) else ''
                date_val = row[0].strip()    if row else ''
                if not date_val:
                    continue
                if cell_val == '':
                    try:
                        d         = parse_sheet_date(date_val)
                        sheet_row = i + 2   # +1 for header, +1 for 1-based
                        country_gaps.append((sheet_row, d))
                    except ValueError:
                        pass
            if country_gaps:
                tab_gaps[country] = country_gaps

        if tab_gaps:
            gaps[tab_name] = tab_gaps
            total              = sum(len(v) for v in tab_gaps.values())
            countries_affected = list(tab_gaps.keys())
            print(f'  {tab_name}: {total} blank cell(s) across {countries_affected}')
        else:
            print(f'  {tab_name}: no gaps found')

    return gaps

def fetch_for_backfill(gaps):
    """Fetch data to fill identified gaps. One fetch call per data source."""
    fetched = {}

    for tab_name, tab_gaps in gaps.items():
        all_dates = sorted({d for gaps_list in tab_gaps.values() for _, d in gaps_list})
        if not all_dates:
            continue

        fetch_start = all_dates[0] - relativedelta(months=13)
        date_set    = set(all_dates)
        print(f'\nFetching {tab_name} ({all_dates[0]} → {all_dates[-1]})...')

        if tab_name == 'Inflation':
            fetched['Inflation']    = fetch_inflation(fetch_start, date_set)
        elif tab_name == 'Unemployment':
            fetched['Unemployment'] = fetch_unemployment(fetch_start, date_set)
        elif tab_name == 'Policy_Rate':
            fetched['Policy_Rate']  = fetch_policy_rate(fetch_start, date_set)

    return fetched

def apply_backfill(wb, gaps, fetched, apply=False):
    """Write (or preview) values for every blank cell identified in gaps."""
    print()
    total_fills  = 0
    total_blanks = 0

    for tab_name, tab_gaps in gaps.items():
        ws      = wb.worksheet(tab_name)
        headers = ws.row_values(1)
        updates  = []
        previews = []

        for country, gap_list in tab_gaps.items():
            if country not in headers:
                continue
            col_num  = headers.index(country) + 1
            col_ltr  = col_letter(col_num)
            tab_data = fetched.get(tab_name, {}).get(country, {})

            for sheet_row, d in gap_list:
                val = tab_data.get(d)
                if val is not None and val != '':
                    cell_ref = f'{col_ltr}{sheet_row}'
                    updates.append({'range': cell_ref, 'values': [[str(val)]]})
                    previews.append((country, d, sheet_row, col_ltr, val))
                    total_fills += 1
                else:
                    previews.append((country, d, sheet_row, col_ltr, None))
                    total_blanks += 1

        if previews:
            print(f'{tab_name}:')
            for (c, d, row, col, v) in previews:
                status = f'→ {v}' if v is not None else '(no data from source)'
                print(f'  {c:<6} {d}  row {row:<5} {col}  {status}')

        if apply and updates:
            ws.batch_update(updates, value_input_option='RAW')
            print(f'  ✓ {tab_name}: wrote {len(updates)} cell(s)')

    print(f'\nBackfill summary: {total_fills} cell(s) filled, {total_blanks} cell(s) had no source data.')
    if not apply:
        print('Dry run — pass --apply to write.')

def run_backfill(wb):
    gaps = scan_blanks(wb)
    if not any(gaps.values()):
        print('\nNo gaps found. Nothing to backfill.')
        return
    fetched = fetch_for_backfill(gaps)
    apply_backfill(wb, gaps, fetched, apply=APPLY)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    mode = 'APPLY' if APPLY else 'DRY run'
    if BACKFILL:
        print(f'update_monthly_actuals.py  [BACKFILL — {mode}]\n')
    else:
        print(f'update_monthly_actuals.py  [{mode}]\n')

    if not SHEET_ID:
        print('ERROR: MACRO_MONTHLY_SHEET_ID env var not set.')
        sys.exit(1)

    wb = get_workbook()

    if BACKFILL:
        run_backfill(wb)
        return

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
