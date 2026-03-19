# MacroSnaps — Comprehensive Handover Brief (v3)

**Date:** February 13, 2026
**Live URL:** https://macrosnaps-01.onrender.com/macrosnaps-globe.html
**Repo:** https://github.com/ralphlazar/macrosnaps-01.git
**Local path:** `/Users/lisaswerling/Downloads/macrosnaps-repo/`
**Hosting:** Render (static site, auto-deploys from `main` branch)


---

## 1. PROJECT OVERVIEW

MacroSnaps is an interactive global economic dashboard. A 3D globe (Three.js) displays pulsing dots for 12 countries and 2 commodity poles. Users click a dot → a "card" slides in showing macro metrics, market metrics, stories at 3 expertise levels (beginner/moderate/expert), and a glossary that highlights economic terms with popover definitions.

**Current scope (as of Feb 13, 2026):**
- 12 countries: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS
- 9 commodities: WTI Crude, Brent Crude, Natural Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans
- ~192 glossary terms across 7 categories (macro, equity, credit, fx, institutions, commodities, trade)
- 3 expertise levels throughout (beginner → moderate → expert)
- Weather emoji system: ☀️ ⛅ ☁️ ⛈️ based on economic health


---

## 2. FILE ARCHITECTURE

```
macrosnaps-repo/
├── frontend/
│   ├── macrosnaps-globe.html    ← THE monolith (~14,000+ lines). All CSS, HTML, JS, data.
│   └── snapshot.json            ← Daily data output from backend
├── backend/
│   └── build_snapshot.py        ← Data fetcher (~1,860 lines). Runs daily.
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
| 700–3,800+ | `<script id="countries-data">` — JSON block with all 12 countries' metrics, stories, fxRegime, historical data, weatherGrid |
| 3,800–7,700+ | `<script id="glossary-data">` — ~192 terms, each with 3 expertise levels |
| 7,700–8,100 | `<script id="app-config">` — Commodity items, global stories, commodity stories |
| 8,100–8,200 | JS: Data bootstrap — parses JSON blocks into `countries`, `glossary`, `cardStories` arrays |
| 8,200–8,500 | JS: Globe initialization (Three.js) — wireframe, dots, hit targets, drag/touch controls |
| 8,500–8,700 | JS: Labels overlay — country labels positioned via 3D→2D projection |
| 8,700–9,700+ | JS: Card rendering, tooltips, metric popovers, glossary highlighting, comparison tables |

### The Backend: `build_snapshot.py`

**Internal structure:**

| Lines (approx) | Section |
|---|---|
| 1–45 | Imports, logging, FRED API setup |
| 46–320 | `COUNTRY_CONFIG` — 12 countries, each with FRED series IDs, Yahoo symbols, FX config |
| 320–355 | `FALLBACK` — Hardcoded values for metrics with no free API (corp spread, sov CDS, yield curve, plus FRED data gaps) |
| 355–375 | `COMMODITY_CONFIG` — 9 commodities with Yahoo symbols + fallback prices |
| 375–415 | Google Sheets integration — fetches Ralph's forecast spreadsheet |
| 415–635 | Fetch functions: `fetch_fred()`, `fetch_yahoo()`, `fetch_weo_budget()`, `fetch_forecasts()` |
| 635–710 | Computation: `compute_yoy_inflation()`, `compute_ytd_return()`, `compute_realized_vol()`, `compute_yield_curve()` |
| 710–760 | Formatting: `fmt_pct_signed()`, `fmt_rate()`, `fmt_bps()`, `fmt_fx()` etc. |
| 760–985 | Weather assignment: GDP > 2% + low inflation + low unemployment → ☀️ ... → ⛈️ |
| 985–1,195 | Historical data builders: fetch 2010→now from FRED, resample monthly/annually |
| 1,195–1,535 | `build_country()` — assembles one country's full data object |
| 1,535–1,675 | `build_commodities()` — fetches 9 commodity prices from Yahoo |
| 1,675–1,860 | `build_snapshot()` — main entry, loops all countries, writes JSON |


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

2. **Inline JSON in HTML** — Stories, glossary terms, fxRegime descriptions, and the initial/fallback metric values are embedded directly in the HTML file as `<script type="application/json">` blocks. These are **static** and only change when you edit the HTML manually (or via a Python injection script).

**What the daily bash ritual refreshes:**
- ✅ Metric values (GDP, inflation, unemployment, etc.)
- ✅ Market data (stock YTD, bond yields, FX rates, vol)
- ✅ Commodity prices and % changes
- ✅ Weather emojis (recomputed from live data)
- ✅ Macro forecasts (from Ralph's Google Sheet)
- ✅ Historical time series (FRED + Yahoo, from 2010)
- ❌ Stories (static in HTML — must be manually updated via injection script)
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

**Runtime:** ~7 minutes (FRED rate-limits at 0.2s between calls × ~90 series + Yahoo fetches for 12 countries + 9 commodities). Russia adds ~30 seconds but many of its FRED calls will fail fast.

**Expected output (as of Feb 13, with RUS added):**
```
Metrics: 168 total | ~118 live | ~49 fallback | ~1 missing
  🇺🇸 USA: ☀️  14/14 metrics live
  🇨🇦 CAN: ☁️  14/14 metrics live
  🇬🇧 GBR: ☁️  14/14 metrics live
  🇯🇵 JPN: ☀️  14/14 metrics live
  🇩🇪 DEU: ☀️  14/14 metrics live
  🇫🇷 FRA: ⛈️  14/14 metrics live
  🇮🇹 ITA: ☁️  14/14 metrics live
  🇨🇳 CHN: ☁️  14/14 metrics live
  🇮🇳 IND: ☁️  14/14 metrics live
  🇿🇦 ZAF: ☀️  14/14 metrics live
  🇧🇷 BRA: ☁️  14/14 metrics live
  🇷🇺 RUS: ☁️  ~5-9/14 metrics live (rest fallback — sanctions)
  🛢️ COMM: ☁️  9/9 commodities live
```

**NOTE:** The first time you run `build_snapshot.py` after adding RUS, watch for FRED errors on Russia's series. The script handles them gracefully (falls back to FALLBACK values), but check the log output to see which series are actually alive vs dead. Update FALLBACK values if needed.

**Fallback metrics** (no free API available — use hardcoded estimates):

| Metric | Countries using fallback |
|---|---|
| Corp Spread | All 12 countries |
| Sov CDS | All 12 countries |
| Yield Curve | 10 countries (USA + one other computed live from DGS10-DGS2) |
| Inflation | JPN |
| GDP Growth | CHN, RUS |
| Unemployment | CHN, IND, BRA, RUS |
| 10Y Bond Yield | CHN, IND, BRA, RUS |
| Currency (FX) | RUS (77.2 — Yahoo may override if working) |


---

## 5. DEPLOYMENT PIPELINE

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

## 6. GOOGLE SHEETS INTEGRATION (RALPH'S FORECASTS)

Ralph maintains a published Google Sheet with macro forecasts.

**Sheet URL (published CSV):**
```
https://docs.google.com/spreadsheets/d/e/2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj/pub?gid=0&single=true&output=csv
```

**Current columns (as of Feb 13, 2026):**
| Country | GDP_Growth_2026 | Inflation_2026 | Budget_Deficit_2026 | Current_Account_2026 | Unemployment_2026 |
|---|---|---|---|---|---|
| USA | 2.1 | 2.3 | -7.5 | -3.8 | 4.2 |
| CAN | 1.8 | 2 | -1.5 | -0.5 | 6.5 |
| GBR | 1.5 | 2.1 | -4.2 | -2.5 | 5 |
| JPN | 0.9 | 1.8 | -1.2 | 4.8 | 2.5 |
| DEU | 1.2 | 2.2 | -2 | 4.5 | 3.8 |
| FRA | 1.4 | 2 | -4.8 | 1 | 7.7 |
| ITA | 1 | 2.3 | -3.2 | 0.8 | 5.6 |
| CHN | 4.5 | 2 | -6.8 | 2.5 | 5.1 |
| IND | 6.5 | 4.2 | -7.2 | -1.2 | 4.7 |
| ZAF | 1.6 | 3.5 | -4.8 | -1.4 | 32.5 |
| BRA | 1.7 | 4.2 | -0.8 | -2.6 | 5.7 |
| RUS | 1 | 4.7 | -2.5 | 2 | 2.5 |

**How it works:**
- `build_snapshot.py` fetches this CSV on every run
- Forecast values override the FRED-derived macro numbers when present
- Policy Rate always comes from FRED (not in the sheet)
- The sheet is the "absolute truth" for macro forecasts
- If the sheet fetch fails, the script continues with FRED data only

**To add a new country:** Ralph adds a row with the country code (e.g., "TUR") and the script picks it up automatically — but only if the code exists in `COUNTRY_CONFIG`.


---

## 7. COUNTRY DATA SCHEMA (FRONTEND)

Each country in the `countries-data` JSON block has this structure:

```json
{
  "RUS": {
    "code": "RUS",
    "name": "Russia",
    "flag": "🇷🇺",
    "lat": 55.75,
    "lon": 37.62,
    "weather": "⛅",
    "metrics": {
      "macro": {
        "GDP Growth": "+1.0%",
        "Inflation (CPI)": "4.7%",
        "Unemployment": "2.2%",
        "Budget Deficit": "-2.5% GDP",
        "Current Account": "+2.0% GDP",
        "Policy Rate": "21.00%"
      },
      "market": {
        "Stock Market YTD": "+12.0%",
        "Equity Vol": "~28",
        "10Y Bond Yield": "14.6%",
        "Yield Curve": "-140bps",
        "Corp Spread": "350bps",
        "Sov CDS": "300bps",
        "USD/RUB": "97.2",
        "FX Vol": "18.0%"
      }
    },
    "stories": {
      "beginner": ["bullet 1", "bullet 2", "bullet 3"],
      "moderate": ["bullet 1", "bullet 2", "bullet 3"],
      "expert": ["bullet 1", "bullet 2", "bullet 3"]
    },
    "fxRegime": {
      "label": "Managed Float (Capital Controls)",
      "beginner": "...",
      "moderate": "...",
      "expert": "..."
    },
    "historical": {
      "GDP Growth": {"v": [...7 values...], "annual": true, "type": "bar"},
      "Inflation (CPI)": {"v": [...], "annual": true, "type": "line"},
      "Unemployment": {"v": [...], "annual": true, "type": "line"},
      "Policy Rate": {"v": [...], "annual": true, "type": "line"},
      "10Y Bond Yield": {"v": [...], "annual": true, "type": "line"},
      "Stock Market YTD": {"v": [...], "annual": true, "type": "bar"}
    },
    "weatherGrid": {
      "gdp": {"flag": "🇷🇺", "values": [2020, 2021, 2022, 2023, 2024, 2025, 2026F]},
      "cpi": {"flag": "🇷🇺", "values": [...]},
      "unemp": {"flag": "🇷🇺", "values": [...]},
      "budget": {"flag": "🇷🇺", "values": [...]},
      "ca": {"flag": "🇷🇺", "values": [...]}
    }
  }
}
```

**weatherGrid & historical values** = 7 years: [2020, 2021, 2022, 2023, 2024, 2025, 2026F]

**Important:** These inline metric values (in the HTML) are initial/fallback only. The live values come from `snapshot.json` at runtime and override them. But stories, fxRegime, historical arrays, and weatherGrid are ONLY in the HTML — they are not in snapshot.json.


---

## 8. BACKEND COUNTRY CONFIG SCHEMA

Each country in `COUNTRY_CONFIG` (build_snapshot.py):

```python
"RUS": {
    "name": "Russia",
    "flag": "🇷🇺",
    "lat": 55.75,        # Moscow
    "lon": 37.62,
    "fx_key": "USD/RUB",
    "stock_symbol": "IMOEX.ME",      # MOEX Russia Index on Yahoo
    "fx_yahoo": "USDRUB=X",          # May reflect offshore NDF pricing
    "fred": {
        # Most FRED series likely stopped updating post-2022 sanctions
        "inflation":      "RUSCPIALLMINMEI",
        "policy_rate":    "IRSTCI01RUM156N",
        # gdp_growth: NAEXKP01RUQ657S likely dead — uses fallback
        # unemployment: LRHUTTTTRUM156S likely dead — uses fallback
        # bond_yield_10y: IRLTLT01RUM156N likely dead — uses fallback
        # currency: DEXRUS likely dead (MOEX halted USD Jun 2024) — uses Yahoo/fallback
        "current_account": "RUSB6BLTT02STSAQ",
    },
    "inflation_is_yoy": False,       # CPI index → script computes YoY
    "rate_is_range": False,
    "fx_invert": False,              # RUB per USD matches USD/RUB display
    "fx_decimals": 1,
},
```

**FRED series naming conventions:**
- `NAEXKP01xxQ657S` — OECD GDP growth (xx = 2-letter country code)
- `xxCPIALLMINMEI` — CPI All Items (xx = 3-letter ISO code)
- `LRHUTTTTxxM156S` — Harmonised unemployment rate
- `IRSTCI01xxM156N` — Short-term interest rate
- `IRLTLT01xxM156N` — Long-term government bond yield (10Y)
- `DEXxxUS` — Exchange rate (local currency per USD)
- `xxB6BLTT02STSAQ` — Current account balance (% GDP)

**FALLBACK dict** (as of Feb 13, 2026):
```python
FALLBACK = {
    "corp_spread": {
        "USA": 85, "CAN": 115, "GBR": 100, "JPN": 42,
        "DEU": 55, "FRA": 60, "ITA": 65, "CHN": 55, "IND": 75, "ZAF": 180, "BRA": 220,
        "RUS": 350,
    },
    "sov_cds": {
        "USA": 35, "CAN": 40, "GBR": 25, "JPN": 22,
        "DEU": 15, "FRA": 30, "ITA": 55, "CHN": 60, "IND": 95, "ZAF": 195, "BRA": 160,
        "RUS": 300,
    },
    "yield_curve": {
        "CAN": 15, "GBR": 10, "JPN": 53,
        "DEU": 30, "FRA": 38, "ITA": 62, "CHN": 46, "IND": 23, "ZAF": 85, "BRA": -145,
        "RUS": -140,
    },
    # Known FRED data gaps
    "inflation":      {"JPN": 2.8},
    "gdp_growth":     {"CHN": 5.2, "RUS": 1.0},
    "unemployment":   {"CHN": 5.1, "IND": 4.7, "BRA": 5.1, "RUS": 2.2},
    "bond_yield_10y": {"CHN": 2.56, "IND": 7.18, "BRA": 13.56, "RUS": 14.6},
    "currency":       {"RUS": 77.2},
}
```


---

## 9. HOW THE GLOBE WORKS (THREE.JS)

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

## 10. STORY UPDATES (MANUAL PROCESS)

Stories are NOT auto-generated. They're static text embedded in the HTML's JSON blocks. To update:

1. Research current economic news for each country
2. Write 3 bullets × 3 expertise levels per country (beginner, moderate, expert)
3. Write global stories (3 items × 3 levels) and commodity stories (3 items × 3 levels)
4. Create a Python injection script to patch all story blocks in the HTML

**Story locations in the HTML:**
- Country stories: inside `<script id="countries-data">` → each country → `"stories"` key
- Global stories: inside `<script id="app-config">` → `"globalStories"` key
- Commodity stories: inside `<script id="app-config">` → `"commodities"` → `"stories"` key

**Total stories to update:** 14 items (3 global + 3 per-country × 12 + 3 commodity) × 3 levels = ~48 story sets, 144 individual bullets.

**How the injection script works** (see `update_stories_feb13.py` as a reference):
- Reads the HTML file
- Locates the `<script id="countries-data">` block, parses the JSON
- For each country, replaces the `"stories"` object with new bullets
- Locates the `<script id="app-config">` block, parses the JSON
- Replaces `"globalStories"` and `"commodities" → "stories"` with new content
- Writes the modified HTML back

**Global stories format** (different from country stories — has icon/label/body/source):
```json
{
  "beginner": [
    {
      "icon": "🔥",
      "label": "Today's Story",
      "body": "HTML string with <span class=\"glossary-term\" data-term=\"dollar\">dollar</span> markup...",
      "source": "Bloomberg; Trading Economics"
    },
    { "icon": "⚡", "label": "...", "body": "...", "source": "..." },
    { "icon": "📊", "label": "...", "body": "...", "source": "..." }
  ],
  "moderate": [...],
  "expert": [...]
}
```

**Country stories format** (simple string arrays):
```json
{
  "beginner": ["bullet 1", "bullet 2", "bullet 3"],
  "moderate": ["bullet 1", "bullet 2", "bullet 3"],
  "expert": ["bullet 1", "bullet 2", "bullet 3"]
}
```

**Latest story update:** Feb 13, 2026 — all 12 countries + global + commodities refreshed via `update_stories_feb13.py` (commit 9c4e3bc).


---

## 11. WHAT WE DID TO ADD SOUTH AFRICA (ZAF) — 10th Country

### Step 1: Research FRED Series
Confirmed these series exist:
- GDP Growth: `NAEXKP01ZAQ657S` (OECD quarterly)
- CPI: `ZAFCPIALLMINMEI` (monthly index)
- Unemployment: `LRHUTTTTZAM156S` (monthly rate — ~32.5%) ← **NOTE: started returning 400 errors as of Feb 13, 2026. Uses fallback.**
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
1. Parsed the countries-data JSON block
2. Added complete ZAF object with metrics, stories, fxRegime, historical, weatherGrid
3. Re-serialized the full JSON and replaced the block in HTML
4. Added 3 glossary terms: SARB, JSE, load-shedding

### Step 4: Ralph's Sheet
Confirmed Ralph already added ZAF row with forecasts.

### Step 5: Deploy
```bash
git add frontend/macrosnaps-globe.html backend/build_snapshot.py
git commit -m "Add South Africa (ZAF) — 10th country"
git push origin main
```

### ZAF Key Economic Context (as of Feb 13, 2026)
- SARB at 7.50% (easing cycle in progress)
- GDP ~1.6%, unemployment ~32.5% (structural)
- GNU (Government of National Unity) political premium fading
- JSE benefiting from gold >$5,000/oz
- Load-shedding reduced but still a structural risk


---

## 12. WHAT WE DID TO ADD BRAZIL (BRA) — 11th Country (Feb 13, 2026)

### Step 1: Verify FRED Series
```bash
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in NAEXKP01BRQ657S BRACPIALLMINMEI LRHUTTTTBRM156S IRSTCI01BRM156N IRLTLT01BRM156N DEXBZUS BRAB6BLTT02STSAQ; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done
```

**Results:**
| Series | Status | Latest Value |
|---|---|---|
| `NAEXKP01BRQ657S` (GDP Growth) | ✅ Live | 2025-07-01 = 0.107 |
| `BRACPIALLMINMEI` (CPI) | ✅ Live | 2025-04-01 = 168.82 |
| `LRHUTTTTBRM156S` (Unemployment) | ❌ No data | Fallback: 5.1% |
| `IRSTCI01BRM156N` (Selic rate) | ✅ Live | 2025-12-01 = 15.0 |
| `IRLTLT01BRM156N` (10Y Bond) | ❌ No data | Fallback: 13.56% |
| `DEXBZUS` (FX BRL/USD) | ✅ Live | 2026-02-06 = 5.2183 |
| `BRAB6BLTT02STSAQ` (Current Account) | ✅ Live | 2024-10-01 = -3.90 |

### Step 2: Backend — build_snapshot.py (3 edits)
1. **Added BRA to COUNTRY_CONFIG:**
   - lat/lon: -15.8, -47.9 (Brasília)
   - stock_symbol: `^BVSP` (Bovespa/IBOVESPA)
   - fx_yahoo: `USDBRL=X`
   - 5 FRED series (gdp_growth, inflation, policy_rate, currency, current_account)
   - Unemployment and 10Y bond yield use fallback
   - `inflation_is_yoy: False`, `fx_invert: False`, `fx_decimals: 2`

2. **Added BRA to all FALLBACK dicts:**
   - `corp_spread`: 220 bps
   - `sov_cds`: 160 bps
   - `yield_curve`: -145 bps (deeply inverted)
   - `unemployment`: 5.1%
   - `bond_yield_10y`: 13.56%

3. **Updated docstring** from "10 countries" to "11 countries"

### Step 3: Frontend — macrosnaps-globe.html (via Python injection script `add_brazil.py`)
- 6 macro metrics + 8 market metrics
- 3×3 stories covering: Selic at 15%, record-low unemployment, fiscal credibility
- fxRegime at 3 levels (managed float, BCB FX swaps, carry trade dynamics)
- Historical arrays (2020–2026F) for 6 key metrics
- weatherGrid data
- 4 glossary terms: BCB, Bovespa, Selic, real (currency)

### BRA Key Economic Context (as of Feb 13, 2026)
- Selic at 15.00% (may go to 15.25%), real rates ~11%
- Record-low 5.1% unemployment, 103M employed
- Fiscal credibility under scrutiny pre-2026 elections
- ~40% of credit is government-directed (BNDES), attenuating monetary transmission
- Carry trade attractiveness (Selic-SOFR ~11pp) supports BRL but creates convex downside risk


---

## 13. WHAT WE DID TO ADD RUSSIA (RUS) — 12th Country (Feb 13, 2026)

### Key Challenges Specific to Russia

1. **FRED coverage is degraded.** Many OECD-sourced series stopped updating after 2022 sanctions. Russia is the most fallback-dependent country on the dashboard.
2. **No reliable USD/RUB FRED series.** MOEX halted USD/EUR trading June 2024 after US sanctions targeted the exchange. CBR sets official rate via OTC interbank data. Yahoo `USDRUB=X` may reflect offshore NDF pricing.
3. **Yahoo MOEX data available.** `IMOEX.ME` on Yahoo Finance is actively updating (~2,800–3,200 range). Foreign investor access restricted.
4. **Heavily sanctions-distorted economy.** Unemployment 2.2% masks wartime labor shortages. All data must be interpreted with caveats.
5. **IMF Article IV suspended since 2021.** `fetch_weo_budget()` may return no data for Russia — Ralph's sheet is primary source.

### Step 1: FRED Series (NOT YET VERIFIED)
Russia's FRED series have NOT been tested locally yet. The backend is configured conservatively — only 3 series are active in `COUNTRY_CONFIG` (inflation, policy_rate, current_account), the rest are commented out and use fallback. **First data refresh run will reveal which series are alive.**

To verify manually:
```bash
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in RUSCPIALLMINMEI IRSTCI01RUM156N RUSB6BLTT02STSAQ NAEXKP01RUQ657S LRHUTTTTRUM156S IRLTLT01RUM156N DEXRUS; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done
```

**Expected FRED results:**
| Series | Expected | Fallback if dead |
|---|---|---|
| `RUSCPIALLMINMEI` (CPI) | Possibly ✅ | N/A (Ralph's sheet) |
| `IRSTCI01RUM156N` (Policy rate) | Possibly ✅ | 21.0% |
| `RUSB6BLTT02STSAQ` (Current Account) | Possibly ✅ | +2.0% GDP |
| `NAEXKP01RUQ657S` (GDP) | Likely ❌ | 1.0% |
| `LRHUTTTTRUM156S` (Unemployment) | Likely ❌ | 2.2% |
| `IRLTLT01RUM156N` (10Y Bond) | Likely ❌ | 14.6% |
| `DEXRUS` (FX) | Likely ❌ | 77.2 |

### Step 2: Backend — build_snapshot.py (3 edits) ✅ DONE
1. **Added RUS to COUNTRY_CONFIG:**
   - lat/lon: 55.75, 37.62 (Moscow)
   - stock_symbol: `IMOEX.ME` (MOEX Russia Index)
   - fx_yahoo: `USDRUB=X`
   - 3 FRED series active (inflation, policy_rate, current_account)
   - Everything else commented out — uses fallback
   - `inflation_is_yoy: False`, `fx_invert: False`, `fx_decimals: 1`

2. **Added RUS to all FALLBACK dicts:**
   - `corp_spread`: 350 bps (heavily sanctioned)
   - `sov_cds`: 300 bps
   - `yield_curve`: -140 bps (inverted — 10Y ~14.6% vs key rate 21%)
   - `gdp_growth`: 1.0%
   - `unemployment`: 2.2%
   - `bond_yield_10y`: 14.6%
   - `currency`: 77.2 RUB/USD

3. **Updated docstring** from "11 countries" to "12 countries"

### Step 3: Frontend — macrosnaps-globe.html (via Python injection script `add_russia.py`) ✅ DONE
- 6 macro metrics + 8 market metrics
- 3×3 stories covering: war economy, CBR monetary policy (21% key rate), sanctions distortion, directed lending, ruble dynamics, National Wealth Fund, labor shortages
- fxRegime at 3 levels (managed float with capital controls, MOEX halted USD trading, yuan as primary hard-currency pair, ~60% exports in rubles)
- Historical arrays (2020–2026F) for 6 key metrics
- weatherGrid data
- 4 glossary terms: CBR, MOEX, ruble, key rate

### Step 4: Ralph's Sheet ✅ DONE
RUS row added: GDP 1.0%, Inflation 4.7%, Budget -2.5%, CA +2.0%, Unemployment 2.5%

### Step 5: Deploy ✅ DONE (as part of story update push)
Committed as part of commit 9c4e3bc (story update Feb 13 2026).

**IMPORTANT: The user has NOT yet run `build_snapshot.py` with Russia included.** The backend code is pushed, but the first data refresh with 12 countries has not happened yet. The next daily ritual run will be the first test of Russia's live data feeds.

### RUS Key Economic Context (as of Feb 13, 2026)
- CBR key rate at 21% (held Dec 2025 after hiking from 7.5% in mid-2023)
- GDP decelerating from 4.3% (2024) to ~1% (2026F) as wartime fiscal stimulus wanes
- Unemployment 2.2% — record low, masking severe wartime labor shortages
- Defense spending ~7.3% of GDP, VAT hiked to 22% (Jan 2025)
- Inflation running ~10% (CPI), well above CBR's 4% target
- National Wealth Fund drawdown accelerating (~$55bn remaining)
- MOEX halted USD/EUR trading June 2024; yuan is now primary hard-currency pair
- ~60% of exports invoiced in rubles (was 14% in 2021)
- Sanctions create dual economy: war-connected sectors booming, consumer economy squeezed


---

## 14. STORY UPDATE — Feb 13, 2026

All stories across the dashboard were refreshed on Feb 13, 2026 using `update_stories_feb13.py`. This was a one-shot injection script (can be deleted from repo).

**Research themes per country:**

| Country | Key Themes |
|---|---|
| USA | Jan NFP +130K beat, BLS annual revision slashed 2025 jobs to 181K, Fed on hold 3.5-3.75%, AI disruption contagion, CPI Feb 13 binary for rate path |
| CAN | BoC at 2.75% after aggressive easing, CAD weak ~1.44, C$300B mortgage renewal cliff |
| GBR | MPC 5-4 hold (Mann pivoting dovish), CPI forecast 2.0% by June, March cut live |
| JPN | BOJ hawkish urgency at 0.75%, Takaichi supermajority fiscal-monetary tension, April hike priced |
| DEU | ECB hold through 2026 base case, GDP 0.8-0.9%, auto restructuring, EUR strength |
| FRA | Labour deteriorating, fiscal deficit >5% GDP, CAC 40 luxury/AI crossover |
| ITA | BTP-Bund spread stable ~115bp, NRRP spending supportive, 140%+ debt/GDP |
| CHN | Deflation structural (CPI +0.2%, PPI -1.4% for 40th month), K-shaped growth, Eurasia Group #7 risk |
| IND | RBI cut to 6.25%, GDP 6.3-6.5%, China+1 beneficiary |
| ZAF | SARB at 7.50%, GDP ~1.6%, GNU premium fading, gold >$5K supports JSE |
| BRA | Selic at 13.25% (terminal 14.5%+), fiscal dominance concerns, BRL -15% YoY |
| RUS | CBR at 21%, GDP decelerating to ~1%, labor shortages, directed lending, sanctions distortion |
| Global | DXY structural break <97, gold >$5K, dollar smile breaking, DM rate divergence |
| Commodities | Gold real-rate beta halved, crude API build +13.4M bbl, late-Jan vol spike |


---

## 15. KNOWN LIMITATIONS & TECH DEBT

1. **Stories are static** — no auto-generation. Must be manually researched and patched via injection scripts.
2. **No automated scheduling** — daily ritual is manual bash commands on Mac.
3. **Single HTML file** — at ~14,000+ lines, edits require careful targeting. Any JSON syntax error in the embedded blocks breaks the entire app.
4. **Fallback values go stale** — corp spread, sov CDS, yield curve are hardcoded estimates that should be periodically reviewed. Russia has the most fallbacks.
5. **Historical data in HTML** — the inline historical arrays are static. The backend generates fresh historical data in snapshot.json, but the HTML's inline copy is only updated when you re-run an add-country or injection script.
6. **No error monitoring** — if Render deploys a broken HTML file, there's no alert.
7. **Yahoo Finance rate limits** — occasional failures during data fetch; the script handles this gracefully with fallbacks.
8. **ZAF unemployment FRED series broken** — `LRHUTTTTZAM156S` started returning 400 errors as of Feb 13, 2026. Uses fallback until resolved.
9. **Russia FRED series untested** — first `build_snapshot.py` run with RUS has not happened yet. Some series may fail; the script handles this via fallback.
10. **Russia FX data unreliable** — Yahoo `USDRUB=X` may reflect offshore NDF rates rather than CBR official rate. Monitor for divergence.


---

## 16. USEFUL COMMANDS

```bash
# Check what's live
open https://macrosnaps-01.onrender.com/macrosnaps-globe.html

# Check git status
cd /Users/lisaswerling/Downloads/macrosnaps-repo && git status

# View recent commits
git log --oneline -10

# Check if a country exists in files
grep "RUS\|BRA\|ZAF" frontend/macrosnaps-globe.html
grep "RUS\|BRA\|ZAF" backend/build_snapshot.py

# Run data refresh (daily ritual)
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Quick push after data refresh
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main

# Hard refresh browser cache
# Cmd+Shift+R or open incognito (Cmd+Shift+N)

# Verify FRED series for a country
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in RUSCPIALLMINMEI IRSTCI01RUM156N RUSB6BLTT02STSAQ; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done

# Count countries in frontend
python3 -c "import json; html=open('frontend/macrosnaps-globe.html').read(); s=html.index('<script type=\"application/json\" id=\"countries-data\">')+len('<script type=\"application/json\" id=\"countries-data\">'); e=html.index('</script>',s); c=json.loads(html[s:e]); print(f'{len(c)} countries: {list(c.keys())}')"
```


---

## 17. CURRENT STATE (as of Feb 13, 2026 — end of day)

- **Countries:** 12 (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS)
- **Commodities:** 9
- **Glossary terms:** ~192
- **Stories:** Fresh as of Feb 13 — all 12 countries + global + commodities (commit 9c4e3bc)
- **Data:** Live as of Feb 13 run — 11 countries confirmed live; RUS backend added but first data refresh pending
- **Ralph's Sheet:** 12 countries (RUS row added Feb 13)
- **Pending action:** Run `build_snapshot.py` with RUS for the first time to test Russia's data feeds
- **No upcoming country additions planned** — dashboard is at target scope

### Git History (recent)
```
9c4e3bc Story update Feb 13 2026                    ← stories for all 12 countries + RUS frontend + RUS backend
[prior]  Add Brazil (BRA) — 11th country
[prior]  Daily snapshot with BRA live data
[prior]  Add South Africa (ZAF) — 10th country
```


---

## 18. FOR THE NEXT CLAUDE SESSION

**Files to upload:**
1. `macrosnaps-handover-v3.md` (this file)
2. `build_snapshot.py` (current version with RUS — attached)
3. `macrosnaps-globe.html` (current version — download fresh from repo since it's ~14,000 lines)

**Immediate next steps:**
1. Run the daily bash ritual with RUS included for the first time
2. Check which FRED series are alive for Russia and update FALLBACK if needed
3. Verify the live site shows Russia correctly with all stories, metrics, and globe dot

**Potential future work:**
- Automated story generation (LLM-powered)
- Automated daily scheduling (cron or Render cron job)
- Turkey or other countries as 13th addition
- Error monitoring / alerting on deploy failures
