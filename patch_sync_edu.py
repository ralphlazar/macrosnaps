#!/usr/bin/env python3
"""
Patches sync_edu.py to fix chart date alignment.

The bug: build_monthly_chart assumed all series start Jan 2000, aligning
dates by array length. If a series starts later (e.g. GBR CPI = Jan 2001),
dates are shifted one year too early.

The fix: read startDate from _frozen_historical and generate dates from
the correct origin for each series.

Usage:
    python3 patch_sync_edu.py
"""

import re
import shutil
from pathlib import Path

TARGET = Path('/Users/lisaswerling/RALPH/AI/macrosnaps/sync_edu.py')

if not TARGET.exists():
    raise FileNotFoundError(f'Not found: {TARGET}')

# Backup
backup = TARGET.with_suffix('.py.bak')
shutil.copy2(TARGET, backup)
print(f'Backup: {backup}')

text = TARGET.read_text(encoding='utf-8')

# ── Patch 1: get_frozen — return (v, startDate) tuple ────────────────────────

OLD_GET_FROZEN = """def get_frozen(code, key, src):
    try:
        return src['countries'][code]['_frozen_historical'][key]['v']
    except (KeyError, TypeError):
        return []"""

NEW_GET_FROZEN = """def get_frozen(code, key, src):
    try:
        entry = src['countries'][code]['_frozen_historical'][key]
        return entry['v'], entry.get('startDate')
    except (KeyError, TypeError):
        return [], None"""

if OLD_GET_FROZEN not in text:
    raise ValueError('Could not find get_frozen — check sync_edu.py has not changed')
text = text.replace(OLD_GET_FROZEN, NEW_GET_FROZEN)
print('Patched: get_frozen')

# ── Patch 2: add make_dates_from_start after make_annual_dates ───────────────

OLD_TAIL = """def tail(values, n):
    return values[-n:] if len(values) >= n else values"""

NEW_TAIL = """def make_dates_from_start(start_str, n_values, fmt='%b %Y'):
    \"\"\"Generate n_values monthly date labels starting from start_str ('YYYY-MM').
    Falls back to SERIES_START if start_str is missing or unparseable.\"\"\"
    try:
        start = datetime.strptime(start_str, '%Y-%m')
    except (ValueError, TypeError):
        start = SERIES_START
    today = datetime.today()
    dates = []
    for i in range(n_values):
        d = start + relativedelta(months=i)
        if d > today:
            break
        dates.append(d.strftime(fmt))
    return dates

def tail(values, n):
    return values[-n:] if len(values) >= n else values"""

if OLD_TAIL not in text:
    raise ValueError('Could not find tail — check sync_edu.py has not changed')
text = text.replace(OLD_TAIL, NEW_TAIL)
print('Patched: added make_dates_from_start')

# ── Patch 3: build_monthly_chart — use startDate ──────────────────────────────

OLD_MONTHLY = """def build_monthly_chart(data, hist_key, country_slug):
    code   = SLUG_TO_CODE[country_slug]
    v      = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    series = round_series(tail(v, W_MON))
    dates  = tail_dates(ALL_MONTHLY, v, W_MON)
    return list(dates), series"""

NEW_MONTHLY = """def build_monthly_chart(data, hist_key, country_slug):
    code            = SLUG_TO_CODE[country_slug]
    v, start_date   = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    all_dates = make_dates_from_start(start_date, len(v))
    series    = round_series(tail(v, W_MON))
    dates     = all_dates[-W_MON:] if len(all_dates) >= W_MON else all_dates
    return list(dates), series"""

if OLD_MONTHLY not in text:
    raise ValueError('Could not find build_monthly_chart — check sync_edu.py has not changed')
text = text.replace(OLD_MONTHLY, NEW_MONTHLY)
print('Patched: build_monthly_chart')

# ── Patch 4: build_annual_chart — unpack tuple from get_frozen ───────────────

OLD_ANNUAL = """def build_annual_chart(data, hist_key, country_slug):
    code   = SLUG_TO_CODE[country_slug]
    v      = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    series = round_series(tail(v, W_ANN))
    dates  = tail_dates(ALL_ANNUAL, v, W_ANN)
    return list(dates), series"""

NEW_ANNUAL = """def build_annual_chart(data, hist_key, country_slug):
    code   = SLUG_TO_CODE[country_slug]
    v, _   = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    series = round_series(tail(v, W_ANN))
    dates  = tail_dates(ALL_ANNUAL, v, W_ANN)
    return list(dates), series"""

if OLD_ANNUAL not in text:
    raise ValueError('Could not find build_annual_chart — check sync_edu.py has not changed')
text = text.replace(OLD_ANNUAL, NEW_ANNUAL)
print('Patched: build_annual_chart')

# ── Patch 5: build_fx_chart — unpack tuple from get_frozen ───────────────────

OLD_FX = """def build_fx_chart(data, country_slug):
    code     = SLUG_TO_CODE[country_slug]
    hist_key = FX_HIST_KEYS[code]
    v        = get_frozen(code, hist_key, data) or get_frozen(code, 'FX Rate', data)
    if not v:
        return [], []
    series = round_series(tail(v, W_MON))
    dates  = tail_dates(ALL_MONTHLY, v, W_MON)
    return list(dates), series"""

NEW_FX = """def build_fx_chart(data, country_slug):
    code     = SLUG_TO_CODE[country_slug]
    hist_key = FX_HIST_KEYS[code]
    v, start_date = get_frozen(code, hist_key, data)
    if not v:
        v, start_date = get_frozen(code, 'FX Rate', data)
    if not v:
        return [], []
    all_dates = make_dates_from_start(start_date, len(v))
    series    = round_series(tail(v, W_MON))
    dates     = all_dates[-W_MON:] if len(all_dates) >= W_MON else all_dates
    return list(dates), series"""

if OLD_FX not in text:
    raise ValueError('Could not find build_fx_chart — check sync_edu.py has not changed')
text = text.replace(OLD_FX, NEW_FX)
print('Patched: build_fx_chart')

# ── Write ─────────────────────────────────────────────────────────────────────

TARGET.write_text(text, encoding='utf-8')
print(f'\nDone. Written: {TARGET}')
print('Run: python3 sync_edu.py to regenerate metrics.js')
