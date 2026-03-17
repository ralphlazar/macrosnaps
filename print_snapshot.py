#!/usr/bin/env python3
"""
print_snapshot.py

Generate a dated, print-friendly PDF snapshot of MacroSnaps for archiving
and pipeline auditing. Reads data.json directly; does not open the live site.

Requirements (one-time):
  pip3 install playwright --break-system-packages
  playwright install chromium

Usage:
  python3 print_snapshot.py
  python3 print_snapshot.py --date 2026-03-15   # override date label only
"""

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GDP_NOMINAL_ORDER = [
    "USA", "CHN", "DEU", "JPN", "IND", "GBR",
    "FRA", "ITA", "BRA", "CAN", "RUS", "ZAF",
]

CARD_MARKET_EXCLUDE = {"Stock Market Index", "FX Rate", "Stock Market YTD (USD)"}

MACRO_ORDER = [
    "GDP Growth",
    "Inflation (CPI)",
    "Unemployment",
    "Budget Deficit",
    "Current Account",
    "Policy Rate",
]

# Maps macro metric name to the monthly_actuals sub-key in data.json
MONTHLY_ACTUALS_KEY = {
    "Inflation (CPI)": "inflation",
    "Unemployment":    "unemployment",
    "Policy Rate":     "policy_rate",
}

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

CHARTJS_CDN  = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
DATALABS_CDN = ("https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels"
                "/2.2.0/chartjs-plugin-datalabels.min.js")

DATA_FILE     = Path(__file__).parent / "data.json"
SNAPSHOTS_DIR = Path(__file__).parent / "00-snapshots"


# ---------------------------------------------------------------------------
# Date / label helpers
# ---------------------------------------------------------------------------

def prev_month(y: int, m: int, steps: int = 1) -> tuple[int, int]:
    """Step (y, m) back by `steps` months."""
    for _ in range(steps):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return y, m


def monthly_labels(n: int, generated: str) -> list[str]:
    """Return n 'Mon YYYY' labels ending at the generated month."""
    gen = date.fromisoformat(generated)
    y, m = gen.year, gen.month
    out: list[str] = []
    for i in range(n - 1, -1, -1):
        ry, rm = prev_month(y, m, i)
        out.append(f"{MONTH_NAMES[rm - 1]} {ry}")
    return out


def annual_labels(n: int, start: int = 2000) -> list[str]:
    return [str(start + i) for i in range(n)]


def last_non_null(v: list) -> int | None:
    for i in range(len(v) - 1, -1, -1):
        if v[i] is not None:
            return i
    return None


# ---------------------------------------------------------------------------
# Value formatting for chart annotations
# ---------------------------------------------------------------------------

# Metrics whose _frozen_historical v[] stores percentage floats
_PCT_METRICS = {
    "GDP Growth", "Inflation (CPI)", "Unemployment",
    "Policy Rate", "10Y Bond Yield",
}
# Metrics whose v[] stores % of GDP
_GDP_METRICS = {"Budget Deficit", "Current Account"}


def fmt_metric_val(metric: str, val) -> str:
    """Human-readable string for the last-point chart annotation."""
    if val is None:
        return "N/A"
    if metric in _PCT_METRICS:
        return f"{val:.1f}%"
    if metric in _GDP_METRICS:
        return f"{val:.1f}% GDP"
    if metric == "Yield Curve":
        return f"{int(round(val))} bps"
    # Generic: FX rates, index levels, commodity prices
    a = abs(val)
    if a >= 10_000:
        return f"{val:,.0f}"
    if a >= 1_000:
        return f"{val:,.0f}"
    if a >= 100:
        return f"{val:.2f}"
    if a >= 10:
        return f"{val:.2f}"
    if a >= 1:
        return f"{val:.3f}"
    return f"{val:.5f}"


def fmt_commodity_val(val, unit: str) -> str:
    """Annotation label for commodity sparkline last point."""
    if val is None:
        return "N/A"
    a = abs(val)
    num = f"{val:,.0f}" if a >= 1_000 else f"{val:.2f}"
    return f"{num} {unit}".strip()


# ---------------------------------------------------------------------------
# Monthly-actuals label reconstruction
# ---------------------------------------------------------------------------

def build_ma_labels(entries: list, generated: str) -> list[str]:
    """
    Reconstruct human-readable 'Mon YYYY' labels for monthly_actuals entries
    (sorted newest-first).

    The stored month field is 'DD/MM/Y' where Y is the first digit of the
    four-digit year (an artefact of how gspread serialises dates). We recover
    the full year by stepping backward from the generated month and matching
    on the MM component.
    """
    gen = date.fromisoformat(generated)
    y, m = prev_month(gen.year, gen.month, 1)   # start one month before generated

    labels: list[str] = []
    for entry in entries:
        stored_m = int(entry["month"].split("/")[1])   # extract MM component (1-12)
        steps = 0
        while m != stored_m and steps < 24:
            y, m = prev_month(y, m, 1)
            steps += 1
        labels.append(f"{MONTH_NAMES[m - 1]} {y}")
        y, m = prev_month(y, m, 1)

    return labels


# ---------------------------------------------------------------------------
# Weather icon from GDP Growth value
# ---------------------------------------------------------------------------

def gdp_weather(country: dict) -> str:
    """Derive ☀️/☁️/⛈️ from the GDP Growth metric value string."""
    raw = country["metrics"]["macro"].get("GDP Growth", {}).get("value", "")
    try:
        val = float(
            raw.replace("%", "")
               .replace("+", "")
               .replace(" GDP", "")
               .strip()
        )
    except ValueError:
        return "☁️"
    if val >= 3:
        return "☀️"
    if val >= 0:
        return "☁️"
    return "⛈️"


# ---------------------------------------------------------------------------
# Chart config builders
# ---------------------------------------------------------------------------

def make_metric_chart_cfg(canvas_id: str, metric: str, fh: dict, generated: str) -> dict:
    """Build a serialisable chart-config dict for one metric."""
    v      = fh["v"]
    is_bar = bool(fh.get("annual")) or fh.get("type") == "bar"
    labels = annual_labels(len(v)) if is_bar else monthly_labels(len(v), generated)

    idx        = last_non_null(v)
    last_label = labels[idx] if idx is not None else ""
    last_val   = fmt_metric_val(metric, v[idx]) if idx is not None else "N/A"

    return {
        "id":        canvas_id,
        "type":      "bar" if is_bar else "line",
        "labels":    labels,
        "data":      v,
        "lastIdx":   idx,
        "lastLabel": last_label,
        "lastVal":   last_val,
    }


def make_commodity_chart_cfg(canvas_id: str, item: dict, generated: str) -> dict:
    """Build chart config for a commodity using its 120-pt spark array."""
    spark  = item.get("spark", [])
    labels = monthly_labels(len(spark), generated)

    idx        = last_non_null(spark)
    last_label = labels[idx] if idx is not None else ""
    last_val   = fmt_commodity_val(spark[idx] if idx is not None else None,
                                   item.get("unit", ""))
    return {
        "id":        canvas_id,
        "type":      "line",
        "labels":    labels,
        "data":      spark,
        "lastIdx":   idx,
        "lastLabel": last_label,
        "lastVal":   last_val,
    }


# ---------------------------------------------------------------------------
# HTML fragment builders
# ---------------------------------------------------------------------------

def render_metrics_table(country: dict) -> str:
    macro  = country["metrics"].get("macro", {})
    market = country["metrics"].get("market", {})
    rows: list[str] = []

    rows.append('<tr><td colspan="3" class="section-label">Macro Indicators</td></tr>')
    for mname in MACRO_ORDER:
        if mname not in macro:
            continue
        mv = macro[mname]
        rows.append(
            f'<tr>'
            f'<td>{mname}</td>'
            f'<td class="val">{mv.get("value", "")}</td>'
            f'<td class="date">{mv.get("last_updated", "")}</td>'
            f'</tr>'
        )

    visible_market = [k for k in market if k not in CARD_MARKET_EXCLUDE]
    if visible_market:
        rows.append('<tr><td colspan="3" class="section-label">Market Metrics</td></tr>')
        for mname in visible_market:
            mv = market[mname]
            rows.append(
                f'<tr>'
                f'<td>{mname}</td>'
                f'<td class="val">{mv.get("value", "")}</td>'
                f'<td class="date">{mv.get("last_updated", "")}</td>'
                f'</tr>'
            )

    return (
        '<table class="metrics-table">'
        '<thead><tr><th>Metric</th><th>Value</th><th>Last Updated</th></tr></thead>'
        '<tbody>' + "".join(rows) + '</tbody>'
        '</table>'
    )


def render_ma_inset(country: dict, metric: str, generated: str) -> str:
    """3-row monthly actuals table, shown below Inflation / Unemployment / Policy Rate charts."""
    ma_key  = MONTHLY_ACTUALS_KEY.get(metric)
    if not ma_key:
        return ""
    ma_data = country.get("monthly_actuals", {}).get(ma_key, [])
    if not ma_data:
        return ""

    top3   = ma_data[:3]
    labels = build_ma_labels(top3, generated)
    rows   = "".join(
        f'<tr><td>{labels[i]}</td>'
        f'<td class="ma-val">{top3[i]["value"]}</td></tr>'
        for i in range(len(top3))
    )
    return (
        '<table class="ma-table">'
        '<thead><tr><th>Month</th><th>Actual</th></tr></thead>'
        '<tbody>' + rows + '</tbody>'
        '</table>'
        '<p class="ma-caption">Monthly actuals - recent 3</p>'
    )


def _canvas_id(code: str, metric: str) -> str:
    safe = (metric
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("/", "_")
            .replace("%", "pct"))
    return f"c_{code}_{safe}"


def build_country_section(
    code: str,
    country: dict,
    generated: str,
    chart_configs: list,
) -> str:
    flag    = country.get("flag", "")
    name    = country.get("name", code)
    wx      = gdp_weather(country)

    header = (
        '<div class="country-header">'
        f'<span class="flag">{flag}</span>'
        f'<span class="name">{name}</span>'
        f'<span class="code">({code})</span>'
        f'<span class="wx">{wx}</span>'
        '</div>'
    )

    table  = render_metrics_table(country)
    fh_all = country.get("_frozen_historical", {})

    macro  = country["metrics"].get("macro", {})
    market = country["metrics"].get("market", {})
    ordered_metrics = (
        [(m, "macro")  for m in MACRO_ORDER if m in macro] +
        [(m, "market") for m in market if m not in CARD_MARKET_EXCLUDE]
    )

    chart_blocks: list[str] = []
    for mname, section in ordered_metrics:
        fh = fh_all.get(mname)
        if not fh or not fh.get("v"):
            continue

        cid = _canvas_id(code, mname)
        cfg = make_metric_chart_cfg(cid, mname, fh, generated)
        chart_configs.append(cfg)

        ma_html = render_ma_inset(country, mname, generated) if section == "macro" else ""

        chart_blocks.append(
            f'<div class="chart-block">'
            f'<div class="chart-title">{mname}</div>'
            f'<canvas id="{cid}" width="300" height="140"></canvas>'
            + ma_html +
            '</div>'
        )

    charts_section = (
        '<div class="charts-grid">' + "".join(chart_blocks) + '</div>'
        if chart_blocks else ""
    )

    return (
        '<div class="country-page">'
        + header + table + charts_section +
        '</div>\n'
    )


def build_commodities_section(
    data: dict,
    generated: str,
    chart_configs: list,
) -> str:
    items = data.get("commodities", {}).get("items", [])
    if not items:
        return ""

    blocks: list[str] = []
    for item in items:
        name   = item.get("name", "")
        price  = item.get("price", "")
        change = item.get("change", 0)
        unit   = item.get("unit", "")
        cid    = f"com_{name.replace(' ', '_').replace('/', '_')}"

        cfg = make_commodity_chart_cfg(cid, item, generated)
        chart_configs.append(cfg)

        # Format change with explicit sign
        if isinstance(change, (int, float)):
            sign         = "+" if change >= 0 else ""
            change_str   = f"{sign}{change:.2f}"
            change_color = "#16a34a" if change >= 0 else "#dc2626"
        else:
            change_str   = str(change)
            change_color = "#444"

        # Format price
        price_str = fmt_commodity_val(price, unit) if isinstance(price, (int, float)) else f"{price} {unit}".strip()

        title = (
            f'<div class="chart-title">'
            f'{name}'
            f'<span class="com-price"> {price_str}</span>'
            f'<span class="com-change" style="color:{change_color}"> {change_str}</span>'
            f'</div>'
        )

        blocks.append(
            '<div class="commodity-block">'
            + title +
            f'<canvas id="{cid}" width="200" height="110"></canvas>'
            '</div>'
        )

    return (
        '<div class="commodities-page">'
        '<div class="section-header">Commodities</div>'
        '<div class="commodity-grid">' + "".join(blocks) + '</div>'
        '</div>\n'
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: Arial, Helvetica, sans-serif;
  background: #fff;
  color: #111;
  font-size: 10pt;
}

/* ---- Country page ---- */
.country-page {
  page-break-after: always;
  padding-bottom: 8mm;
}
.country-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  border-bottom: 2px solid #111;
  padding-bottom: 4px;
  margin-bottom: 8px;
}
.country-header .flag { font-size: 20px; line-height: 1; }
.country-header .name { font-size: 15pt; font-weight: bold; }
.country-header .code { font-size: 9pt; color: #666; }
.country-header .wx   { font-size: 16px; margin-left: auto; }

/* ---- Metrics table ---- */
.metrics-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 10px;
  font-size: 8pt;
}
.metrics-table th {
  background: #efefef;
  text-align: left;
  padding: 3px 6px;
  border: 1px solid #ccc;
  font-weight: bold;
}
.metrics-table td {
  padding: 3px 6px;
  border: 1px solid #ddd;
}
.metrics-table .val  { font-weight: bold; }
.metrics-table .date { color: #666; }
.metrics-table .section-label {
  background: #e4e4e4;
  font-weight: bold;
  font-size: 7pt;
  color: #444;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ---- Charts grid: 2 per row ---- */
.charts-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chart-block {
  width: calc(50% - 4px);
  border: 1px solid #e0e0e0;
  border-radius: 3px;
  padding: 5px 7px;
  background: #fff;
  page-break-inside: avoid;
}
.chart-title {
  font-size: 7.5pt;
  font-weight: bold;
  color: #222;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chart-block canvas { display: block; }

/* ---- Monthly actuals inset ---- */
.ma-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 4px;
  font-size: 7pt;
}
.ma-table th {
  background: #f5f5f5;
  padding: 2px 5px;
  border: 1px solid #ccc;
  text-align: left;
}
.ma-table td { padding: 2px 5px; border: 1px solid #eee; }
.ma-table .ma-val { text-align: right; font-weight: bold; }
.ma-caption { font-size: 6pt; color: #888; margin-top: 2px; }

/* ---- Commodities section ---- */
.commodities-page { padding-bottom: 8mm; }
.section-header {
  font-size: 14pt;
  font-weight: bold;
  border-bottom: 2px solid #111;
  padding-bottom: 4px;
  margin-bottom: 10px;
}
.commodity-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.commodity-block {
  width: calc(33.33% - 6px);
  border: 1px solid #e0e0e0;
  border-radius: 3px;
  padding: 5px 7px;
  page-break-inside: avoid;
}
.commodity-block canvas { display: block; }
.com-price  { font-weight: normal; color: #444; }
.com-change { font-weight: normal; }

/* ---- Global header strip ---- */
.doc-header {
  font-size: 7.5pt;
  color: #888;
  text-align: right;
  margin-bottom: 6px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 3px;
}

@media print {
  .country-page    { page-break-after: always; }
  .chart-block     { page-break-inside: avoid; }
  .commodity-block { page-break-inside: avoid; }
}
"""


# ---------------------------------------------------------------------------
# JS chart renderer (injected as a single inline script block)
# ---------------------------------------------------------------------------

# CHART_CONFIGS_PLACEHOLDER is replaced at runtime with JSON.
_JS_RENDERER = r"""
(function () {
  if (typeof Chart === 'undefined' || typeof ChartDataLabels === 'undefined') {
    console.error('Chart.js or chartjs-plugin-datalabels not loaded');
    window.allChartsRendered = true;
    return;
  }

  Chart.register(ChartDataLabels);

  var configs = CHART_CONFIGS_PLACEHOLDER;

  configs.forEach(function (cfg) {
    var el = document.getElementById(cfg.id);
    if (!el) return;
    var ctx = el.getContext('2d');
    var isBar = cfg.type === 'bar';

    // pointRadius: 0 for all points except the last non-null (shown as filled dot)
    var pointRadii = cfg.data.map(function (_, i) {
      return i === cfg.lastIdx ? 5 : 0;
    });

    new Chart(ctx, {
      type: cfg.type,
      data: {
        labels: cfg.labels,
        datasets: [{
          data:               cfg.data,
          backgroundColor:    isBar ? '#bfdbfe' : 'rgba(37,99,235,0.06)',
          borderColor:        '#2563eb',
          borderWidth:        isBar ? 1 : 1.5,
          pointRadius:        isBar ? undefined : pointRadii,
          pointBackgroundColor: '#dc2626',
          fill:               !isBar,
          tension:            0.2,
          spanGaps:           true
        }]
      },
      options: {
        responsive: false,
        animation:  false,
        layout: { padding: { top: 22, right: 8, bottom: 2, left: 2 } },
        plugins: {
          legend:  { display: false },
          tooltip: { enabled: false },
          datalabels: {
            display: function (context) {
              return context.dataIndex === cfg.lastIdx;
            },
            formatter: function () {
              return cfg.lastLabel + ': ' + cfg.lastVal;
            },
            color:           '#111',
            font:            { size: 7, weight: 'bold' },
            anchor:          'end',
            align:           'top',
            offset:          2,
            backgroundColor: 'rgba(255,255,255,0.92)',
            borderColor:     '#bbb',
            borderWidth:     0.5,
            borderRadius:    2,
            padding:         { top: 1, bottom: 1, left: 3, right: 3 },
            clamp:           true
          }
        },
        scales: {
          x: {
            ticks: {
              color:        '#555',
              font:         { size: 6.5 },
              maxTicksLimit: 6,
              maxRotation:  0,
              autoSkip:     true
            },
            grid: { color: '#ececec' }
          },
          y: {
            ticks: { color: '#555', font: { size: 6.5 } },
            grid:  { color: '#ececec' }
          }
        }
      },
      plugins: [ChartDataLabels]
    });
  });

  window.allChartsRendered = true;
}());
"""


# ---------------------------------------------------------------------------
# Full HTML assembly
# ---------------------------------------------------------------------------

def _fetch_js(url: str) -> str:
    """Fetch a JS library and return its source as a string for inlining."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def build_html(data: dict, label_date: str, chartjs_src: str, datalabels_src: str) -> str:
    generated = data["_meta"]["generated"]
    built_at  = data["_meta"].get("built_at", generated)

    chart_configs: list = []

    country_sections = "".join(
        build_country_section(code, data["countries"][code], generated, chart_configs)
        for code in GDP_NOMINAL_ORDER
        if code in data["countries"]
    )

    commodity_section = build_commodities_section(data, generated, chart_configs)

    js_body = _JS_RENDERER.replace(
        "CHART_CONFIGS_PLACEHOLDER",
        json.dumps(chart_configs, separators=(",", ":")),
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MacroSnaps Snapshot - {label_date}</title>
  <script>{chartjs_src}</script>
  <script>{datalabels_src}</script>
  <style>{CSS}</style>
</head>
<body>
  <div class="doc-header">
    MacroSnaps snapshot - {label_date} - data built {built_at}
  </div>
  {country_sections}
  {commodity_section}
  <script>{js_body}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# PDF generation via Playwright
# ---------------------------------------------------------------------------

async def _generate_pdf(html: str, output_path: str) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()
        await page.set_viewport_size({"width": 1200, "height": 900})
        # Load page and wait for CDN scripts (networkidle ensures Chart.js is ready)
        await page.set_content(html, wait_until="networkidle")
        # Wait until every Chart.js instance has been created
        await page.wait_for_function(
            "window.allChartsRendered === true",
            timeout=120_000,
        )
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={
                "top":    "15mm",
                "right":  "15mm",
                "bottom": "15mm",
                "left":   "15mm",
            },
        )
        await browser.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a print-friendly PDF snapshot of MacroSnaps."
    )
    parser.add_argument(
        "--date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Override the date label in the filename and header "
             "(still reads current data.json).",
    )
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print(f"[ERROR] data.json not found at {DATA_FILE}", file=sys.stderr)
        sys.exit(1)

    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    label_date = args.date or data["_meta"]["generated"]
    try:
        date.fromisoformat(label_date)
    except ValueError:
        print(
            f"[ERROR] Invalid date '{label_date}' - expected YYYY-MM-DD",
            file=sys.stderr,
        )
        sys.exit(1)

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(SNAPSHOTS_DIR / f"macrosnaps-{label_date}.pdf")

    print("[1/4] Fetching Chart.js libraries...")
    try:
        chartjs_src    = _fetch_js(CHARTJS_CDN)
        datalabels_src = _fetch_js(DATALABS_CDN)
    except Exception as exc:
        print(f"[ERROR] Failed to fetch JS libraries: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[2/4] Building HTML ({len(GDP_NOMINAL_ORDER)} countries + commodities)...")
    html = build_html(data, label_date, chartjs_src, datalabels_src)

    print("[3/4] Launching Playwright (Chromium)...")
    asyncio.run(_generate_pdf(html, output_path))

    size_kb = Path(output_path).stat().st_size // 1024
    print(f"[4/4] Saved: {output_path}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
