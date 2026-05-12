#!/usr/bin/env python3
"""
MacroSnaps v2 (MACRO-MAY) build script.

Reads data.json + styles.css + charts.js, generates a homepage + 12 country pages
into dist/. Each page is standalone (CSS, JS, and relevant data inlined) so the
folder can be served by any static host.

Usage:
    python3 build.py

Output:
    dist/index.html         (homepage)
    dist/usa.html ... rus.html  (12 country pages)
"""

import json
import os
import sys
import re
import argparse
import html as _html
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(ROOT)  # the main macrosnaps repo
# Prefer the parent repo's data.json so MACRO-MAY stays in sync automatically.
DATA_FILE = os.path.join(PARENT, "data.json")
if not os.path.exists(DATA_FILE):
    DATA_FILE = os.path.join(ROOT, "data.json")  # fallback: local copy
STYLES_FILE = os.path.join(ROOT, "styles.css")
CHARTS_FILE = os.path.join(ROOT, "charts.js")
# DIST_DIR set in main() based on --target flag:
#   --target=local      → MACRO-MAY/dist/        (default, dev server)
#   --target=production → macrosnaps/v2/         (parallel deploy at macrosnaps.app/v2/)

LONDON = ZoneInfo("Europe/London")
TODAY = datetime.now(tz=LONDON).date()
DATE_STAMP = TODAY.strftime("%a %-d %b %Y")  # e.g. "Sat 10 May 2026"

COUNTRY_ORDER = ["USA","CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"]

# Default sort order for the homepage snapshot table: nominal GDP descending (2026).
# Refresh annually. Used only for the snapshot table's initial render; column-click
# sorting in the browser re-orders from there. Country cards and per-page generation
# continue to use COUNTRY_ORDER (geographic grouping).
GDP_RANK_ORDER = ["USA","CHN","DEU","JPN","IND","GBR","FRA","ITA","BRA","CAN","RUS","ZAF"]

MACRO_METRICS = ["GDP Growth", "Inflation (CPI)", "Unemployment",
                 "Budget Deficit", "Current Account", "Policy Rate"]
MARKET_BASE = ["Stock Market YTD", "10Y Bond Yield", "Yield Curve"]
FX_KEYS = {
    "USA":"USD/DXY","CAN":"CAD/USD","GBR":"GBP/USD","JPN":"USD/JPY",
    "DEU":"EUR/USD","FRA":"EUR/USD","ITA":"EUR/USD","CHN":"USD/CNY",
    "IND":"USD/INR","ZAF":"USD/ZAR","BRA":"USD/BRL","RUS":"USD/RUB"
}

# 3-letter country code -> 2-letter ISO for flag SVG filenames in flags/
ISO_CODES = {
    "USA":"us","CAN":"ca","GBR":"gb","JPN":"jp",
    "DEU":"de","FRA":"fr","ITA":"it","CHN":"cn",
    "IND":"in","ZAF":"za","BRA":"br","RUS":"ru"
}
FLAGS_DIR = os.path.join(ROOT, "flags")

# V2 only displays these 3 commodities on the homepage. V1 pipeline keeps writing
# all 9 to data.json (WTI, Brent, Nat Gas, Gold, Silver, Copper, Wheat, Corn,
# Soybeans). Aliases below are matched case-insensitively as substrings of the
# item name from data.json, so naming variants ("Nat Gas" / "Natural Gas") work
# without a pipeline change. Order here is the display order on the page.
COMMODITIES_DISPLAY = [
    ["brent"],                       # Brent Crude
    ["natural gas", "nat gas"],      # Natural Gas
    ["gold"],                        # Gold
]

# Each country's 10 displayed metrics, in order
def country_metric_order(code):
    return MACRO_METRICS + MARKET_BASE + [FX_KEYS[code]]

# Snapshot columns shown on homepage table
SNAPSHOT_COLS = [
    ("GDP",   "macro",  "GDP Growth",      "signed"),
    ("CPI",   "macro",  "Inflation (CPI)", "plain"),
    ("Unemp", "macro",  "Unemployment",    "plain"),
    ("Policy","macro",  "Policy Rate",     "plain"),
    ("10Y",   "market", "10Y Bond Yield",  "plain"),
    ("Stock", "market", "Stock Market YTD","signed"),
    ("FX",    "market", "FX_DYNAMIC",      "signed"),  # picked per country
]

# Display-layer overrides for country-page metric box titles.
# Keys in data.json stay as-is (Stock Market YTD); only the on-page label changes.
DISPLAY_NAMES = {
    "Stock Market YTD": "Stock Market",
}

# Glossary content (lifted from existing site; one entry per metric)
GLOSSARY = {
    "GDP Growth": {
        "title": "What is GDP growth?",
        "body": "GDP growth measures how fast a country's economy is expanding or shrinking. It is the single most important number for understanding whether an economy is healthy, struggling, or in recession.",
        "source": "National statistics offices · IMF"
    },
    "Inflation (CPI)": {
        "title": "What is inflation?",
        "body": "Inflation is a sustained increase in the overall price level of goods and services, which reduces the purchasing power of money over time.",
        "source": "National statistics offices · IMF"
    },
    "Unemployment": {
        "title": "What is the unemployment rate?",
        "body": "The unemployment rate measures what percentage of people who want to work cannot find a job. It is one of the clearest signals of whether an economy is providing enough opportunity for its citizens.",
        "source": "National statistics offices · IMF"
    },
    "Budget Deficit": {
        "title": "What is the budget deficit?",
        "body": "The budget deficit measures how much more a government spends than it earns in a given year. A deficit means the government is borrowing to cover the gap, adding to national debt.",
        "source": "IMF Fiscal Monitor · National finance ministries"
    },
    "Current Account": {
        "title": "What is the current account?",
        "body": "The current account measures whether a country earns more from the rest of the world than it spends. It tracks trade in goods and services, plus income flows like investment returns and remittances.",
        "source": "IMF BOP Statistics"
    },
    "Policy Rate": {
        "title": "What is the policy rate?",
        "body": "The policy rate is the interest rate set by a country's central bank. It is the most powerful tool for controlling inflation and influencing economic growth, because it affects the cost of borrowing for everyone.",
        "source": "National central banks"
    },
    "Stock Market YTD": {
        "title": "What is the stock market YTD?",
        "body": "Stock Market YTD shows how much a country's main stock market index has gone up or down since the start of the year. It is the most visible daily scoreboard for investor confidence in a country's economy and companies.",
        "source": "Exchange data"
    },
    "10Y Bond Yield": {
        "title": "What is the 10-year bond yield?",
        "body": "The 10-year bond yield is the annual return investors earn for lending money to a government for 10 years. It is the most important interest rate in any economy, the benchmark that influences mortgage rates, corporate borrowing costs, and stock valuations.",
        "source": "Bloomberg · Refinitiv"
    },
    "Yield Curve": {
        "title": "What is the yield curve?",
        "body": "The yield curve shows the difference between short-term and long-term government bond yields. Its shape is one of the most reliable predictors of recessions: when long-term rates fall below short-term rates (an inversion), a recession has followed almost every time in history.",
        "source": "Bloomberg · Refinitiv"
    },
    "_FX_DEFAULT": {
        "title": "What is the exchange rate?",
        "body": "The exchange rate is how much one currency is worth in terms of another. It determines the price of everything a country imports and exports, and is one of the most visible daily indicators of a country's economic standing in the world.",
        "source": "WM/Refinitiv · Bloomberg · National central banks"
    }
}

def slug(code):
    return code.lower()

def esc(s):
    if s is None: return ""
    return _html.escape(str(s), quote=True)

def parse_signed(val_str):
    """Return float or None from strings like '+2.3%', '-3.7% GDP', '4.50%'."""
    if val_str is None: return None
    s = str(val_str).strip()
    m = re.search(r'[-+]?\d+(\.\d+)?', s)
    if not m: return None
    try: return float(m.group(0))
    except: return None

def signed_cls(v):
    if v is None: return "muted"
    return "pos" if v >= 0 else "neg"

def format_signed(val_str):
    """Format e.g. '+2.3%' -> '+2.3'; '-0.2%' -> '−0.2'; '4.50%' -> '4.50'."""
    if val_str is None: return "—"
    s = str(val_str).strip().rstrip('%').strip()
    s = s.replace('-', '−')  # unicode minus
    return s

def strip_pct(val_str):
    if val_str is None: return "—"
    return str(val_str).strip()

def format_1dp(val_str, force_sign=False):
    """Format to exactly 1 decimal place for the snapshot table.
    force_sign=True prepends '+' for non-negative values (signed columns).
    Negatives always render with the unicode minus."""
    num = parse_signed(val_str)
    if num is None:
        return "—"
    if num < 0:
        return f"−{abs(num):.1f}"  # unicode minus
    if force_sign:
        return f"+{num:.1f}"
    return f"{num:.1f}"

# Flag SVG loader: read once, inline into the homepage HTML.
# Strips root width/height so CSS controls sizing in .flag-rect.
_flag_cache = {}
def get_flag_svg(country_code):
    if country_code in _flag_cache:
        return _flag_cache[country_code]
    iso = ISO_CODES.get(country_code)
    if not iso:
        _flag_cache[country_code] = ""
        return ""
    path = os.path.join(FLAGS_DIR, f"{iso}.svg")
    if not os.path.exists(path):
        _flag_cache[country_code] = ""
        return ""
    with open(path) as f:
        svg = f.read()
    # Strip width="..." / height="..." from the root <svg> tag
    svg = re.sub(r'(<svg\b[^>]*?)\s+width="[^"]*"', r'\1', svg, count=1)
    svg = re.sub(r'(<svg\b[^>]*?)\s+height="[^"]*"', r'\1', svg, count=1)
    _flag_cache[country_code] = svg
    return svg

def render_stories_ol(stories, size="lg"):
    cls = "stories" if size == "lg" else "stories sm"
    items = "".join(f"<li>{esc(s)}</li>" for s in stories)
    return f'<ol class="{cls}">{items}</ol>'

def render_metric_box(country, metric_name, group):
    """Render one metric section box."""
    metric = country['metrics'].get(group, {}).get(metric_name, {})
    if not metric:
        return ""
    value = metric.get('value', '—')
    stories = metric.get('story', {}).get('beginner', [])
    if not isinstance(stories, list): stories = [stories]

    # Display label override (key stays unchanged for data lookups and consumers)
    display_name = DISPLAY_NAMES.get(metric_name, metric_name)

    # Value color: GDP +/-, Stock YTD +/-, FX vs USD, otherwise neutral
    color_metrics = {"GDP Growth", "Stock Market YTD"}
    is_fx = "/" in metric_name
    val_color = ""
    val_num = parse_signed(value)
    if metric_name in color_metrics and val_num is not None:
        val_color = " pos" if val_num >= 0 else " neg"

    # Chart data from _frozen_historical
    fh = country.get('_frozen_historical', {}).get(metric_name, {})
    chart_html = ""
    if fh.get('v'):
        is_bar = fh.get('type') == 'bar' or fh.get('annual') is True
        chart_data_json = json.dumps({
            'v': fh.get('v', []),
            'startDate': fh.get('startDate', None),
            'type': fh.get('type', 'line')
        })
        if is_bar:
            range_btns = ""
            title_suffix = "Annual"
        else:
            range_btns = """
            <div class="metric-chart-range">
              <button class="mcr-btn" data-r="12">1Y</button>
              <button class="mcr-btn" data-r="24">2Y</button>
              <button class="mcr-btn" data-r="60">5Y</button>
              <button class="mcr-btn" data-r="0">All</button>
            </div>"""
            title_suffix = "History since 2000"
        chart_html = f"""
        <div class="metric-chart-wrap" data-metric="{esc(metric_name)}" data-chart='{esc(chart_data_json)}'>
          <div class="metric-chart-head">
            <div class="metric-chart-title">{esc(display_name)} · {title_suffix}</div>{range_btns}
          </div>
          <div class="metric-chart-canvas"><canvas></canvas></div>
        </div>"""

    # Glossary
    gloss_key = "_FX_DEFAULT" if is_fx else metric_name
    gloss = GLOSSARY.get(gloss_key, GLOSSARY["_FX_DEFAULT"])

    # FX regime block (only for FX metric, when fxRegime present on country)
    fx_regime_html = ""
    if is_fx:
        fx_regime = country.get('fxRegime') or {}
        fx_label = fx_regime.get('label', '')
        fx_body = fx_regime.get('beginner', '')
        if fx_body:
            label_str = f"{country.get('name', '')}'s FX regime"
            if fx_label:
                label_str = f"{label_str}: {fx_label}"
            fx_regime_html = f"""
        <div class="fx-regime">
          <div class="fx-label">{esc(label_str)}</div>
          <p>{esc(fx_body)}</p>
        </div>"""

    return f"""
    <div class="box">
      <div class="metric-head">
        <h2>{esc(display_name)}</h2>
        <div class="metric-value{val_color}">{esc(value)}</div>
      </div>
      {render_stories_ol(stories, 'sm')}
      {chart_html}
      {fx_regime_html}
      <div class="gloss">
        <div class="gloss-title">{esc(gloss['title'])}</div>
        <p class="gloss-body">{esc(gloss['body'])}</p>
        <div class="gloss-source">Source: {esc(gloss['source'])}</div>
      </div>
    </div>"""

def render_page_shell(title, body_html, styles_css, charts_js):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>{styles_css}</style>
</head>
<body>
{body_html}
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>{charts_js}</script>
</body>
</html>"""

def render_homepage(data, styles_css, charts_js):
    # Top headlines from globalStories.beginner
    gs = data.get('globalStories', {}).get('beginner', [])
    # globalStories.beginner is a list of {icon, label, source, bullets}
    # For headlines, we want 3 short sentences. Use the label + first bullet as the line.
    headlines = []
    for item in gs[:3]:
        if isinstance(item, dict):
            bullets = item.get('bullets', [])
            if bullets:
                headlines.append(bullets[0])
            elif item.get('label'):
                headlines.append(item['label'])
        elif isinstance(item, str):
            headlines.append(item)
    while len(headlines) < 3:
        headlines.append("")

    # Snapshot table rows (default order: nominal GDP descending; click any header to re-sort)
    rows_html = []
    for code in GDP_RANK_ORDER:
        country = data['countries'].get(code, {})
        if not country: continue
        flag_svg = get_flag_svg(code)
        code_td = (
            f'<td data-sort="{esc(code)}">'
            f'<span class="code-cell">'
            f'<span class="row-flag">{flag_svg}</span>'
            f'<span class="code-text">{esc(code)}</span>'
            f'<span class="row-arrow">→</span>'
            f'</span>'
            f'</td>'
        )
        cells = []
        for label, group, metric_key, fmt in SNAPSHOT_COLS:
            if metric_key == "FX_DYNAMIC":
                # FX YTD vs USD, derived from Stock YTD (local vs USD).
                # USA: no value (DXY is a basket, USD-vs-USD = 0 by definition).
                if code == "USA":
                    cells.append('<td class="muted" data-sort="">—</td>'); continue
                mkt = country.get('metrics', {}).get('market', {})
                local_str = mkt.get('Stock Market YTD', {}).get('value')
                usd_val = mkt.get('Stock Market YTD (USD)', {}).get('value')
                local_pct = parse_signed(local_str)
                try: usd_pct = float(usd_val)
                except (TypeError, ValueError): usd_pct = None
                if local_pct is None or usd_pct is None:
                    cells.append('<td class="muted" data-sort="">—</td>'); continue
                try:
                    fx_ytd = ((1 + usd_pct / 100.0) / (1 + local_pct / 100.0) - 1) * 100.0
                except ZeroDivisionError:
                    cells.append('<td class="muted" data-sort="">—</td>'); continue
                fx_rounded = round(fx_ytd, 1)
                cls = signed_cls(fx_rounded)
                disp = format_1dp(f"{fx_rounded}", force_sign=True)
                cells.append(f'<td class="{cls}" data-sort="{fx_rounded}">{esc(disp)}</td>')
                continue
            metric = country['metrics'].get(group, {}).get(metric_key, {})
            val = metric.get('value', None)
            if val is None:
                cells.append('<td class="muted" data-sort="">—</td>'); continue
            num = parse_signed(val)
            sort_attr = f' data-sort="{num}"' if num is not None else ' data-sort=""'
            if fmt == 'signed':
                cls = signed_cls(num)
                cells.append(f'<td class="{cls}"{sort_attr}>{esc(format_1dp(val, force_sign=True))}</td>')
            else:
                cells.append(f'<td{sort_attr}>{esc(format_1dp(val))}</td>')
        rows_html.append(
            f'<tr class="clickable" data-href="{esc(slug(code))}.html">{code_td}{"".join(cells)}</tr>'
        )

    snapshot_html = f"""
    <table class="snapshot">
      <colgroup><col style="width:96px"><col><col><col><col><col><col><col></colgroup>
      <thead>
        <tr>
          <th class="sortable" data-col="0"><span class="th-label"></span><span class="sort-arrow"></span></th>
          {"".join(f'<th class="sortable" data-col="{i+1}"><span class="th-label">{esc(c[0])}</span><span class="sort-arrow"></span></th>' for i, c in enumerate(SNAPSHOT_COLS))}
        </tr>
      </thead>
      <tbody>
        {"".join(rows_html)}
      </tbody>
    </table>"""

    # Commodities (V2 display: filter the 9 in data.json down to our 3, in order)
    raw_commodities = data.get('commodities', {}).get('items', [])
    commodities = []
    seen_idx = set()
    for aliases in COMMODITIES_DISPLAY:
        for i, item in enumerate(raw_commodities):
            if i in seen_idx: continue
            nm_lower = item.get('name', '').lower()
            if any(a in nm_lower for a in aliases):
                commodities.append(item)
                seen_idx.add(i)
                break
    comm_html = []
    for item in commodities:
        nm = item.get('name', '')
        price = item.get('price', '')
        change = item.get('change', None)
        unit = item.get('unit', '')
        # Format change
        if change is None:
            change_html = ''
        else:
            try:
                ch = float(change)
                ch_cls = 'pos' if ch >= 0 else 'neg'
                ch_str = ('+' if ch >= 0 else '−') + f'{abs(ch):.1f}%'
                change_html = f'<span class="c-change {ch_cls}">{esc(ch_str)}</span>'
            except:
                change_html = ''
        # Format price
        try:
            p = float(price)
            if p >= 1000:
                price_str = f'${p:,.0f}'
            elif p >= 100:
                price_str = f'${p:.2f}'
            else:
                price_str = f'${p:.2f}'
        except:
            price_str = str(price)
        comm_html.append(f"""
        <div class="commodity-item">
          <div class="c-name">{esc(nm)}</div>
          <div class="c-value">{esc(price_str)}{change_html}</div>
        </div>""")

    body = f"""
<div class="page">

  <div class="box compact">
    <div class="head-row no-divider">
      <h1 class="brand">MacroSnaps</h1>
      <span class="date">{esc(DATE_STAMP)}</span>
    </div>
  </div>

  <div class="box">
    <div class="section-label">Today's headlines</div>
    {render_stories_ol(headlines, 'lg')}
  </div>

  <div class="box">
    <div class="section-label">Snapshot</div>
    {snapshot_html}
  </div>

  <div class="box">
    <div class="section-label">Commodities</div>
    <div class="commodities-grid">{"".join(comm_html)}</div>
  </div>

  <div class="footer">
    Built {esc(DATE_STAMP)} · macrosnaps.app
  </div>

</div>

<script>
(function () {{
  var table = document.querySelector('.snapshot');
  if (!table) return;
  var tbody = table.tBodies[0];
  var headers = table.tHead.rows[0].cells;
  var originalOrder = Array.prototype.slice.call(tbody.rows);
  var currentCol = -1;
  var asc = false;

  for (var i = 0; i < headers.length; i++) {{
    (function (idx) {{
      headers[idx].addEventListener('click', function () {{ sortBy(idx); }});
    }})(i);
  }}

  // Row click navigates to the country page.
  // Sort happens on <th> only, navigation on <td> only - no conflict.
  Array.prototype.slice.call(tbody.rows).forEach(function (row) {{
    var href = row.getAttribute('data-href');
    if (!href) return;
    row.addEventListener('click', function () {{ window.location.href = href; }});
  }});

  function sortBy(col) {{
    var isText = (col === 0);
    if (currentCol === col) {{
      asc = !asc;
    }} else {{
      asc = isText ? true : false;  // text: A→Z first; numeric: highest first
      currentCol = col;
    }}
    var rows = Array.prototype.slice.call(tbody.rows);
    rows.sort(function (a, b) {{
      var av = a.cells[col].getAttribute('data-sort') || a.cells[col].textContent;
      var bv = b.cells[col].getAttribute('data-sort') || b.cells[col].textContent;
      if (isText) {{
        return av.localeCompare(bv);
      }}
      var aNum = parseFloat(av);
      var bNum = parseFloat(bv);
      var aNull = isNaN(aNum);
      var bNull = isNaN(bNum);
      if (aNull && bNull) return 0;
      if (aNull) return 1;
      if (bNull) return -1;
      return bNum - aNum;
    }});
    if (asc) rows.reverse();
    rows.forEach(function (r) {{ tbody.appendChild(r); }});
    updateArrows();
  }}

  function updateArrows() {{
    for (var i = 0; i < headers.length; i++) {{
      var arrow = headers[i].querySelector('.sort-arrow');
      headers[i].classList.toggle('active', i === currentCol);
      if (arrow) {{
        arrow.textContent = (i === currentCol) ? (asc ? '↑' : '↓') : '';
      }}
    }}
  }}
}})();
</script>"""

    return render_page_shell(f"MacroSnaps · {DATE_STAMP}", body, styles_css, charts_js)

def render_country_page(data, code, styles_css, charts_js):
    country = data['countries'][code]
    name = country.get('name', code)
    stories = country.get('stories', {}).get('beginner', [])
    if not isinstance(stories, list): stories = []

    metric_boxes = []
    for m in MACRO_METRICS:
        metric_boxes.append(render_metric_box(country, m, 'macro'))
    for m in MARKET_BASE:
        metric_boxes.append(render_metric_box(country, m, 'market'))
    fx_metric = FX_KEYS[code]
    metric_boxes.append(render_metric_box(country, fx_metric, 'market'))

    body = f"""
<div class="page">

  <div class="box compact">
    <div class="head-row">
      <a class="back-link" href="index.html">← MacroSnaps</a>
      <span class="date">{esc(DATE_STAMP)}</span>
    </div>
    <div class="country-title">
      <h1>{esc(name)}</h1>
      <span class="flag-pill">{esc(code)}</span>
    </div>
  </div>

  <div class="box">
    <div class="section-label">Today</div>
    {render_stories_ol(stories[:3], 'lg')}
  </div>

  {"".join(metric_boxes)}

  <div class="footer">
    Built {esc(DATE_STAMP)} · macrosnaps.app · <a href="index.html">All countries</a>
  </div>

</div>"""

    return render_page_shell(f"{name} · MacroSnaps", body, styles_css, charts_js)

def main():
    parser = argparse.ArgumentParser(description="Build MacroSnaps v2 site.")
    parser.add_argument('--target', choices=['local', 'production'], default='local',
                        help="local (default): write to MACRO-MAY/dist/. "
                             "production: write to macrosnaps/v2/ for parallel deploy at macrosnaps.app/v2/")
    args = parser.parse_args()

    if args.target == 'production':
        dist_dir = os.path.join(PARENT, "v2")
        target_label = "PRODUCTION (parallel deploy at macrosnaps.app/v2/)"
    else:
        dist_dir = os.path.join(ROOT, "dist")
        target_label = "LOCAL (dev server)"

    # Load inputs
    if not os.path.exists(DATA_FILE):
        print(f"FATAL: data.json not found at {DATA_FILE}")
        sys.exit(1)
    with open(DATA_FILE) as f:
        data = json.load(f)
    with open(STYLES_FILE) as f:
        styles_css = f.read()
    with open(CHARTS_FILE) as f:
        charts_js = f.read()

    os.makedirs(dist_dir, exist_ok=True)

    print(f"\nMacroSnaps v2 build — {DATE_STAMP}")
    print(f"Target: {target_label}")
    print(f"Data:   {DATA_FILE}")
    print(f"Output: {dist_dir}\n")

    # Homepage
    homepage_html = render_homepage(data, styles_css, charts_js)
    out = os.path.join(dist_dir, "index.html")
    with open(out, "w") as f:
        f.write(homepage_html)
    print(f"  ✓ index.html  ({os.path.getsize(out)//1024} KB)")

    # Country pages
    for code in COUNTRY_ORDER:
        if code not in data['countries']:
            print(f"  ⚠  Missing country: {code}")
            continue
        page_html = render_country_page(data, code, styles_css, charts_js)
        out = os.path.join(dist_dir, f"{slug(code)}.html")
        with open(out, "w") as f:
            f.write(page_html)
        print(f"  ✓ {slug(code)}.html  ({os.path.getsize(out)//1024} KB)")

    if args.target == 'production':
        print(f"\nDone. Built to {dist_dir}.")
        print(f"Next: cd {PARENT} && git add v2/ && git commit -m 'v2 update' && git push")
    else:
        print(f"\nDone. Serve with:  bash serve.sh")

if __name__ == "__main__":
    main()
