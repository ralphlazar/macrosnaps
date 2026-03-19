# PROJECT HANDOVER BRIEF: MacroSnaps — Global Economic Dashboard

---

## ARCHITECTURE

Single-file HTML app (`macrosnaps-globe.html`, ~8,950 lines) with everything inline — CSS, HTML, JS, and all data as embedded JSON blocks. No build system, no frameworks beyond CDN-loaded libs.

External dependencies (loaded from CDN):
- Three.js r128 (3D globe)
- Chart.js 4.4.1 (historical charts in metric tooltips)
- Google Fonts: Space Mono (display/monospace) + DM Sans (body)

Backend: `build_snapshot.py` — Python script that fetches live data from FRED API + Yahoo Finance + IMF WEO + a Google Sheets CSV (Ralph's forecasts), computes derived metrics, assigns weather status, and outputs `snapshot.json`.

---

## DATA FLOW

1. `build_snapshot.py` runs daily, produces `snapshot.json`
2. Frontend has hardcoded fallback data in three embedded `<script type="application/json">` blocks:
   - `#countries-data` — 9 countries with metrics, stories, historical data, weather grids, FX regime info
   - `#glossary-data` — full glossary with beginner/moderate/expert definitions, BLUF + full expandable content
   - `#app-config` — global stories, metric sources, chart config, commodities data, footer content
3. On load, frontend tries `fetch('snapshot.json')` — if found, overwrites hardcoded data in-place; if not, silently uses fallbacks

---

## 9 COUNTRIES

USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND. Each has:
- **Macro metrics (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate
- **Market metrics (8):** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, FX pair, FX Vol
- Weather emoji (☀️/☁️/⛈️) with sunny/cloudy/stormy CSS filters
- Story bullets per expertise level
- Historical data (annual + monthly) powering Chart.js sparklines in metric tooltips
- Weather grid data (2020–2026F) for cross-country comparison tables
- FX regime descriptions per level

---

## THREE EXPERTISE LEVELS

`beginner` / `moderate` / `expert` — toggled via top bar buttons or inline toggle in any open card/tooltip. Changing level refreshes the current view. Affects: story bullets, glossary definitions, news stories, commodities commentary, FX regime descriptions, metric explanations.

---

## GLOBE (Three.js)

- Wireframe sphere with solid inner core and atmosphere glow
- Lat/lon grid lines
- Cyan pulsing dots at each country's coordinates
- Invisible larger hit-target spheres for click/tap detection (raycasting)
- Floating country labels (`<div class="country-label">`) projected from 3D→2D each animation frame, hidden when dot faces away (`p.z < 0.15`)
- Drag to rotate (mouse + touch), scroll/pinch to zoom, click/tap for card
- Labels are recreated every frame (removed and re-added to DOM)

---

## INTERACTION FLOW

- Click country dot/label → `showCard(co)` → full card-overlay with weather, stories, macro section, market section
- Click a metric row in card → `showMTT()` → metric tooltip with value, BLUF explanation, expandable full explanation, historical chart, source, nav arrows
- Metric tooltip has compare button → cross-country comparison view
- Metric tooltip has weather grid button → heat map table across all 9 countries
- Click news icon (🔥/⚡/💡) → `showNewsTooltip(idx)` → centered tooltip with global story
- Click pole dot/label (🛢️) → `showCommoditiesCard()` → commodities card overlay
- Glossary terms are `<span class="glossary-term" data-term="...">` — clicking opens a positioned bubble with level-aware definition
- `closeAll()` clears everything (cards, tooltips, bubbles, charts)

---

## COMMODITIES CARD (newly built)

Triggered by amber (`#e8a838`) pulsing dots placed at North Pole (lat 90) and South Pole (lat -90) on the globe. Uses the exact same pattern as country dots:

- **Visible dot:** `SphereGeometry(.018)`, amber material
- **Pulse ring:** `RingGeometry(.022, .035)`, amber, transparent, `userData={pulse:true}`
- **Hit target:** `SphereGeometry(.07)`, invisible, `userData={commodity:true, lat:lat}`
- **Floating label:** `<div class="pole-label">🛢️ COMM</div>`, amber border/text, appears when pole faces camera

Click handling added in three places:
- **Mouse click handler:** checks `.pole-label` first, then country labels, then raycasts (checks `userData.commodity` before `userData.code`)
- **Touch tap handler:** same priority — pole label, country label, raycast
- **Pole labels themselves** have `click` event listeners with `stopPropagation`

`showCommoditiesCard()` creates a `card-overlay` div (same as `renderCard`) containing:
- Card head: 🛢️ emoji + "Commodities" title
- Level-aware commentary paragraph (`.comm-commentary`)
- Amber-styled section header "PRICES"
- 2-column CSS grid (`.comm-grid`) with category section labels spanning full width
- 9 commodity items, each with: name, ticker symbol, price + unit, % change (green/red/grey), canvas sparkline
- Sparklines drawn via `drawSparkline()` — gradient fill + line + end dot, using `requestAnimationFrame` after DOM insert
- Source/date footer
- Level toggle refreshes in place, glossary active, click backdrop to dismiss

**Category colors:** energy = `#e8a838`, metals = `#00d4ff`, agriculture = `#00e68a`

**Data location:** `_appConfig.commodities` in the `#app-config` JSON block. Structure:

```json
{
  "asOf": "Feb 11, 2026",
  "source": "CME · ICE · COMEX · CBOT · Yahoo Finance",
  "items": [
    {
      "name": "WTI Crude",
      "symbol": "CL",
      "cat": "energy",
      "unit": "$/bbl",
      "price": 71.24,
      "change": -1.8,
      "spark": [68, 70, 73, 76, 74, 72, 69, 71, 74, 73, 72, 71]
    }
  ],
  "commentary": {
    "beginner": "...",
    "moderate": "...",
    "expert": "..."
  }
}
```

Currently hardcoded — ready for `build_snapshot.py` to populate with live Yahoo Finance commodity prices.

---

## CSS VARIABLES

```css
--cyan: #00d4ff;    /* primary accent, globe, country dots, section heads */
--hot: #ff3d5a;     /* Today's Story, negative values */
--gold: #ffd700;    /* Biggest Movers */
--green: #00e68a;   /* positive values, agriculture */
--font-display: 'Space Mono', monospace;
--font-body: 'DM Sans', sans-serif;
```

Commodities amber: `#e8a838` (not a CSS variable, used directly)

---

## RESPONSIVE BREAKPOINTS

- `@media(max-width:768px)` — mobile: smaller fonts, full-width cards, touch-optimized hit targets
- `@media(max-width:380px)` — iPhone SE: further size reductions

---

## KEY JS FUNCTIONS

| Function | Purpose |
|---|---|
| `initGlobe()` | Creates Three.js scene, dots, labels, handles drag/zoom/click |
| `ll(lat, lon, r)` | Converts lat/lon to Three.js Vector3 |
| `showCard(co)` / `renderCard(d, co)` | Country card overlay |
| `showCommoditiesCard()` | Commodities card overlay |
| `showMTT()` / `renderMTT(d)` | Metric tooltip |
| `showNewsTooltip(idx)` / `renderNews(d)` | News story tooltip |
| `drawSparkline(canvas, data, color)` | Canvas sparkline renderer |
| `applyGlossary(html)` | Wraps glossary terms in clickable spans |
| `attachGlossary(container)` | Binds click handlers on glossary terms |
| `levelToggleHTML()` / `attachLevelToggle(container, refreshFn)` | Expertise toggle |
| `setLevel(lv)` | Updates `currentLevel` and top bar buttons |
| `closeAll()` | Removes all overlays, tooltips, bubbles, destroys active chart |

---

## DAILY BASH RITUAL

```bash
# 1. Generate fresh data
FRED_API_KEY=xxx python backend/build_snapshot.py

# 2. Serve locally
cd ~/Downloads   # or wherever macrosnaps-globe.html lives
python3 -m http.server 8000

# 3. Open in browser
# http://localhost:8000/macrosnaps-globe.html
```

The frontend auto-fetches `snapshot.json` from the same directory. If the JSON file is present alongside the HTML, live data appears; if not, hardcoded fallbacks are used.

### build_snapshot.py details

- Requires `FRED_API_KEY` env var
- Dependencies: `requests`, `yfinance`, optionally `imf_reader` for budget deficit
- Fetches from: FRED (macro + rates + bonds + FX), Yahoo Finance (stocks, FX where FRED gaps), Google Sheets CSV (Ralph's 2026 forecasts), IMF WEO (budget deficit)
- `--skip-historical` flag carries forward historical data from previous snapshot
- `--output` flag for custom output path
- Atomic write (tmp file then rename)
- Never fails completely — falls back to hardcoded values per metric

---

## FILES

| File | Status |
|---|---|
| `macrosnaps-globe.html` | The app (single file, ~8,950 lines) — **keep** |
| `build_snapshot.py` | Backend data fetcher (~1,585 lines) — **keep** |
| `snapshot.json` | Generated daily output — **regenerated each run** |
| `add_commodities_card.sh` | One-time patch script — **can delete, already applied** |
| `macrosnaps-globe.html.bak` | Old backup — **can delete** |
| `macrosnaps-globe-final.html` | Intermediate file — **can delete** |
