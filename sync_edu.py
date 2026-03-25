#!/usr/bin/env python3
"""
sync_edu.py
===========
Reads MacroSnaps data.json + most recent backup.
Writes edu-data.json to macedu/app/data/ with:
  - Snapshot: value + direction per country per concept
  - Charts: date-labelled historical series per concept

Run after build.py in the Daily Bash Ritual:
    python3 sync_edu.py

Historical series source: _frozen_historical in data.json.
All series start Jan 2000. Dates reconstructed from that anchor.
Chart windows per brief:
  - Inflation, unemployment, interest-rates: last 120 months (10 years)
  - GDP, trade: last 10 annual values
  - Exchange rates: last 36 months (3 years)
"""

import json
import os
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

MACROSNAPS_DIR = '/Users/lisaswerling/RALPH/AI/macrosnaps'
MACEDU_DATA    = '/Users/lisaswerling/RALPH/AI/macedu/app/data/edu-data.json'
TODAY          = date.today().isoformat()
DATA_FILE      = os.path.join(MACROSNAPS_DIR, 'data.json')
BACKUP_DIR     = os.path.join(MACROSNAPS_DIR, 'backups')

SERIES_START   = datetime(2000, 1, 1)
ANNUAL_START   = 2000

COUNTRY_MAP = {
    'GBR': 'uk',
    'USA': 'us',
    'DEU': 'eurozone',
    'CHN': 'china',
    'JPN': 'japan',
    'BRA': 'brazil',
}

FX_HIST_KEYS = {
    'GBR': 'GBP/USD',
    'USA': 'USD/DXY',
    'DEU': 'EUR/USD',
    'CHN': 'USD/CNY',
    'JPN': 'USD/JPY',
    'BRA': 'USD/BRL',
}

FX_DECIMALS = {
    'GBR': 2,
    'USA': 1,
    'DEU': 2,
    'CHN': 2,
    'JPN': 0,
    'BRA': 2,
}

def parse_num(val_str):
    if val_str is None:
        return None
    s = str(val_str).strip().replace('% GDP', '').replace('%', '').strip()
    try:
        return float(s)
    except ValueError:
        return None

def get_direction(new_val, old_val, threshold=0.05):
    if new_val is None or old_val is None:
        return 'flat'
    diff = new_val - old_val
    if abs(diff) < threshold:
        return 'flat'
    return 'up' if diff > 0 else 'down'

def get_fx_direction(new_val, old_val, threshold=0.001):
    if new_val is None or old_val is None or old_val == 0:
        return 'flat'
    if abs(new_val - old_val) / old_val < threshold:
        return 'flat'
    return 'up' if new_val > old_val else 'down'

def format_fx(val, decimals):
    if val is None:
        return None
    return str(int(round(val))) if decimals == 0 else f'{val:.{decimals}f}'

def get_macro_value(code, key, src):
    try:
        return src['countries'][code]['metrics']['macro'][key]['value']
    except (KeyError, TypeError):
        return None

def get_fx_raw(code, src):
    try:
        return src['countries'][code]['metrics']['market']['FX Rate']
    except (KeyError, TypeError):
        return None

def get_frozen(code, key, src):
    try:
        return src['countries'][code]['_frozen_historical'][key]['v']
    except (KeyError, TypeError):
        return []

def make_monthly_dates(n, fmt="%b %Y"):
    today = datetime.today()
    dates = []
    for i in range(n):
        d = SERIES_START + relativedelta(months=i)
        if d > today:
            break
        dates.append(d.strftime(fmt))
    return dates

def make_annual_dates(n):
    today = datetime.today()
    return [str(ANNUAL_START + i) for i in range(n) if ANNUAL_START + i <= today.year]

def tail(values, n):
    return values[-n:] if len(values) >= n else values

def tail_dates(all_dates, values, n):
    offset = len(all_dates) - len(values)
    aligned = all_dates[offset:]
    return aligned[-n:] if len(aligned) >= n else aligned

def round_series(values):
    return [round(float(v), 2) if v is not None else None for v in values]

# ── Load ──────────────────────────────────────────────────────────────────────

print(f'\nsync_edu.py — {TODAY}')
print('─' * 40)

with open(DATA_FILE, encoding='utf-8') as f:
    data = json.load(f)
print(f'Loaded:  {DATA_FILE}')

old_data = None
if os.path.isdir(BACKUP_DIR):
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith('data_') and f.endswith('.json')
    ], reverse=True)
    if backups:
        backup_path = os.path.join(BACKUP_DIR, backups[0])
        with open(backup_path, encoding='utf-8') as f:
            old_data = json.load(f)
        print(f'Backup:  {backup_path}')
    else:
        print('No backup found — directions will be flat.')
else:
    print('No backup directory — directions will be flat.')

ALL_MONTHLY = make_monthly_dates(320)
ALL_ANNUAL  = make_annual_dates(30)

edu = {'_meta': {'generated': TODAY}}

# ── Snapshots ─────────────────────────────────────────────────────────────────

SNAPSHOT_MAP = {
    'inflation':      'Inflation (CPI)',
    'unemployment':   'Unemployment',
    'gdp':            'GDP Growth',
    'interest-rates': 'Policy Rate',
    'trade':          'Current Account',
}

for slug, macro_key in SNAPSHOT_MAP.items():
    block = {}
    for code, country in COUNTRY_MAP.items():
        new_str = get_macro_value(code, macro_key, data)
        old_str = get_macro_value(code, macro_key, old_data) if old_data else None
        display  = new_str.replace(' GDP', '').strip() if new_str else new_str
        block[country] = {
            'value':     display,
            'direction': get_direction(parse_num(new_str), parse_num(old_str)),
        }
    edu[slug] = block

fx_block = {}
for code, country in COUNTRY_MAP.items():
    new_raw = get_fx_raw(code, data)
    old_raw = get_fx_raw(code, old_data) if old_data else None
    fx_block[country] = {
        'value':     format_fx(new_raw, FX_DECIMALS[code]),
        'direction': get_fx_direction(new_raw, old_raw),
    }
edu['exchange-rates'] = fx_block

# ── Charts ────────────────────────────────────────────────────────────────────

print('\nBuilding charts...')
charts = {}
W_MON = 120   # 10 years monthly
W_ANN = 10    # 10 years annual
W_FX  = 120  # 10 years monthly

def build_monthly_chart(hist_key, window):
    series = {}
    dates  = None
    for code, country in COUNTRY_MAP.items():
        v = get_frozen(code, hist_key, data)
        if not v:
            series[country] = []
            continue
        series[country] = round_series(tail(v, window))
        if dates is None:
            dates = tail_dates(ALL_MONTHLY, v, window)
    return {'dates': dates or [], 'series': series}

def build_annual_chart(hist_key, window):
    series = {}
    dates  = None
    for code, country in COUNTRY_MAP.items():
        v = get_frozen(code, hist_key, data)
        if not v:
            series[country] = []
            continue
        series[country] = round_series(tail(v, window))
        if dates is None:
            dates = tail_dates(ALL_ANNUAL, v, window)
    return {'dates': dates or [], 'series': series}

charts['inflation']     = build_monthly_chart('Inflation (CPI)', W_MON)
charts['unemployment']  = build_monthly_chart('Unemployment', W_MON)
charts['interest-rates']= build_monthly_chart('Policy Rate', W_MON)
charts['gdp']           = build_annual_chart('GDP Growth', W_ANN)
charts['trade']         = build_annual_chart('Current Account', W_ANN)

# Exchange rates: per-country key
fx_series = {}
fx_dates  = None
for code, country in COUNTRY_MAP.items():
    hist_key = FX_HIST_KEYS[code]
    v = get_frozen(code, hist_key, data) or get_frozen(code, 'FX Rate', data)
    if not v:
        fx_series[country] = []
        continue
    fx_series[country] = round_series(tail(v, W_FX))
    if fx_dates is None:
        fx_dates = tail_dates(ALL_MONTHLY, v, W_FX)
charts['exchange-rates'] = {'dates': fx_dates or [], 'series': fx_series}

for name, c in charts.items():
    n_countries = sum(1 for v in c['series'].values() if v)
    print(f'  {name:<18} {len(c["dates"])} dates, {n_countries}/6 countries')

edu['charts'] = charts

# ── Write ─────────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(MACEDU_DATA), exist_ok=True)
with open(MACEDU_DATA, 'w', encoding='utf-8') as f:
    json.dump(edu, f, indent=2, ensure_ascii=False)

size_kb = os.path.getsize(MACEDU_DATA) // 1024
print(f'\nWritten: {MACEDU_DATA} ({size_kb} KB)')

print('\nSnapshot:')
for concept in ['inflation','unemployment','gdp','interest-rates','trade','exchange-rates']:
    block = edu.get(concept, {})
    print(f'  {concept}:')
    for country, vals in block.items():
        print(f'    {country}: {vals["value"]}  {vals["direction"]}')

print('\n  sync_edu complete.\n')
