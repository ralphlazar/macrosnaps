#!/usr/bin/env python3
"""
sync_edu.py  (rewritten Session 22)
=====================================
Reads MacroSnaps data.json.
Writes metrics.js to macedu/app/data/ with:
  - Snapshot: value, direction, releasedDaysAgo, icon, correctIcon, weatherReason per country
  - Charts: chartDates, chartSeries (last point forced to match value)
  - Blurbs: generated via Claude API (Haiku)
      All metrics:       only on new release (releasedDaysAgo == 0)
      Exchange rates:    regenerated daily
      No cached blurb:   generated immediately (bootstrap on first run)

Run after build.py in the Daily Bash Ritual:
    python3 sync_edu.py

Historical series source: _frozen_historical in data.json.
Chart windows:
  Inflation, unemployment, interest-rates: last 120 months (10 years)
  GDP, trade:                              last 10 annual values
  Exchange rates:                          last 120 months (10 years)
"""

import json
import os
import sys
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

try:
    from dotenv import load_dotenv
    load_dotenv('/Users/lisaswerling/RALPH/AI/macrosnaps/.env')
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print('WARNING: anthropic not installed. Blurb generation disabled.')

# ── Paths ─────────────────────────────────────────────────────────────────────

MACROSNAPS_DIR = '/Users/lisaswerling/RALPH/AI/macrosnaps'
MACEDU_DIR     = '/Users/lisaswerling/RALPH/AI/macedu'
METRICS_JS     = os.path.join(MACEDU_DIR, 'app/data/metrics.js')
BLURB_CACHE    = os.path.join(MACEDU_DIR, 'app/data/blurb-cache.json')
DATA_FILE      = os.path.join(MACROSNAPS_DIR, 'data.json')
BACKUP_DIR     = os.path.join(MACROSNAPS_DIR, 'backups')
TODAY          = date.today()
SERIES_START   = datetime(2000, 1, 1)
ANNUAL_START   = 2000

# ── Metric metadata ───────────────────────────────────────────────────────────

METRIC_META = {
    'inflation':      {'title': 'Inflation',      'aqaRef': '3.2.1', 'unit': '%',     'decimals': 1},
    'unemployment':   {'title': 'Unemployment',   'aqaRef': '3.2.2', 'unit': '%',     'decimals': 1},
    'gdp':            {'title': 'GDP',             'aqaRef': '3.1.1', 'unit': '%',     'decimals': 1},
    'interest-rates': {'title': 'Interest rates', 'aqaRef': '3.2.4', 'unit': '%',     'decimals': 2},
    'exchange-rates': {'title': 'Exchange rates', 'aqaRef': '3.3.2', 'unit': '',      'decimals': 0},
    'trade':          {'title': 'Trade',           'aqaRef': '3.3.3', 'unit': '% GDP', 'decimals': 1},
}

METRIC_SLUGS  = ['inflation', 'unemployment', 'gdp', 'interest-rates', 'exchange-rates', 'trade']
COUNTRY_SLUGS = ['uk', 'us', 'eurozone', 'china', 'japan', 'brazil']

COUNTRY_MAP = {
    'GBR': 'uk', 'USA': 'us', 'DEU': 'eurozone',
    'CHN': 'china', 'JPN': 'japan', 'BRA': 'brazil',
}
SLUG_TO_CODE = {v: k for k, v in COUNTRY_MAP.items()}

COUNTRY_NAMES = {
    'uk': 'UK', 'us': 'US', 'eurozone': 'Eurozone',
    'china': 'China', 'japan': 'Japan', 'brazil': 'Brazil',
}
FLAG_MAP = {
    'uk': '🇬🇧', 'us': '🇺🇸', 'eurozone': '🇪🇺',
    'china': '🇨🇳', 'japan': '🇯🇵', 'brazil': '🇧🇷',
}

MACRO_KEYS = {
    'inflation':      'Inflation (CPI)',
    'unemployment':   'Unemployment',
    'gdp':            'GDP Growth',
    'interest-rates': 'Policy Rate',
    'trade':          'Current Account',
}

FX_HIST_KEYS = {
    'GBR': 'GBP/USD', 'USA': 'USD/DXY', 'DEU': 'EUR/USD',
    'CHN': 'USD/CNY', 'JPN': 'USD/JPY', 'BRA': 'USD/BRL',
}
FX_DECIMALS = {
    'GBR': 2, 'USA': 1, 'DEU': 2, 'CHN': 2, 'JPN': 0, 'BRA': 2,
}
ICON_MAP = {'sunny': '☀️', 'cloudy': '☁️', 'stormy': '⛈️'}

# ── Release calendar ──────────────────────────────────────────────────────────
# Update monthly with official announced release dates.
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
    # exchange-rates: always 0 — handled separately
}

# ── Helpers ───────────────────────────────────────────────────────────────────

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

def format_pct(val, decimals=1, sign=False):
    if val is None:
        return None
    formatted = f'{val:.{decimals}f}%'
    if sign and val > 0:
        return f'+{formatted}'
    return formatted

def parse_value_float(value_str):
    """Parse a formatted value string back to float for chartSeries alignment."""
    if value_str is None:
        return None
    s = str(value_str).strip().replace('%', '').replace('GDP', '').replace('+', '').strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return None

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

def make_monthly_dates(n, fmt='%b %Y'):
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

ALL_MONTHLY = make_monthly_dates(400)
ALL_ANNUAL  = make_annual_dates(50)

# ── Icon / reveal logic ───────────────────────────────────────────────────────

INFLATION_TARGETS = {'uk': 2.0, 'us': 2.0, 'eurozone': 2.0, 'china': 3.0, 'japan': 2.0, 'brazil': 3.0}
STRUCTURAL_U      = {'uk': 4.0, 'us': 4.0, 'eurozone': 6.5, 'china': 5.0, 'japan': 2.5, 'brazil': 8.0}
GDP_TREND         = {'uk': 2.0, 'us': 2.5, 'eurozone': 1.5, 'china': 5.0, 'japan': 1.0, 'brazil': 2.0}

def inflation_icon_label(country, val, direction):
    target = INFLATION_TARGETS.get(country, 2.0)
    name   = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No inflation data available for {name} right now.'
    diff = val - target
    if abs(diff) <= 0.3:
        return 'sunny',  f'Inflation is right on the {name} central bank target -- that is a sunny read.'
    elif diff > 0:
        if direction == 'up':
            return 'stormy', f'Inflation in {name} is above target and still rising -- stormy.'
        else:
            return 'cloudy', f'Inflation in {name} is above target but falling -- cloudy, heading in the right direction.'
    else:
        if direction == 'down':
            return 'cloudy', f'Inflation in {name} is below target and still dropping -- deflation risk makes this cloudy.'
        else:
            return 'sunny',  f'Inflation in {name} is just below target and stable -- close enough to call it sunny.'

def unemployment_icon_label(country, val, direction):
    structural = STRUCTURAL_U.get(country, 5.0)
    name       = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No unemployment data available for {name} right now.'
    diff = val - structural
    if diff <= 0.3:
        return 'sunny',  f'Unemployment in {name} is at or below its normal level -- a sunny labour market.'
    elif diff <= 2.0:
        if direction == 'up':
            return 'stormy', f'Unemployment in {name} is above its normal level and rising -- that is a stormy read.'
        else:
            return 'cloudy', f'Unemployment in {name} is above its normal level but improving -- cloudy for now.'
    else:
        return 'stormy', f'Unemployment in {name} is well above its normal level -- stormy.'

def gdp_icon_label(country, val, direction):
    trend = GDP_TREND.get(country, 2.0)
    name  = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No GDP data available for {name} right now.'
    if val < 0:
        return 'stormy', f'The {name} economy is shrinking -- negative growth is a stormy read.'
    elif val >= trend * 0.75:
        return 'sunny',  f'{name} is growing at or near its normal rate -- that is a sunny read.'
    else:
        return 'cloudy', f'{name} is growing, but well below its usual pace -- cloudy.'

def interest_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No interest rate data available for {name} right now.'
    if val <= 1.0:
        return 'sunny',  f'{name} rates are very low -- cheap borrowing is designed to boost the economy, a sunny signal.'
    elif val <= 4.0:
        if direction == 'down':
            return 'sunny',  f'{name} is cutting rates -- the central bank thinks inflation is under control, a sunny read.'
        elif direction == 'up':
            return 'cloudy', f'{name} is raising rates to fight inflation -- tightening makes this cloudy.'
        else:
            return 'cloudy', f'{name} rates are on hold -- the central bank is waiting for more data, cloudy.'
    else:
        return 'stormy', f'{name} rates are high and squeezing borrowing -- that is a stormy read.'

def fx_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No exchange rate data available for {name} right now.'
    if direction == 'up':
        return 'cloudy', f'The {name} currency is strengthening -- good for importers, bad for exporters, so cloudy overall.'
    elif direction == 'down':
        return 'cloudy', f'The {name} currency is weakening -- helps exporters but pushes up import costs, cloudy.'
    else:
        return 'sunny',  f'The {name} exchange rate is holding steady -- stability is a sunny signal.'

def trade_icon_label(country, val, direction):
    name = COUNTRY_NAMES[country]
    if val is None:
        return 'cloudy', f'No current account data available for {name} right now.'
    if abs(val) <= 1.0:
        return 'sunny',  f'{name} imports and exports are broadly balanced -- a sunny read.'
    elif val > 0:
        if abs(val) > 4.0:
            return 'sunny', f'{name} is selling far more to the world than it buys -- a large surplus, sunny.'
        return 'sunny',     f'{name} is selling more to the world than it buys -- a surplus is a sunny read.'
    elif abs(val) <= 4.0:
        return 'cloudy', f'{name} is buying more from the world than it sells -- a deficit makes this cloudy.'
    else:
        return 'stormy', f'{name} has a large current account deficit -- a significant imbalance, stormy.'

ICON_FNS = {
    'inflation':      inflation_icon_label,
    'unemployment':   unemployment_icon_label,
    'gdp':            gdp_icon_label,
    'interest-rates': interest_icon_label,
    'exchange-rates': fx_icon_label,
    'trade':          trade_icon_label,
}

# ── Chart builders ────────────────────────────────────────────────────────────

W_MON = 120
W_ANN = 10

def build_monthly_chart(data, hist_key, country_slug):
    code   = SLUG_TO_CODE[country_slug]
    v      = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    series = round_series(tail(v, W_MON))
    dates  = tail_dates(ALL_MONTHLY, v, W_MON)
    return list(dates), series

def build_annual_chart(data, hist_key, country_slug):
    code   = SLUG_TO_CODE[country_slug]
    v      = get_frozen(code, hist_key, data)
    if not v:
        return [], []
    series = round_series(tail(v, W_ANN))
    dates  = tail_dates(ALL_ANNUAL, v, W_ANN)
    return list(dates), series

def build_fx_chart(data, country_slug):
    code     = SLUG_TO_CODE[country_slug]
    hist_key = FX_HIST_KEYS[code]
    v        = get_frozen(code, hist_key, data) or get_frozen(code, 'FX Rate', data)
    if not v:
        return [], []
    series = round_series(tail(v, W_MON))
    dates  = tail_dates(ALL_MONTHLY, v, W_MON)
    return list(dates), series

# ── Blurb generation ──────────────────────────────────────────────────────────

BLURB_SYSTEM = """You write 3-bullet analysis copy for a Bloomberg-style A-level economics teaching platform.

Rules:
- UK English throughout
- 3 bullets, each 1-2 punchy sentences
- Direction and context only — never cite specific numbers, percentages, or data values
- No hedging ("generally", "it is worth noting", "broadly speaking")
- No wasted openers ("This shows that...", "The data suggests...")
- No double hyphens — use "to" for ranges or rewrite
- No em dashes
- Confident, wry, authoritative teacher voice — not dry, not municipal
- Return JSON only: {"blurb": ["bullet 1", "bullet 2", "bullet 3"]}
- No markdown, no preamble, no explanation outside the JSON"""

BLURB_SYSTEM_AP = """You write 3-bullet analysis copy for a Bloomberg-style AP Macroeconomics teaching platform.

Rules:
- US English throughout (labor not labour, behavior not behaviour, recognize not recognise)
- 3 bullets, each 1-2 punchy sentences
- Direction and context only — never cite specific numbers, percentages, or data values
- No hedging ("generally", "it is worth noting", "broadly speaking")
- No wasted openers ("This shows that...", "The data suggests...")
- No double hyphens — use "to" for ranges or rewrite
- No em dashes
- Confident, wry, authoritative teacher voice — not dry, not municipal
- Frame analysis in AP Macroeconomics terms where natural (aggregate demand, FOMC, natural rate, etc.)
- Return JSON only: {"blurb": ["bullet 1", "bullet 2", "bullet 3"]}
- No markdown, no preamble, no explanation outside the JSON"""

BLURB_SYSTEM_AP = """You write 3-bullet analysis copy for a Bloomberg-style AP Macroeconomics teaching platform.

Rules:
- US English throughout (labor not labour, behavior not behaviour, recognize not recognise)
- 3 bullets, each 1-2 punchy sentences
- Direction and context only — never cite specific numbers, percentages, or data values
- No hedging ("generally", "it is worth noting", "broadly speaking")
- No wasted openers ("This shows that...", "The data suggests...")
- No double hyphens — use "to" for ranges or rewrite
- No em dashes
- Confident, wry, authoritative teacher voice — not dry, not municipal
- Frame analysis in AP Macroeconomics terms where natural (aggregate demand, FOMC, natural rate, etc.)
- Return JSON only: {"blurb": ["bullet 1", "bullet 2", "bullet 3"]}
- No markdown, no preamble, no explanation outside the JSON"""

def should_generate_blurb(metric_slug, released_days_ago, has_cached):
    """Return True if blurb should be regenerated this run."""
    if not has_cached:
        return True                    # bootstrap: always generate if no cache
    if metric_slug == 'exchange-rates':
        return True                    # FX: regenerate daily
    return released_days_ago == 0     # others: only on new release

def generate_blurb(client, system, metric_slug, country_slug, direction, icon_slug, reveal):
    """Call Claude Haiku for a 3-bullet blurb. Returns list[str] or []."""
    user_prompt = (
        f"Country: {COUNTRY_NAMES[country_slug]}\n"
        f"Metric: {METRIC_META[metric_slug]['title']}\n"
        f"Direction: {direction}\n"
        f"Weather icon: {icon_slug}\n"
        f"Context: {reveal}\n\n"
        f"Write 3 bullets for the snapshot card."
    )
    try:
        resp  = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            system=system,
            messages=[{'role': 'user', 'content': user_prompt}],
        )
        raw   = resp.content[0].text.strip()
        raw   = raw.strip('`').lstrip('json').strip()
        data  = json.loads(raw)
        blurb = data.get('blurb', [])
        if isinstance(blurb, list) and len(blurb) == 3:
            return blurb
        print(f'    WARNING: unexpected blurb shape for {metric_slug}/{country_slug}')
        return []
    except Exception as e:
        print(f'    ERROR generating blurb for {metric_slug}/{country_slug}: {e}')
        return []

# ── Load data ─────────────────────────────────────────────────────────────────

print(f'\nsync_edu.py — {TODAY.isoformat()}')

if not os.path.exists(DATA_FILE):
    sys.exit(f'ERROR: data.json not found at {DATA_FILE}')

with open(DATA_FILE, encoding='utf-8') as f:
    data = json.load(f)
print('data.json loaded.')

# Most recent backup for direction comparison
backup_data = None
if os.path.isdir(BACKUP_DIR):
    backups = sorted([
        os.path.join(BACKUP_DIR, fn)
        for fn in os.listdir(BACKUP_DIR)
        if fn.endswith('.json')
    ])
    if backups:
        with open(backups[-1], encoding='utf-8') as f:
            backup_data = json.load(f)
        print(f'Backup loaded: {os.path.basename(backups[-1])}')

# Blurb cache
blurb_cache = {}
if os.path.exists(BLURB_CACHE):
    with open(BLURB_CACHE, encoding='utf-8') as f:
        blurb_cache = json.load(f)
print(f'Blurb cache: {len(blurb_cache)} entries')

# Claude client
claude = None
if HAS_ANTHROPIC:
    try:
        claude = anthropic.Anthropic()
        print('Claude API: ready')
    except Exception as e:
        print(f'Claude API: unavailable ({e}). Blurb generation disabled.')

# ── Build metrics ─────────────────────────────────────────────────────────────

print('\nBuilding metrics...')
metrics = {}
blurbs_generated = 0

for metric_slug in METRIC_SLUGS:
    meta         = METRIC_META[metric_slug]
    countries_out = {}

    for country_slug in COUNTRY_SLUGS:
        code = SLUG_TO_CODE[country_slug]
        flag = FLAG_MAP[country_slug]
        name = COUNTRY_NAMES[country_slug]

        # ── Value & direction ─────────────────────────────────────────────────
        if metric_slug == 'exchange-rates':
            raw_val   = get_fx_raw(code, data)
            prev_val  = get_fx_raw(code, backup_data) if backup_data else None
            raw_num   = parse_num(raw_val)
            prev_num  = parse_num(prev_val)
            decimals  = FX_DECIMALS[code]
            direction = get_fx_direction(raw_num, prev_num)
            value_str = format_fx(raw_num, decimals)
        else:
            macro_key = MACRO_KEYS[metric_slug]
            raw_val   = get_macro_value(code, macro_key, data)
            prev_val  = get_macro_value(code, macro_key, backup_data) if backup_data else None
            raw_num   = parse_num(raw_val)
            prev_num  = parse_num(prev_val)
            direction = get_direction(raw_num, prev_num)
            sign      = (metric_slug == 'trade')
            value_str = format_pct(raw_num, decimals=meta['decimals'], sign=sign)

        # ── Released days ago ────────────────────────────────────────────────
        if metric_slug == 'exchange-rates':
            released_days_ago = 0   # overridden below after chart is built
        else:
            release_date      = RELEASE_DATES.get(metric_slug, {}).get(country_slug)
            released_days_ago = max(0, (TODAY - release_date).days) if release_date else None

        # ── Icon & reveal ────────────────────────────────────────────────────
        icon_slug_val, reveal = ICON_FNS[metric_slug](country_slug, raw_num, direction)
        icon = ICON_MAP[icon_slug_val]

        # ── Chart data ───────────────────────────────────────────────────────
        if metric_slug == 'exchange-rates':
            chart_dates, chart_series = build_fx_chart(data, country_slug)
        elif metric_slug in ('gdp', 'trade'):
            chart_dates, chart_series = build_annual_chart(data, MACRO_KEYS[metric_slug], country_slug)
        else:
            chart_dates, chart_series = build_monthly_chart(data, MACRO_KEYS[metric_slug], country_slug)

        # ── Force last chartSeries point to match value ──────────────────────
        val_float = parse_value_float(value_str)
        if chart_series and val_float is not None:
            chart_series[-1] = val_float

        # ── Exchange rate move filter ────────────────────────────────────────
        # Only count FX as live/updated if rate moved >5% year-on-year.
        move_percent = None
        if metric_slug == 'exchange-rates':
            if len(chart_series) >= 13:
                prev_year = chart_series[-13]
                curr      = chart_series[-1]
                if prev_year and prev_year != 0:
                    move_percent = round((curr - prev_year) / prev_year * 100, 1)
            # Gate: only include in stats if abs move > 5%
            if move_percent is None or abs(move_percent) < 5:
                released_days_ago = None   # excluded from homepage stats

        # ── Blurb ────────────────────────────────────────────────────────────
        cache_key  = f'{metric_slug}:{country_slug}'
        has_cached = bool(blurb_cache.get(cache_key))

        if should_generate_blurb(metric_slug, released_days_ago, has_cached) and claude:
            print(f'  Generating blurb: {metric_slug}/{country_slug}...')
            new_blurb = generate_blurb(claude, BLURB_SYSTEM, metric_slug, country_slug, direction, icon_slug_val, reveal)
            if new_blurb:
                blurb_cache[cache_key] = new_blurb
                blurbs_generated += 1
            blurb = blurb_cache.get(cache_key, [])
        else:
            blurb = blurb_cache.get(cache_key, [])

        # ── AP blurb ─────────────────────────────────────────────────────────
        ap_cache_key  = f'ap:{metric_slug}:{country_slug}'
        ap_has_cached = bool(blurb_cache.get(ap_cache_key))
        if should_generate_blurb(metric_slug, released_days_ago, ap_has_cached) and claude:
            print(f'  Generating AP blurb: {metric_slug}/{country_slug}...')
            new_ap_blurb = generate_blurb(claude, BLURB_SYSTEM_AP, metric_slug, country_slug, direction, icon_slug_val, reveal)
            if new_ap_blurb:
                blurb_cache[ap_cache_key] = new_ap_blurb
                blurbs_generated += 1
        blurb_ap = blurb_cache.get(ap_cache_key, [])

        countries_out[country_slug] = {
            'flag':            flag,
            'name':            name,
            'value':           value_str,
            'direction':       direction,
            'releasedDaysAgo': released_days_ago,
            'icon':            icon,
            'correctIcon':     icon_slug_val,
            'weatherReason':   reveal,
            'blurb':           blurb,
            'blurbAp':         blurb_ap,
            'chartDates':      chart_dates,
            'chartSeries':     chart_series,
            'movePercent':     move_percent,
        }

        print(f'  {flag} {country_slug:<10} {metric_slug:<16} {str(value_str):<10} {direction:<5} ({released_days_ago}d ago)')

    metrics[metric_slug] = {
        'slug':      metric_slug,
        'title':     meta['title'],
        'aqaRef':    meta['aqaRef'],
        'unit':      meta['unit'],
        'countries': countries_out,
    }

# ── Write metrics.js ──────────────────────────────────────────────────────────

from datetime import date as _date
last_updated = _date.today().strftime("%-d %B %Y")

js_content = 'export const metrics = ' + json.dumps(metrics, indent=2, ensure_ascii=False) + '\n'
js_content += f'\nexport const lastUpdated = "{last_updated}";\n'

os.makedirs(os.path.dirname(METRICS_JS), exist_ok=True)
with open(METRICS_JS, 'w', encoding='utf-8') as f:
    f.write(js_content)
size_kb = os.path.getsize(METRICS_JS) // 1024
print(f'\nWritten: {METRICS_JS} ({size_kb} KB)')

# ── Write blurb cache ─────────────────────────────────────────────────────────

with open(BLURB_CACHE, 'w', encoding='utf-8') as f:
    json.dump(blurb_cache, f, indent=2, ensure_ascii=False)
print(f'Blurb cache: {len(blurb_cache)} entries ({blurbs_generated} generated this run)')

print('\nsync_edu complete.\n')
