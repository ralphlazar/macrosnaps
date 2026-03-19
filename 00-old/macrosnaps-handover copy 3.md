# MacroSnaps — Comprehensive Handover Brief

**Date:** February 12, 2026
**Live URL:** https://macrosnaps-01.onrender.com/macrosnaps-globe.html
**Repo (local):** `/Users/lisaswerling/Downloads/macrosnaps-repo/`
**Hosting:** Render (static site, auto-deploys from `main` branch)


---

## 1. PROJECT OVERVIEW

MacroSnaps is an interactive global economic dashboard. A 3D globe (Three.js) displays pulsing dots for 10 countries and 2 commodity poles. Users click a dot → a "card" slides in showing macro metrics, market metrics, stories at 3 expertise levels (beginner/moderate/expert), and a glossary that highlights economic terms with popover definitions.

**Current scope:**
- 10 countries: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF
- 9 commodities: WTI Crude, Brent Crude, Natural Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans
- 180 glossary terms across 7 categories (macro, equity, credit, fx, institutions, commodities, trade)
- 3 expertise levels throughout (beginner → moderate → expert)
- Weather emoji system: ☀️ ⛅ ☁️ ⛈️ based on economic health


---

## 2. FILE ARCHITECTURE

```
macrosnaps-repo/
├── frontend/
│   ├── macrosnaps-globe.html    ← THE monolith (~13,300 lines). All CSS, HTML, JS, data.
│   └── snapshot.json            ← Daily data output from backend
├── backend/
│   └── build_snapshot.py        ← Data fetcher (~1,800 lines). Runs daily.
├── .env                         ← FRED_API_KEY=xxx (not committed)
├── snapshot.json                ← Copy at repo root (backend writes here first)
└── .gitignore
```

### The Monolith: `macrosnaps-globe.html`

Everything lives in one file. No external CSS/JS except Three.js and Chart.js CDN imports.

**Internal structure (top to bottom):**

| Lines (approx) | Section |
|---|---|
| 1–700 | `<style>` — All CSS including mobile breakpoints |
| 700–3,400 | `<script id="countries-data">` — JSON block with all 10 countries' metrics, stories, fxRegime, historical data, weatherGrid |
| 3,400–7,200 | `<script id="glossary-data">` — 180 terms, each with 3 expertise levels |
| 7,200–7,700 | `<script id="app-config">` — Commodity items, global stories, commodity stories |
| 7,700–7,800 | JS: Data bootstrap — parses JSON blocks into `countries`, `glossary`, `cardStories` arrays |
| 7,800–8,100 | JS: Globe initialization (Three.js) — wireframe, dots, hit targets, drag/touch controls |
| 8,100–8,300 | JS: Labels overlay — country labels positioned via 3D→2D projection |
| 8,300–9,300 | JS: Card rendering, tooltips, metric popovers, glossary highlighting, comparison tables |

### The Backend: `build_snapshot.py`

**Internal structure:**

| Lines (approx) | Section |
|---|---|
| 1–45 | Imports, logging, FRED API setup |
| 46–270 | `COUNTRY_CONFIG` — 10 countries, each with FRED series IDs, Yahoo symbols, FX config |
| 270–310 | `FALLBACK` — Hardcoded values for metrics with no free API (corp spread, sov CDS, yield curve, plus FRED data gaps) |
| 310–330 | `COMMODITY_CONFIG` — 9 commodities with Yahoo symbols + fallback prices |
| 330–370 | Google Sheets integration — fetches Ralph's forecast spreadsheet |
| 370–590 | Fetch functions: `fetch_fred()`, `fetch_yahoo()`, `fetch_weo_budget()`, `fetch_forecasts()` |
| 590–665 | Computation: `compute_yoy_inflation()`, `compute_ytd_return()`, `compute_realized_vol()`, `compute_yield_curve()` |
| 665–715 | Formatting: `fmt_pct_signed()`, `fmt_rate()`, `fmt_bps()`, `fmt_fx()` etc. |
| 715–940 | Weather assignment: GDP > 2% + low inflation + low unemployment → ☀️ ... → ⛈️ |
| 940–1,140 | Historical data builders: fetch 2010→now from FRED, resample monthly/annually |
| 1,140–1,480 | `build_country()` — assembles one country's full data object |
| 1,480–1,620 | `build_commodities()` — fetches 9 commodity prices from Yahoo |
| 1,620–1,800 | `build_snapshot()` — main entry, loops all countries, writes JSON |


---

## 3. DATA FLOW

```
                   ┌────────────────────┐
                   │  Ralph's Google     │
                   │  Sheet (forecasts)  │
                   └────────┬───────────┘
                            │ CSV fetch
                            ▼
┌──────────┐    ┌──────────────────────┐    ┌────────────┐
│ FRED API │───▶│  build_snapshot.py   │◀───│ Yahoo Fin  │
│ (macro)  │    │                      │    │ (markets)  │
└──────────┘    │  Merges all sources  │    └────────────┘
                │  Applies fallbacks   │
                │  Assigns weather     │
                │  Computes derived    │
                └────────┬─────────────┘
                         │
                         ▼
                   snapshot.json
                         │
                         │ git push
                         ▼
            ┌─────────────────────────┐
            │   macrosnaps-globe.html │
            │   (reads snapshot.json  │
            │    at load time)        │
            └─────────────────────────┘
```

**Key distinction: TWO data sources feed the frontend.**

1. **snapshot.json** — Live numeric data refreshed daily by `build_snapshot.py`. Contains current metric values, commodity prices, weather emojis, and historical time series. The HTML loads this at runtime via a `<script>` tag or fetch.

2. **Inline JSON in HTML** — Stories, glossary terms, fxRegime descriptions, and the initial/fallback metric values are embedded directly in the HTML file as `<script type="application/json">` blocks. These are **static** and only change when you edit the HTML manually (or via a script like we did today).

**What the daily bash ritual refreshes:**
- ✅ Metric values (GDP, inflation, unemployment, etc.)
- ✅ Market data (stock YTD, bond yields, FX rates, vol)
- ✅ Commodity prices and % changes
- ✅ Weather emojis (recomputed from live data)
- ✅ Macro forecasts (from Ralph's Google Sheet)
- ❌ Stories (static in HTML — must be manually updated)
- ❌ Glossary terms (static in HTML)
- ❌ fxRegime descriptions (static in HTML)


---

## 4. DAILY BASH RITUAL

Run this every trading day (or whenever you want fresh data):

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo

# 1. Fetch fresh data from FRED + Yahoo + Google Sheets
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# 2. Copy snapshot to frontend directory
cp snapshot.json frontend/snapshot.json

# 3. Push to GitHub → auto-deploys to Render
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main
```

**Runtime:** ~5 minutes (FRED rate-limits at 0.2s between calls × ~70 series + Yahoo fetches)

**Expected output:**
```
Metrics: 140 total | 100+ live | 30-ish fallback | 0 missing
  🇺🇸 USA: ☀️  14/14 metrics live
  🇨🇦 CAN: ☁️  14/14 metrics live
  ... (10 countries)
  🛢️ COMM: ☁️  9/9 commodities live
```

**Fallback metrics** (no free API available — use hardcoded estimates):
- Corp spread: all 10 countries
- Sov CDS: all 10 countries
- Yield curve: 8 countries (USA computed live from DGS10-DGS2)
- Japan inflation, China GDP/unemployment/10Y, India unemployment/10Y


---

## 5. STORY UPDATES (MANUAL PROCESS)

Stories are NOT auto-generated. They're static text embedded in the HTML's JSON blocks. To update:

1. Research current economic news for each country
2. Write 3 bullets × 3 expertise levels per country (beginner, moderate, expert)
3. Write global stories (3 items × 3 levels) and commodity stories (3 items × 3 levels)
4. Either: manually edit the HTML, or create a Python script to patch all story blocks

**Story locations in the HTML:**
- Country stories: inside `<script id="countries-data">` → each country → `"stories"` key
- Global stories: inside `<script id="app-config">` → `"globalStories"` key
- Commodity stories: inside `<script id="app-config">` → `"commodities"` → `"stories"` key

**Total stories to update:** 9 items (3 global + 3 per-country × 10 + 3 commodity) × 3 levels = ~39 story sets, 117 individual bullets.


---

## 6. DEPLOYMENT PIPELINE

```
Local Mac                       GitHub                    Render
──────────                     ────────                  ──────
Edit files                     origin/main               Static site
    │                              │                         │
    ├── git add                    │                         │
    ├── git commit                 │                         │
    ├── git push ─────────────────▶│                         │
    │                              ├── webhook ─────────────▶│
    │                              │                         ├── git pull
    │                              │                         ├── serve frontend/
    │                              │                         └── live in ~2 min
```

**Render config:**
- Serves the `frontend/` directory as a static site
- Auto-deploys on every push to `main`
- Takes ~2 minutes to go live after push
- **Cache busting:** Use Cmd+Shift+R or incognito window (Cmd+Shift+N) to see changes immediately

**The .env file is NOT pushed to GitHub.** The `FRED_API_KEY` lives only on your Mac in `/Users/lisaswerling/Downloads/macrosnaps-repo/.env`.


---

## 7. GOOGLE SHEETS INTEGRATION (RALPH'S FORECASTS)

Ralph maintains a published Google Sheet with macro forecasts.

**Sheet URL (published CSV):**
```
https://docs.google.com/spreadsheets/d/e/2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj/pub?gid=0&single=true&output=csv
```

**Current columns:**
| Country | GDP_Growth_2026 | Inflation_2026 | Budget_Deficit_2026 | Current_Account_2026 | Unemployment_2026 |
|---|---|---|---|---|---|
| USA | 2.1 | 2.3 | -7.5 | -3.8 | 4.2 |
| ZAF | 1.6 | 3.5 | -4.8 | -1.4 | 32.5 |
| ... | ... | ... | ... | ... | ... |

**How it works:**
- `build_snapshot.py` fetches this CSV on every run
- Forecast values override the FRED-derived macro numbers when present
- Policy Rate always comes from FRED (not in the sheet)
- The sheet is the "absolute truth" for macro forecasts
- If the sheet fetch fails, the script continues with FRED data only

**To add a new country:** Ralph adds a row with the country code (e.g., "BRA") and the script picks it up automatically — but only if the code exists in `COUNTRY_CONFIG`.


---

## 8. COUNTRY DATA SCHEMA

Each country in the `countries-data` JSON block has this structure:

```json
{
  "ZAF": {
    "code": "ZAF",
    "name": "South Africa",
    "flag": "🇿🇦",
    "lat": -29.0,
    "lon": 24.0,
    "weather": "⛈️",
    "metrics": {
      "macro": {
        "GDP Growth": "+1.6%",
        "Inflation (CPI)": "3.5%",
        "Unemployment": "32.5%",
        "Budget Deficit": "-4.8% GDP",
        "Current Account": "-1.4% GDP",
        "Policy Rate": "7.50%"
      },
      "market": {
        "Stock Market YTD": "+5.2%",
        "Equity Vol": "~18",
        "10Y Bond Yield": "9.85%",
        "Yield Curve": "+85bps",
        "Corp Spread": "180bps",
        "Sov CDS": "195bps",
        "USD/ZAR": "17.8",
        "FX Vol": "15.2%"
      }
    },
    "stories": {
      "beginner": ["bullet 1", "bullet 2", "bullet 3"],
      "moderate": ["bullet 1", "bullet 2", "bullet 3"],
      "expert": ["bullet 1", "bullet 2", "bullet 3"]
    },
    "fxRegime": {
      "label": "Free Float",
      "beginner": "...",
      "moderate": "...",
      "expert": "..."
    },
    "historical": {
      "GDP Growth": {"v": [...], "annual": true, "type": "bar"},
      "Inflation (CPI)": {"v": [...], "annual": true, "type": "line"},
      ...
    },
    "weatherGrid": {
      "gdp": {"flag": "🇿🇦", "values": [-6.0, 4.7, 1.9, 0.7, 1.3, 0.8, 1.6]},
      "cpi": {"flag": "🇿🇦", "values": [3.3, 4.6, 6.9, 6.0, 4.4, 3.2, 3.5]},
      "unemp": {"flag": "🇿🇦", "values": [...]},
      "budget": {"flag": "🇿🇦", "values": [...]},
      "ca": {"flag": "🇿🇦", "values": [...]}
    }
  }
}
```

**weatherGrid values** = 7 years: [2020, 2021, 2022, 2023, 2024, 2025, 2026F]


---

## 9. BACKEND COUNTRY CONFIG SCHEMA

Each country in `COUNTRY_CONFIG` (build_snapshot.py):

```python
"ZAF": {
    "name": "South Africa",
    "flag": "🇿🇦",
    "lat": -29.0,         # Globe dot latitude
    "lon": 24.0,          # Globe dot longitude
    "fx_key": "USD/ZAR",  # Label shown on card
    "stock_symbol": "^J203.JO",  # Yahoo Finance ticker for stock index
    "fx_yahoo": "USDZAR=X",     # Yahoo Finance ticker for FX pair
    "fred": {
        "gdp_growth":     "NAEXKP01ZAQ657S",    # OECD quarterly GDP growth
        "inflation":      "ZAFCPIALLMINMEI",     # CPI index (YoY computed)
        "unemployment":   "LRHUTTTTZAM156S",     # Harmonised unemployment
        "policy_rate":    "IRSTCI01ZAM156N",     # Short-term interest rate
        "bond_yield_10y": "IRLTLT01ZAM156N",     # 10-year government bond
        "currency":       "DEXSFUS",             # ZAR per USD (daily)
        "current_account": "ZAFB6BLTT02STSAQ",   # Current account % GDP
    },
    "inflation_is_yoy": False,  # False = CPI index, script computes YoY
    "rate_is_range": False,     # True only for USA (Fed target range)
    "fx_invert": False,         # True = flip the FRED rate (e.g., CAD)
    "fx_decimals": 1,           # Decimal places for FX display
}
```

**FRED series naming conventions:**
- `NAEXKP01xxQ657S` — OECD GDP growth (xx = 2-letter country code)
- `xxCPIALLMINMEI` — CPI All Items (xx = 3-letter ISO code)
- `LRHUTTTTxxM156S` — Harmonised unemployment rate
- `IRSTCI01xxM156N` — Short-term interest rate
- `IRLTLT01xxM156N` — Long-term government bond yield (10Y)
- `DEXxxUS` — Exchange rate (local currency per USD)
- `xxB6BLTT02STSAQ` — Current account balance (% GDP)

**FALLBACK dict:** Metrics with no free API get hardcoded estimates. These are used when FRED/Yahoo returns nothing:
```python
"corp_spread": {"ZAF": 180},   # basis points
"sov_cds":     {"ZAF": 195},   # basis points
"yield_curve": {"ZAF": 85},    # basis points (10Y - 2Y)
```


---

## 10. HOW THE GLOBE WORKS (THREE.JS)

The globe auto-discovers countries from the data. In `initGlobe()`:

```javascript
// Countries — loops over the countries array
countries.forEach(co => {
    const pos = ll(co.lat, co.lon, 1.005);
    // Creates: visible dot, pulse ring, invisible hit target
    // hit.userData = co  ← links dot to country data
});

// Commodities — hardcoded North + South pole
[90, -90].forEach(lat => { ... });
```

**When you add a country to countries-data JSON, it automatically:**
- ✅ Gets a cyan dot at (lat, lon)
- ✅ Gets a pulsing ring
- ✅ Gets a floating label
- ✅ Gets a clickable hit target
- ✅ Gets included in ◀▶ card navigation (alphabetical by code)
- ✅ Gets included in comparison/weather grid tables

**No manual globe code changes needed.** The only thing not auto-generated is the card content (stories, fxRegime, historical), which must be provided in the JSON.


---

## 11. WHAT WE DID TO ADD SOUTH AFRICA (ZAF)

### Step 1: Research FRED Series
Searched FRED for South Africa economic data. Confirmed these series exist:
- GDP Growth: `NAEXKP01ZAQ657S` (OECD quarterly)
- CPI: `ZAFCPIALLMINMEI` (monthly index)
- Unemployment: `LRHUTTTTZAM156S` (monthly rate — ~32.5%)
- Policy Rate: `IRSTCI01ZAM156N` (SARB repo rate)
- 10Y Bond: `IRLTLT01ZAM156N` (government bond yield)
- FX: `DEXSFUS` (daily ZAR per USD)
- Current Account: `ZAFB6BLTT02STSAQ` (% GDP, quarterly)

Yahoo Finance tickers: `^J203.JO` (JSE All Share), `USDZAR=X` (FX pair)

### Step 2: Backend — build_snapshot.py (3 edits)
1. **Added ZAF to COUNTRY_CONFIG** — full config with all FRED series IDs, Yahoo symbols, lat/lon (-29.0, 24.0), fx_key "USD/ZAR"
2. **Added ZAF to FALLBACK** — corp_spread (180bps), sov_cds (195bps), yield_curve (85bps)
3. **Updated description** — "9 countries" → "10 countries"

### Step 3: Frontend — macrosnaps-globe.html (via Python script)
1. **Parsed the countries-data JSON block** using regex + json.loads()
2. **Added complete ZAF object** with:
   - 6 macro metrics + 8 market metrics (initial values)
   - 3×3 stories (beginner/moderate/expert) covering: 32.5% unemployment, SARB easing cycle, load-shedding, fiscal sustainability, ZAR carry trade
   - fxRegime descriptions at 3 levels (free float, SARB non-intervention, reserve adequacy)
   - historical data arrays (2020–2026F) for 6 key metrics
   - weatherGrid data (2020–2026F) for cross-country comparison tables
3. **Re-serialized** the full JSON and replaced the block in HTML
4. **Added 3 glossary terms:** SARB, JSE, load-shedding

### Step 4: Ralph's Sheet
Confirmed Ralph already added ZAF row with forecasts:
- GDP 1.6%, Inflation 3.5%, Unemployment 32.5%, Budget -4.8%, CA -1.4%

### Step 5: Deploy
```bash
git add frontend/macrosnaps-globe.html backend/build_snapshot.py
git commit -m "Add South Africa (ZAF) — 10th country"
git push origin main
# Then ran data refresh:
FRED_API_KEY=... python3 backend/build_snapshot.py
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily snapshot with ZAF live data"
git push origin main
```


---

## 12. ROADMAP: ADDING BRAZIL (BRA)

Exact same pattern as ZAF. Here's the plan:

### Pre-requisite: Ralph's Sheet
Ralph needs to add a BRA row with forecasts:
| Country | GDP_Growth_2026 | Inflation_2026 | Budget_Deficit_2026 | Current_Account_2026 | Unemployment_2026 |
|---|---|---|---|---|---|
| BRA | ? | ? | ? | ? | ? |

### Step 1: Research FRED Series for Brazil
Need to confirm these exist (high confidence based on naming patterns):
- GDP Growth: `NAEXKP01BRQ657S` (OECD quarterly — may not exist for Brazil; alternative: `BRALORSGPNOSTSAM`)
- CPI: `BRACPIALLMINMEI` (monthly CPI index)
- Unemployment: `LRHUTTTTBRM156S` (may not exist — Brazil uses IBGE PNAD)
- Policy Rate: `IRSTCI01BRM156N` (Selic rate — may need alternative series)
- 10Y Bond: likely NOT on FRED — will need fallback
- FX: `DEXBZUS` (daily BRL per USD) ✅ confirmed exists
- Current Account: `BRAB6BLTT02STSAQ` (% GDP)

**Known risk:** Brazil has more FRED gaps than South Africa. May need fallbacks for GDP, unemployment, bond yield, and possibly policy rate. The Selic rate might be under a different FRED series ID.

Yahoo Finance tickers: `^BVSP` (Bovespa index), `USDBRL=X` (FX pair)

### Step 2: Backend Changes

**build_snapshot.py — 3 edits:**

```python
# 1. Add to COUNTRY_CONFIG
"BRA": {
    "name": "Brazil",
    "flag": "🇧🇷",
    "lat": -15.8,       # Brasília
    "lon": -47.9,
    "fx_key": "USD/BRL",
    "stock_symbol": "^BVSP",
    "fx_yahoo": "USDBRL=X",
    "fred": {
        "gdp_growth":     "NAEXKP01BRQ657S",  # verify
        "inflation":      "BRACPIALLMINMEI",
        # "unemployment": may need fallback
        "policy_rate":    "IRSTCI01BRM156N",   # verify (Selic)
        # "bond_yield_10y": likely fallback
        "currency":       "DEXBZUS",
        "current_account": "BRAB6BLTT02STSAQ",
    },
    "inflation_is_yoy": False,
    "rate_is_range": False,
    "fx_invert": False,    # DEXBZUS is BRL per USD - matches USD/BRL
    "fx_decimals": 2,
},

# 2. Add to FALLBACK
"corp_spread": {..., "BRA": 220},
"sov_cds":     {..., "BRA": 160},
"yield_curve": {..., "BRA": 120},
# Plus any FRED gaps:
"unemployment": {..., "BRA": 6.8},
"bond_yield_10y": {..., "BRA": 13.5},

# 3. Update description to "11 countries"
```

### Step 3: Frontend Changes

**macrosnaps-globe.html — same script pattern as ZAF:**

1. Parse countries-data JSON, add BRA object with:
   - **Metrics:** Use Ralph's forecasts + current market estimates
   - **Stories (3×3):** Cover Selic rate (~14.25%), fiscal trajectory, Lula spending, real commodity exposure, BRL vol
   - **fxRegime (3 levels):** Managed float, BCB intervention, carry trade dynamics
   - **Historical arrays (2020–2026F):** GDP, CPI, unemployment, Selic, 10Y, Bovespa YTD
   - **weatherGrid (2020–2026F):** GDP, CPI, unemployment, budget, CA

2. Add glossary terms: BCB (Banco Central do Brasil), Bovespa/B3, Selic, real (currency)

### Step 4: Deploy
Same as ZAF — git add both files, push, run data refresh.

### Estimated Time
- FRED series research: 10 min (web search to verify which series exist)
- Backend edits: 5 min
- Frontend script: 15 min (stories are the bulk — need current Brazil news)
- Glossary: 5 min
- Total: ~35 min in one Claude session

### Things to Watch
- **FRED coverage for Brazil** is spottier than for OECD members. South Africa had near-complete coverage; Brazil may need more fallback values.
- **Bovespa (^BVSP)** on Yahoo Finance can be flaky — may need retry logic or fallback.
- **BRL is high-vol** (~15-20% annualized) — FX Vol display should use 1 decimal.
- After adding Brazil, the dashboard will have 11 countries. Layout should hold fine — the comparison tables and weather grids loop dynamically.


---

## 13. KNOWN LIMITATIONS & TECH DEBT

1. **Stories are static** — no auto-generation. Must be manually researched and patched.
2. **No automated scheduling** — daily ritual is manual bash commands on Mac.
3. **Single HTML file** — at 13,300+ lines, edits require careful targeting. Any JSON syntax error in the embedded blocks breaks the entire app.
4. **Fallback values go stale** — corp spread, sov CDS, yield curve are hardcoded estimates that should be periodically reviewed.
5. **Historical data in HTML** — the inline historical arrays are static. The backend generates fresh historical data in snapshot.json, but the HTML's inline copy is only updated when you re-run the add-country script.
6. **No error monitoring** — if Render deploys a broken HTML file, there's no alert.
7. **Yahoo Finance rate limits** — occasional failures during data fetch; the script handles this gracefully with fallbacks.


---

## 14. USEFUL COMMANDS

```bash
# Check what's live
open https://macrosnaps-01.onrender.com/macrosnaps-globe.html

# Check git status
cd /Users/lisaswerling/Downloads/macrosnaps-repo && git status

# View recent commits
git log --oneline -10

# Check if ZAF/BRA exists in files
grep "ZAF\|BRA" frontend/macrosnaps-globe.html
grep "ZAF\|BRA" backend/build_snapshot.py

# Run data refresh
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Quick push after data refresh
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main

# Nuclear option: hard refresh browser cache
# Cmd+Shift+R or open incognito (Cmd+Shift+N)
```


---

## 15. CURRENT STATE (as of Feb 12, 2026)

- **Countries:** 10 (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF)
- **Commodities:** 9
- **Glossary terms:** 180
- **Stories:** Fresh as of Feb 12 — dollar weakness, gold past $5,000, Friday CPI catalyst
- **Data:** Live as of Feb 12 run — 126+ metrics fetched
- **Sparklines:** Removed from commodity card front (charts only in metric tooltips)
- **Next task:** Add Brazil (BRA) as 11th country
