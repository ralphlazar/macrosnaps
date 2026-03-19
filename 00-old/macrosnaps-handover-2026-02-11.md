# PROJECT HANDOVER BRIEF: MacroSnaps — Global Economic Dashboard

**Date:** February 11, 2026  
**Live site:** https://macrosnaps-01.onrender.com/macrosnaps-globe.html  
**GitHub repo:** https://github.com/ralphlazar/macrosnaps-01

---

## RALPH'S MACHINE — FILE LOCATIONS

Everything lives inside one folder on Ralph's MacBook Air:

```
/Users/lisaswerling/Downloads/macrosnaps-repo/
```

This folder IS the Git repo. GitHub Desktop cloned it here. Inside it:

```
macrosnaps-repo/
├── .claude/                  ← Claude config (don't touch)
├── .env                      ← Contains FRED_API_KEY (secret, never push)
├── .env.example              ← Template for .env
├── .git/                     ← Git internals (don't touch)
├── .gitignore                ← Tells git which files to ignore
├── backend/
│   ├── build_snapshot.py     ← ⭐ BACKEND — the Python data fetcher (~1,775 lines)
│   └── (other backend files)
├── docs/                     ← Documentation
├── frontend/
│   ├── glossary/             ← Enriched glossary JSON files
│   ├── macrosnaps-globe.html ← ⭐ THE APP — single-file HTML (~9,440 lines)
│   ├── index.html            ← Redirect or landing page
│   └── snapshot.json         ← Generated daily data (overwritten each run)
├── glossary/                 ← Glossary source files
├── CLAUDE.md                 ← Project context for Claude
├── README.md                 ← Repo readme
├── render.yaml               ← Render deployment config
├── requirements.txt          ← Python dependencies
└── snapshot.json             ← Root-level snapshot copy
```

### The two files that matter

| File | Full path on Ralph's machine | What it does |
|---|---|---|
| **The app** | `/Users/lisaswerling/Downloads/macrosnaps-repo/frontend/macrosnaps-globe.html` | The entire frontend — HTML, CSS, JS, embedded data |
| **The backend** | `/Users/lisaswerling/Downloads/macrosnaps-repo/backend/build_snapshot.py` | Fetches live data daily, produces `snapshot.json` |

**When Claude delivers updated files, Ralph saves them to these exact paths, overwriting the old versions.**

---

## HOW TO PUSH CHANGES TO GITHUB (STEP BY STEP)

Ralph uses Terminal (the black window). Every time Claude delivers updated files:

### Step 1: Save the file(s)

Download the file(s) Claude provides and save them into the correct folder(s):

- HTML file → save to `frontend/macrosnaps-globe.html`
- Python file → save to `backend/build_snapshot.py`

**Overwrite the existing files. Don't rename them.**

### Step 2: Open Terminal and run these commands

Copy-paste this entire block into Terminal:

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo
git add frontend/macrosnaps-globe.html backend/build_snapshot.py
git commit -m "Update description here"
git push origin main
```

**Claude will give you the exact commands each time, including the commit message. Just copy-paste.**

### Step 3: Wait ~2 minutes

Render auto-deploys from GitHub. Then hard-refresh the live site:

https://macrosnaps-01.onrender.com/macrosnaps-globe.html

(Hard refresh: Cmd+Shift+R on Mac)

### If only one file changed

Claude will tell you. The `git add` line will only include the file(s) that changed. For example, if only the HTML changed:

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo
git add frontend/macrosnaps-globe.html
git commit -m "Fix commodity card layout"
git push origin main
```

### If git complains

- `"nothing to commit"` → The file wasn't actually saved/changed. Re-save it and try again.
- `"pathspec did not match"` → Wrong file path. Check you saved to the right folder.
- `"rejected"` → Someone else pushed first. Run `git pull` then try pushing again.
- Authentication popup → Follow the prompts (GitHub username + password or token).

---

## ARCHITECTURE

### Frontend

Single-file HTML app (`macrosnaps-globe.html`, ~9,440 lines) with everything inline — CSS, HTML, JS, and all data as embedded JSON blocks. No build system, no frameworks beyond CDN-loaded libs.

External dependencies (loaded from CDN):
- Three.js r128 (3D globe)
- Chart.js 4.4.1 (historical charts in metric tooltips)
- Google Fonts: Space Mono (display/monospace) + DM Sans (body)

### Backend

`build_snapshot.py` — Python script that fetches live data from:
- **FRED API** — macro metrics, rates, bonds, FX (requires `FRED_API_KEY` env var)
- **Yahoo Finance** — stocks, FX, commodity prices + historical data
- **IMF WEO** — budget deficit (requires `imf_reader` package, optional)
- **Google Sheets CSV** — Ralph's 2026 macro forecasts

Outputs `snapshot.json` which the frontend loads on page open.

---

## DATA FLOW

1. `build_snapshot.py` runs daily, produces `snapshot.json`
2. Frontend has hardcoded fallback data in three embedded `<script type="application/json">` blocks:
   - `#countries-data` — 9 countries with metrics, stories, historical data, weather grids, FX regime info
   - `#glossary-data` — full glossary (177 terms) with beginner/moderate/expert definitions, BLUF + full expandable content
   - `#app-config` — global stories, metric sources, chart config, commodities data (prices, stories, historical, per-item explanations), footer content
3. On load, frontend tries `fetch('snapshot.json')` — if found, overwrites hardcoded data in-place (countries AND commodities); if not, silently uses fallbacks

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

## 9 COMMODITIES

WTI Crude, Brent Crude, Natural Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans. Each has:
- **Price + unit** (e.g. $71.24 $/bbl)
- **Day-over-day % change** (green/red/grey)
- **12-month sparkline** (canvas mini-chart)
- **Annual historical data** (2010–2025, ~16 data points, Chart.js line chart in tooltip)
- **Level-aware BLUF + expandable explanation** (beginner/moderate/expert)
- Grouped by category: Energy (#e8a838 amber), Metals (#00d4ff cyan), Agriculture (#00e68a green)

### Data sources for commodities

| Data | Source | API key needed? |
|---|---|---|
| Current price | Yahoo Finance (`yfinance`) via futures tickers: `CL=F`, `BZ=F`, `NG=F`, `GC=F`, `SI=F`, `HG=F`, `ZW=F`, `ZC=F`, `ZS=F` | No |
| Day-over-day change | Computed from last two Yahoo daily closes | No |
| 12-month sparkline | Monthly closes from ~400 days of Yahoo data | No |
| Annual history (2010→now) | Yahoo Finance historical, resampled to annual averages | No |
| Item explanations | Hardcoded in HTML (3 levels × 9 items) — carried forward from snapshot | No |
| Commodity stories | Hardcoded in HTML (3 levels × 3 bullets) — carried forward from snapshot | No |
| Weather icon | Computed from aggregate price changes | No |

### What updates daily vs. what's static

| Field | Updates daily? | How |
|---|---|---|
| Prices, % change, sparklines | ✅ Yes | `build_snapshot.py` fetches from Yahoo Finance |
| Annual historical data | ✅ Yes (unless `--skip-historical`) | `build_snapshot.py` fetches from Yahoo Finance |
| Weather icon | ✅ Yes | Computed from price changes |
| Commodity stories (3 bullets) | ❌ No — static | Carried forward from previous snapshot. To update: edit HTML manually or add to snapshot.json |
| Item explanations (BLUF + full) | ❌ No — static | Same as stories — hardcoded, carried forward |
| Glossary terms | ❌ No — static | Embedded in HTML `#glossary-data` block |

**Note:** Country stories are also static (same pattern). If you want AI-generated daily stories for either countries or commodities, that would require adding a Claude API call to `build_snapshot.py` — a future enhancement.

---

## THREE EXPERTISE LEVELS

`beginner` / `moderate` / `expert` — toggled via top bar buttons or inline toggle in any open card/tooltip. Changing level refreshes the current view. Affects: story bullets, glossary definitions, news stories, commodities stories, commodity item explanations, FX regime descriptions, metric explanations.

---

## GLOBE (Three.js)

- Wireframe sphere with solid inner core and atmosphere glow
- Lat/lon grid lines
- Cyan pulsing dots at each country's coordinates
- Amber pulsing dots at North Pole (lat 90) and South Pole (lat -90) for commodities
- Invisible larger hit-target spheres for click/tap detection (raycasting)
- Floating country labels (`<div class="country-label">`) projected from 3D→2D each animation frame, hidden when dot faces away (`p.z < 0.15`)
- Floating pole labels (`<div class="pole-label">🛢️ COMM</div>`) for commodity dots
- Drag to rotate (mouse + touch), scroll/pinch to zoom, click/tap for card
- Labels are recreated every frame (removed and re-added to DOM)

---

## INTERACTION FLOW

- Click country dot/label → `showCard(co)` → full card-overlay with weather, stories, macro section, market section
- **◀▶ arrows in card-head row** → cycle through countries alphabetically + commodities at end (wraps around)
- Click a metric row in country card → `showMTT()` → metric tooltip with value, BLUF explanation, expandable full explanation, historical chart, source, nav arrows
- Metric tooltip has compare button → cross-country comparison view
- Metric tooltip has weather grid button → heat map table across all 9 countries
- Click news icon (🔥/⚡/💡) → `showNewsTooltip(idx)` → centered tooltip with global story
- Click pole dot/label (🛢️) → `showCommoditiesCard()` → commodities card overlay with weather, 3 story bullets, clickable commodity items
- Click a commodity item in commodities card → `showCommodityMTT(idx)` → commodity tooltip with price, chart, BLUF explanation, expandable full, nav arrows
- Glossary terms are `<span class="glossary-term" data-term="...">` — clicking opens a positioned bubble with level-aware definition
- `closeAll()` clears everything (cards, tooltips, bubbles, charts)

---

## COMMODITIES CARD (redesigned Feb 11, 2026)

Now mirrors the country card pattern:

- **Card head:** 🛢️ emoji + "Commodities" title + ◀▶ nav arrows
- **Weather section:** Weather emoji + 3 story bullets (level-aware, like country cards)
- **Category section headers:** styled like MACRO/MARKETS headers, each in category colour (Energy amber, Metals cyan, Agriculture green)
- **Clickable commodity items:** 2-column grid, each item shows name, ticker, price, % change, sparkline
- Click any item → opens **commodity metric tooltip** (`showCommodityMTT`)
- Level toggle refreshes in place, glossary active, click backdrop to dismiss

### Commodity Metric Tooltip

- Name, ticker, category, price, unit, % change
- **Chart.js historical chart** (annual prices 2010→now)
- **Level-aware BLUF** + expandable "Read more" explanation
- **▲/▼ nav arrows** to cycle through all 9 commodities
- Source footer

---

## GLOSSARY

177 terms across categories: macro, credit, equity, fx, trade, institutions, **commodities**.

Commodity-specific glossary terms (added Feb 11, 2026):
- Backwardation
- Contango
- Spot Price
- Futures
- OPEC
- Safe-haven
- Convenience Yield
- Crack Spread

Each has beginner/moderate/expert definitions. These are embedded in the HTML `#glossary-data` JSON block — no backend fetching needed. They're clickable anywhere glossary terms appear (stories, explanations, tooltips).

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
| `getCardOrder()` | Returns countries sorted A→Z + commodities sentinel at end |
| `cardNavHTML()` / `attachCardNav(container, id)` | ◀▶ arrow buttons + click handlers for card-to-card cycling |
| `showCommoditiesCard()` | Commodities card overlay (weather + stories + clickable items) |
| `showCommodityMTT(idx)` | Individual commodity tooltip with chart + explanation |
| `renderCommodityChart(container, item)` | Chart.js annual price chart for a commodity |
| `showMTT()` / `renderMTT(d)` | Country metric tooltip |
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
# 1. Generate fresh data (run from repo root)
cd /Users/lisaswerling/Downloads/macrosnaps-repo
FRED_API_KEY=xxx python backend/build_snapshot.py

# 2. Copy snapshot to frontend folder (so Render can serve it)
cp snapshot.json frontend/snapshot.json

# 3. Push to GitHub so Render deploys
git add frontend/snapshot.json snapshot.json
git commit -m "Daily snapshot update"
git push origin main
```

### build_snapshot.py details

- Requires `FRED_API_KEY` env var (stored in `.env` file)
- Dependencies: `requests`, `yfinance`, optionally `imf_reader` for budget deficit
- Fetches from: FRED (macro + rates + bonds + FX), Yahoo Finance (stocks, FX, **commodity prices + history**), Google Sheets CSV (Ralph's 2026 forecasts), IMF WEO (budget deficit)
- `--skip-historical` flag carries forward historical data from previous snapshot (faster, less API calls)
- `--output` flag for custom output path
- Atomic write (tmp file then rename)
- Never fails completely — falls back to hardcoded values per metric

### What build_snapshot.py now outputs

```json
{
  "generated_at": "2026-02-11T10:00:00Z",
  "data_freshness": { ... },
  "fetch_summary": { ... },
  "countries": {
    "USA": { "metrics": {...}, "weather": "☀️", "stories": {...}, ... },
    "CAN": { ... },
    ...
  },
  "commodities": {
    "asOf": "Feb 11, 2026",
    "source": "CME · ICE · COMEX · CBOT · Yahoo Finance",
    "weather": "☁️",
    "items": [
      { "name": "WTI Crude", "symbol": "CL", "cat": "energy", "unit": "$/bbl",
        "price": 71.24, "change": -1.8,
        "spark": [68, 70, 73, ...],
        "annual": [79.61, 94.88, ...] }
    ],
    "stories": { "beginner": [...], "moderate": [...], "expert": [...] },
    "itemExplanations": { "WTI Crude": { "beginner": {...}, ... }, ... }
  }
}
```

### Frontend snapshot loader

When `snapshot.json` is found, the frontend merges:
- Country metrics, weather, stories, fxRegime, historical data, weather grids
- Global stories
- **Commodity items** (prices, sparklines, annual history), weather, stories, item explanations

If any field is missing from the snapshot, the hardcoded HTML fallback is used silently.

---

## DEPLOYMENT

- **Hosting:** Render (static site) at `https://macrosnaps-01.onrender.com/`
- **Source:** linked to GitHub repo `ralphlazar/macrosnaps-01` — any push triggers auto-deploy (~2 minutes)
- **Verify changes:** hard-refresh `https://macrosnaps-01.onrender.com/macrosnaps-globe.html` after push

### What lives where

| Location | What | Updates how |
|---|---|---|
| Ralph's machine (`/Users/lisaswerling/Downloads/macrosnaps-repo/`) | Working copies of all files | Edited locally, pushed to GitHub |
| GitHub repo (`ralphlazar/macrosnaps-01`) | `frontend/macrosnaps-globe.html`, `backend/build_snapshot.py`, etc. | Ralph pushes via Terminal (or GitHub Desktop) |
| Render | Serves the HTML + any `snapshot.json` | Auto-deploys from GitHub on push |
| `snapshot.json` | Daily data output | Generated by `build_snapshot.py` each morning |

---

## ⚠️ CHANGE PROTOCOL — MUST READ FOR EVERY UPDATE

**Ralph is a beginner with git/backend. Every time Claude makes changes, Claude MUST:**

1. **State clearly** which files changed: HTML only? Python only? Both?
2. **State clearly** which files need to go to GitHub (i.e. be pushed via Terminal)
3. **Give Ralph the exact Terminal commands** to push — copy-paste ready, starting with `cd /Users/lisaswerling/Downloads/macrosnaps-repo`
4. **Flag any risk** that tomorrow's `build_snapshot.py` run could conflict with today's changes — e.g. if a new data field was added to the HTML that the backend doesn't yet produce, or vice versa
5. **Ensure consistency** — if both files change, both must be delivered together so Ralph can push them as a pair. Never leave the frontend expecting data the backend doesn't produce, or the backend producing data the frontend ignores.
6. **Only test on the live site** — never reference `file:///Users/lisaswerling/Downloads/macrosnaps-globe.html` or any local file. All testing happens at `https://macrosnaps-01.onrender.com/macrosnaps-globe.html`

**The golden rule:** Today's delivered changes are the source of truth. Tomorrow's bash ritual must work seamlessly with them. If it won't, Claude must fix the backend too and say so explicitly.

**Checklist Claude gives Ralph after every update:**
- [ ] Files to save locally: (list, with exact folder paths)
- [ ] Terminal commands to push: (copy-paste block)
- [ ] Backend (`build_snapshot.py`) changed? Yes/No
- [ ] Tomorrow's bash ritual will work as-is? Yes/No (if No, explain)

**Example push instructions Claude gives Ralph:**

> Save the updated HTML file to: `frontend/macrosnaps-globe.html`
> 
> Then copy-paste this into Terminal:
> ```bash
> cd /Users/lisaswerling/Downloads/macrosnaps-repo
> git add frontend/macrosnaps-globe.html
> git commit -m "Fix commodity sparkline colours"
> git push origin main
> ```
> Wait 2 minutes, then hard-refresh the live site.

---

## CHANGELOG

| Date | Change | Files touched | Backend change? |
|---|---|---|---|
| Feb 11, 2026 | Added ◀▶ card-to-card nav arrows in card-head row — cycles countries alphabetically + commodities at end | `frontend/macrosnaps-globe.html` | No |
| Feb 11, 2026 | Commodities card redesign: weather + 3 story bullets + clickable items → per-commodity tooltips with Chart.js annual price charts + level-aware explanations + ▲/▼ nav. 8 new commodity glossary terms (backwardation, contango, etc.). Backend: commodity price fetcher via Yahoo Finance (prices, sparklines, annual history). Frontend: snapshot loader merges commodity data from snapshot.json. | `frontend/macrosnaps-globe.html`, `backend/build_snapshot.py` | Yes |

---

## FILES

| File | Path in repo | Status |
|---|---|---|
| `macrosnaps-globe.html` | `frontend/macrosnaps-globe.html` | The app (single file, ~9,440 lines) — **keep** |
| `build_snapshot.py` | `backend/build_snapshot.py` | Backend data fetcher (~1,775 lines) — **keep** |
| `snapshot.json` | `frontend/snapshot.json` + root `snapshot.json` | Generated daily output — **regenerated each run** |
| `add_commodities_card.sh` | root | One-time patch script — **can delete, already applied** |
| `push.sh` | root | One-time push script — **can delete, already used** |
| `render.yaml` | root | Render deployment config — **keep** |
| `.env` | root | Contains `FRED_API_KEY` — **keep, never push to GitHub** |
| `requirements.txt` | root | Python dependencies — **keep** |
