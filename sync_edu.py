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

# ── Constants ─────────────────────────────────────────────────────────────────

COUNTRY_NAMES = {'uk': 'UK', 'us': 'US', 'eurozone': 'Eurozone',
                 'china': 'China', 'japan': 'Japan', 'brazil': 'Brazil'}

FLAG_MAP = {'uk': '🇬🇧', 'us': '🇺🇸', 'eurozone': '🇪🇺',
            'china': '🇨🇳', 'japan': '🇯🇵', 'brazil': '🇧🇷'}

# Unit appended after the value on the homepage feed
UNIT_MAP = {
    'inflation':      '%',
    'unemployment':   '%',
    'gdp':            '%',
    'interest-rates': '%',
    'exchange-rates': '',   # value already includes pair context
    'trade':          '% GDP',
}

# ── Release date calendar ──────────────────────────────────────────────────────
# Update monthly. Use the official announced release date for each series.
# Exchange rates are always 0 (pulled daily).
# Sources:
#   UK:       https://www.ons.gov.uk/releases
#   US:       https://www.bls.gov/schedule/ and https://www.bea.gov/news/schedule
#   Eurozone: https://ec.europa.eu/eurostat/news/release-calendar
#   ECB/BoE:  central bank meeting calendars
#   Japan:    https://www.stat.go.jp/english/info/news/index.html
#   Brazil:   https://www.ibge.gov.br/en/news-agency/release-schedule.html

RELEASE_DATES = {
    'inflation': {
        'uk':       date(2026, 3, 19),
        'us':       date(2026, 3, 12),
        'eurozone': date(2026, 3, 19),
        'china':    date(2026, 3, 11),
        'japan':    date(2026, 3, 21),
        'brazil':   date(2026, 3, 14),
    },
    'unemployment': {
        'uk':       date(2026, 3, 18),
        'us':       date(2026, 3,  7),
        'eurozone': date(2026, 3,  3),
        'china':    date(2026, 3, 17),
        'japan':    date(2026, 2, 28),
        'brazil':   date(2026, 3, 27),
    },
    'gdp': {
        'uk':       date(2026, 2, 13),
        'us':       date(2026, 2, 27),
        'eurozone': date(2026, 1, 30),
        'china':    date(2026, 1, 17),
        'japan':    date(2026, 2, 17),
        'brazil':   date(2026, 2, 27),
    },
    'interest-rates': {
        'uk':       date(2026, 2,  6),
        'us':       date(2026, 3, 19),
        'eurozone': date(2026, 3,  6),
        'china':    date(2026, 3, 20),
        'japan':    date(2026, 3, 19),
        'brazil':   date(2026, 3, 19),
    },
    'trade': {
        'uk':       date(2026, 2, 13),
        'us':       date(2026, 3,  6),
        'eurozone': date(2026, 1, 21),
        'china':    date(2026, 3,  7),
        'japan':    date(2026, 3,  5),
        'brazil':   date(2026, 2, 25),
    },
    # exchange-rates handled separately — always 0
}

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

today_date = date.today()

for slug, macro_key in SNAPSHOT_MAP.items():
    block = {}
    release_dates_for_concept = RELEASE_DATES.get(slug, {})
    for code, country in COUNTRY_MAP.items():
        new_str = get_macro_value(code, macro_key, data)
        old_str = get_macro_value(code, macro_key, old_data) if old_data else None
        display  = new_str.replace(' GDP', '').strip() if new_str else new_str
        release_date = release_dates_for_concept.get(country)
        days_ago = (today_date - release_date).days if release_date else 0
        block[country] = {
            'value':           display,
            'direction':       get_direction(parse_num(new_str), parse_num(old_str)),
            'flag':            FLAG_MAP.get(country, ''),
            'country':         COUNTRY_NAMES.get(country, country),
            'unit':            UNIT_MAP.get(slug, ''),
            'releasedDaysAgo': max(0, days_ago),
        }
    edu[slug] = block

fx_block = {}
for code, country in COUNTRY_MAP.items():
    new_raw = get_fx_raw(code, data)
    old_raw = get_fx_raw(code, old_data) if old_data else None

    # movePercent: compare today vs 7 days ago via frozen historical
    move_pct = None
    hist_key = FX_HIST_KEYS[code]
    fx_hist = get_frozen(code, hist_key, data) or get_frozen(code, 'FX Rate', data)
    if fx_hist and len(fx_hist) >= 8 and new_raw:
        prev_7d = fx_hist[-8]   # approx 7 trading days ago
        if prev_7d and prev_7d != 0:
            move_pct = round(((new_raw - prev_7d) / prev_7d) * 100, 1)

    fx_block[country] = {
        'value':           format_fx(new_raw, FX_DECIMALS[code]),
        'direction':       get_fx_direction(new_raw, old_raw),
        'flag':            FLAG_MAP.get(country, ''),
        'country':         COUNTRY_NAMES.get(country, country),
        'unit':            '',
        'releasedDaysAgo': 0,   # FX is always today
        'movePercent':     move_pct,
    }
edu['exchange-rates'] = fx_block


# ── Icon + label derivation ───────────────────────────────────────────────────
#
# Adds 'icon' (sunny / cloudy / stormy) and 'label' (one editorial sentence)
# to every snapshot entry. Rules are per-concept; all thresholds are
# intentionally conservative. the aim is to surface genuinely notable
# situations, not to cry wolf on normal variation.

INFLATION_TARGET = 2.0
INFLATION_TARGETS = {'uk': 2.0, 'us': 2.0, 'eurozone': 2.0,
                     'china': 3.0, 'japan': 2.0, 'brazil': 3.0}

STRUCTURAL_U = {'uk': 4.0, 'us': 4.0, 'eurozone': 6.5,
                'china': 5.0, 'japan': 2.5, 'brazil': 8.0}

GDP_TREND = {'uk': 2.0, 'us': 2.5, 'eurozone': 1.5,
             'china': 5.0, 'japan': 1.0, 'brazil': 2.0}

def inflation_icon_label(country, val, direction):
    target = INFLATION_TARGETS.get(country, 2.0)
    name   = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing inflation data. worth discussing why data gaps occur.'
    diff = val - target
    if abs(diff) <= 0.3:
        return 'sunny', f'Good example of inflation on target. {name} CPI is sitting right where the central bank wants it.'
    elif diff > 0:
        if direction == 'up':
            return 'stormy', f'Good example of a central bank under pressure. {name} inflation is above target and still rising.'
        else:
            return 'cloudy', f'Good example of inflation coming under control. {name} CPI is above target but heading in the right direction.'
    else:
        if direction == 'down':
            return 'cloudy', f'Good example of below-target inflation. {name} CPI is low and falling, raising questions about deflation risk.'
        else:
            return 'sunny', f'Good example of inflation running slightly cool. {name} CPI is just below target.'

def unemployment_icon_label(country, val, direction):
    structural = STRUCTURAL_U.get(country, 5.0)
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing labour market data. worth discussing measurement challenges.'
    diff = val - structural
    if diff <= 0.3:
        return 'sunny', f'Good example of a tight labour market. {name} unemployment is at or below its normal level.'
    elif diff <= 2.0:
        if direction == 'up':
            return 'stormy', f'Good example of a weakening labour market. {name} unemployment is rising above its structural rate.'
        else:
            return 'cloudy', f'Good example of elevated unemployment. {name} is above its structural rate but improving.'
    else:
        return 'stormy', f'Good example of a labour market under serious strain. {name} unemployment is well above its normal level.'

def gdp_icon_label(country, val, direction):
    trend = GDP_TREND.get(country, 2.0)
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing growth data. worth discussing GDP measurement.'
    if val < 0:
        return 'stormy', f'Good example of a contracting economy. {name} is in negative growth territory right now.'
    elif val >= trend * 0.75:
        return 'sunny', f'Good example of healthy growth. {name} is expanding at or above its trend rate.'
    else:
        return 'cloudy', f'Good example of sluggish growth. {name} is growing but well below its historical trend.'

def interest_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing monetary policy data.'
    if val <= 1.0:
        return 'sunny', f'Good example of loose monetary policy. {name} rates are very low, designed to stimulate the economy.'
    elif val <= 4.0:
        if direction == 'down':
            return 'sunny', f'Good example of a central bank easing. {name} is cutting rates as inflation comes under control.'
        elif direction == 'up':
            return 'cloudy', f'Good example of a central bank tightening. {name} is raising rates to bear down on inflation.'
        else:
            return 'cloudy', f'Good example of a central bank on hold. {name} is watching the data before moving rates.'
    else:
        return 'stormy', f'Good example of restrictive monetary policy. {name} rates are high and squeezing the economy.'

def fx_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing exchange rate data.'
    if direction == 'up':
        return 'cloudy', f'Good example of currency appreciation. the {name} currency is strengthening, which helps importers but hurts exporters.'
    elif direction == 'down':
        return 'cloudy', f'Good example of currency depreciation. the {name} currency is weakening, which helps exporters but raises import costs.'
    else:
        return 'sunny', f'Good example of a stable exchange rate. the {name} currency is holding steady against the dollar.'

def trade_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', 'Good example of missing current account data.'
    if abs(val) <= 1.0:
        return 'sunny', f'Good example of a broadly balanced current account. {name} is neither heavily importing nor exporting on net.'
    elif val > 0:
        if abs(val) > 4.0:
            return 'sunny', f'Good example of a large current account surplus. {name} is selling significantly more to the world than it is buying.'
        return 'sunny', f'Good example of a current account surplus. {name} is selling more to the world than it is buying.'
    elif abs(val) <= 4.0:
        return 'cloudy', f'Good example of a current account deficit. {name} is buying more from the world than it is selling.'
    else:
        return 'stormy', f'Good example of a large current account deficit. {name} is running a significant external imbalance.'

ICON_FNS = {
    'inflation':      inflation_icon_label,
    'unemployment':   unemployment_icon_label,
    'gdp':            gdp_icon_label,
    'interest-rates': interest_icon_label,
    'exchange-rates': fx_icon_label,
    'trade':          trade_icon_label,
}

for slug, fn in ICON_FNS.items():
    block = edu.get(slug, {})
    for country, entry in block.items():
        raw_val = parse_num(entry.get('value'))
        direction = entry.get('direction', 'flat')
        icon, label = fn(country, raw_val, direction)
        entry['icon']  = icon
        entry['label'] = label

print('Icons + labels derived.')

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

# ── Wrap snapshots ────────────────────────────────────────────────────────────
# TeacherHomePage.js reads from edu-data.snapshots (not top-level concept keys).
# Move all concept blocks into a nested 'snapshots' object for clarity.

CONCEPT_SLUGS = ['inflation', 'unemployment', 'gdp', 'interest-rates', 'exchange-rates', 'trade']
edu['snapshots'] = {slug: edu.pop(slug) for slug in CONCEPT_SLUGS if slug in edu}

# ── Write ─────────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(MACEDU_DATA), exist_ok=True)
with open(MACEDU_DATA, 'w', encoding='utf-8') as f:
    json.dump(edu, f, indent=2, ensure_ascii=False)

size_kb = os.path.getsize(MACEDU_DATA) // 1024
print(f'\nWritten: {MACEDU_DATA} ({size_kb} KB)')

print('\nSnapshot:')
for concept in ['inflation','unemployment','gdp','interest-rates','trade','exchange-rates']:
    block = edu.get('snapshots', {}).get(concept, {})
    print(f'  {concept}:')
    for country, vals in block.items():
        move = f"  move={vals['movePercent']}%" if vals.get('movePercent') is not None else ''
        print(f'    {vals["flag"]} {country}: {vals["value"]}  {vals["direction"]}  ({vals["releasedDaysAgo"]}d ago){move}')

print('\n  sync_edu complete.\n')
