# MacroSnaps — Comprehensive Handover Brief (v2)

**Date:** February 13, 2026
**Live URL:** https://macrosnaps-01.onrender.com/macrosnaps-globe.html
**Repo:** https://github.com/ralphlazar/macrosnaps-01.git
**Local path:** `/Users/lisaswerling/Downloads/macrosnaps-repo/`
**Hosting:** Render (static site, auto-deploys from `main` branch)


---

## 1. PROJECT OVERVIEW

MacroSnaps is an interactive global economic dashboard. A 3D globe (Three.js) displays pulsing dots for 11 countries and 2 commodity poles. Users click a dot → a "card" slides in showing macro metrics, market metrics, stories at 3 expertise levels (beginner/moderate/expert), and a glossary that highlights economic terms with popover definitions.

**Current scope (as of Feb 13, 2026):**
- 11 countries: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA
- 9 commodities: WTI Crude, Brent Crude, Natural Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans
- 184 glossary terms across 7 categories (macro, equity, credit, fx, institutions, commodities, trade)
- 3 expertise levels throughout (beginner → moderate → expert)
- Weather emoji system: ☀️ ⛅ ☁️ ⛈️ based on economic health


---

## 2. FILE ARCHITECTURE

```
macrosnaps-repo/
├── frontend/
│   ├── macrosnaps-globe.html    ← THE monolith (~13,500+ lines). All CSS, HTML, JS, data.
│   └── snapshot.json            ← Daily data output from backend
├── backend/
│   └── build_snapshot.py        ← Data fetcher (~1,820 lines). Runs daily.
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
| 700–3,500+ | `<script id="countries-data">` — JSON block with all 11 countries' metrics, stories, fxRegime, historical data, weatherGrid |
| 3,500–7,400+ | `<script id="glossary-data">` — 184 terms, each with 3 expertise levels |
| 7,400–7,800 | `<script id="app-config">` — Commodity items, global stories, commodity stories |
| 7,800–7,900 | JS: Data bootstrap — parses JSON blocks into `countries`, `glossary`, `cardStories` arrays |
| 7,900–8,200 | JS: Globe initialization (Three.js) — wireframe, dots, hit targets, drag/touch controls |
| 8,200–8,400 | JS: Labels overlay — country labels positioned via 3D→2D projection |
| 8,400–9,400+ | JS: Card rendering, tooltips, metric popovers, glossary highlighting, comparison tables |

### The Backend: `build_snapshot.py`

**Internal structure:**

| Lines (approx) | Section |
|---|---|
| 1–45 | Imports, logging, FRED API setup |
| 46–290 | `COUNTRY_CONFIG` — 11 countries, each with FRED series IDs, Yahoo symbols, FX config |
| 290–320 | `FALLBACK` — Hardcoded values for metrics with no free API (corp spread, sov CDS, yield curve, plus FRED data gaps) |
| 320–340 | `COMMODITY_CONFIG` — 9 commodities with Yahoo symbols + fallback prices |
| 340–380 | Google Sheets integration — fetches Ralph's forecast spreadsheet |
| 380–600 | Fetch functions: `fetch_fred()`, `fetch_yahoo()`, `fetch_weo_budget()`, `fetch_forecasts()` |
| 600–675 | Computation: `compute_yoy_inflation()`, `compute_ytd_return()`, `compute_realized_vol()`, `compute_yield_curve()` |
| 675–725 | Formatting: `fmt_pct_signed()`, `fmt_rate()`, `fmt_bps()`, `fmt_fx()` etc. |
| 725–950 | Weather assignment: GDP > 2% + low inflation + low unemployment → ☀️ ... → ⛈️ |
| 950–1,160 | Historical data builders: fetch 2010→now from FRED, resample monthly/annually |
| 1,160–1,500 | `build_country()` — assembles one country's full data object |
| 1,500–1,640 | `build_commodities()` — fetches 9 commodity prices from Yahoo |
| 1,640–1,820 | `build_snapshot()` — main entry, loops all countries, writes JSON |


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

**Runtime:** ~6 minutes (FRED rate-limits at 0.2s between calls × ~80 series + Yahoo fetches for 11 countries + 9 commodities)

**Expected output (as of Feb 13):**
```
Metrics: 154 total | 113 live | 40 fallback | 1 missing
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
  🛢️ COMM: ☁️  9/9 commodities live
```

**Fallback metrics** (no free API available — use hardcoded estimates):

| Metric | Countries using fallback |
|---|---|
| Corp Spread | All 11 countries |
| Sov CDS | All 11 countries |
| Yield Curve | 9 countries (USA + one other computed live from DGS10-DGS2) |
| Inflation | JPN |
| GDP Growth | CHN |
| Unemployment | CHN, IND, BRA |
| 10Y Bond Yield | CHN, IND, BRA |


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

**Current columns:**
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

**How it works:**
- `build_snapshot.py` fetches this CSV on every run
- Forecast values override the FRED-derived macro numbers when present
- Policy Rate always comes from FRED (not in the sheet)
- The sheet is the "absolute truth" for macro forecasts
- If the sheet fetch fails, the script continues with FRED data only

**To add a new country:** Ralph adds a row with the country code (e.g., "RUS") and the script picks it up automatically — but only if the code exists in `COUNTRY_CONFIG`.


---

## 7. COUNTRY DATA SCHEMA (FRONTEND)

Each country in the `countries-data` JSON block has this structure:

```json
{
  "BRA": {
    "code": "BRA",
    "name": "Brazil",
    "flag": "🇧🇷",
    "lat": -15.8,
    "lon": -47.9,
    "weather": "⛅",
    "metrics": {
      "macro": {
        "GDP Growth": "+1.7%",
        "Inflation (CPI)": "4.2%",
        "Unemployment": "5.1%",
        "Budget Deficit": "-0.8% GDP",
        "Current Account": "-2.6% GDP",
        "Policy Rate": "15.00%"
      },
      "market": {
        "Stock Market YTD": "+16.5%",
        "Equity Vol": "~22",
        "10Y Bond Yield": "13.56%",
        "Yield Curve": "-145bps",
        "Corp Spread": "220bps",
        "Sov CDS": "160bps",
        "USD/BRL": "5.22",
        "FX Vol": "16.8%"
      }
    },
    "stories": {
      "beginner": ["bullet 1", "bullet 2", "bullet 3"],
      "moderate": ["bullet 1", "bullet 2", "bullet 3"],
      "expert": ["bullet 1", "bullet 2", "bullet 3"]
    },
    "fxRegime": {
      "label": "Managed Float",
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
      "gdp": {"flag": "🇧🇷", "values": [2020, 2021, 2022, 2023, 2024, 2025, 2026F]},
      "cpi": {"flag": "🇧🇷", "values": [...]},
      "unemp": {"flag": "🇧🇷", "values": [...]},
      "budget": {"flag": "🇧🇷", "values": [...]},
      "ca": {"flag": "🇧🇷", "values": [...]}
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
"BRA": {
    "name": "Brazil",
    "flag": "🇧🇷",
    "lat": -15.8,         # Globe dot latitude
    "lon": -47.9,         # Globe dot longitude
    "fx_key": "USD/BRL",  # Label shown on card
    "stock_symbol": "^BVSP",     # Yahoo Finance ticker for stock index
    "fx_yahoo": "USDBRL=X",     # Yahoo Finance ticker for FX pair
    "fred": {
        "gdp_growth":     "NAEXKP01BRQ657S",    # OECD quarterly GDP growth
        "inflation":      "BRACPIALLMINMEI",     # CPI index (YoY computed)
        # unemployment: not available in FRED — uses fallback
        "policy_rate":    "IRSTCI01BRM156N",     # Selic rate
        # bond_yield_10y: not available in FRED — uses fallback
        "currency":       "DEXBZUS",             # BRL per USD (daily)
        "current_account": "BRAB6BLTT02STSAQ",   # Current account % GDP
    },
    "inflation_is_yoy": False,  # False = CPI index, script computes YoY
    "rate_is_range": False,     # True only for USA (Fed target range)
    "fx_invert": False,         # True = flip the FRED rate (e.g., CAD per USD → USD per CAD)
    "fx_decimals": 2,           # Decimal places for FX display
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

**FALLBACK dict:** Metrics with no free API get hardcoded estimates:
```python
FALLBACK = {
    "corp_spread":    {..., "BRA": 220},    # basis points
    "sov_cds":        {..., "BRA": 160},    # basis points
    "yield_curve":    {..., "BRA": -145},   # basis points (10Y - Selic; deeply inverted)
    "unemployment":   {..., "BRA": 5.1},    # FRED gap
    "bond_yield_10y": {..., "BRA": 13.56},  # FRED gap
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
4. Either: manually edit the HTML, or create a Python script to patch all story blocks

**Story locations in the HTML:**
- Country stories: inside `<script id="countries-data">` → each country → `"stories"` key
- Global stories: inside `<script id="app-config">` → `"globalStories"` key
- Commodity stories: inside `<script id="app-config">` → `"commodities"` → `"stories"` key

**Total stories to update:** 10 items (3 global + 3 per-country × 11 + 3 commodity) × 3 levels = ~42 story sets, 126 individual bullets.


---

## 11. WHAT WE DID TO ADD SOUTH AFRICA (ZAF) — 10th Country

### Step 1: Research FRED Series
Searched FRED for South Africa economic data. Confirmed these series exist:
- GDP Growth: `NAEXKP01ZAQ657S` (OECD quarterly)
- CPI: `ZAFCPIALLMINMEI` (monthly index)
- Unemployment: `LRHUTTTTZAM156S` (monthly rate — ~32.5%) ← NOTE: this has since started returning 400 errors
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
1. **Parsed the countries-data JSON block** using `json.loads()` on the content between `<script id="countries-data">` and `</script>`
2. **Added complete ZAF object** with metrics, stories, fxRegime, historical, weatherGrid
3. **Re-serialized** the full JSON and replaced the block in HTML
4. **Added 3 glossary terms:** SARB, JSE, load-shedding

### Step 4: Ralph's Sheet
Confirmed Ralph already added ZAF row with forecasts.

### Step 5: Deploy
```bash
git add frontend/macrosnaps-globe.html backend/build_snapshot.py
git commit -m "Add South Africa (ZAF) — 10th country"
git push origin main
# Then data refresh:
FRED_API_KEY=... python3 backend/build_snapshot.py
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily snapshot with ZAF live data"
git push origin main
```


---

## 12. WHAT WE DID TO ADD BRAZIL (BRA) — 11th Country (Feb 13, 2026)

### Step 1: Verify FRED Series
Ran a bash one-liner from Terminal to test each candidate FRED series:

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
   - Unemployment and 10Y bond yield omitted from fred dict (use fallback)
   - `inflation_is_yoy: False` (CPI index → script computes YoY)
   - `fx_invert: False` (DEXBZUS is BRL per USD, matches USD/BRL display)
   - `fx_decimals: 2`

2. **Added BRA to all FALLBACK dicts:**
   - `corp_spread`: 220 bps
   - `sov_cds`: 160 bps
   - `yield_curve`: -145 bps (deeply inverted — 10Y at 13.56% vs Selic at 15%)
   - `unemployment`: 5.1%
   - `bond_yield_10y`: 13.56%

3. **Updated docstring** from "10 countries" to "11 countries"

### Step 3: Frontend — macrosnaps-globe.html (via Python injection script)
Used a Python script (`add_brazil.py`) that:

1. **Parsed the countries-data JSON block** from the HTML
2. **Added complete BRA object** with:
   - 6 macro metrics + 8 market metrics (initial values from current data)
   - 3×3 stories covering: Selic at 15%, record-low unemployment (5.1%), fiscal credibility pre-2026 elections, BCB monetary transmission, labor market paradox, fiscal-monetary tension
   - fxRegime descriptions at 3 levels (managed float, BCB FX swaps, carry trade dynamics, reserve position ~$350bn)
   - Historical data arrays (2020–2026F) for 6 key metrics
   - weatherGrid data (2020–2026F) for cross-country comparison tables
3. **Added 4 glossary terms:** BCB, Bovespa, Selic, real (currency)
4. **Re-serialized** both JSON blocks and replaced them in the HTML

### Step 4: Ralph's Sheet
Confirmed BRA row already present with forecasts:
- GDP 1.7%, Inflation 4.2%, Unemployment 5.7%, Budget -0.8%, CA -2.6%

### Step 5: Deploy
```bash
# First push: the code changes
cp ~/Downloads/macrosnaps-globe.html frontend/macrosnaps-globe.html
cp ~/Downloads/build_snapshot.py backend/build_snapshot.py
git add frontend/macrosnaps-globe.html backend/build_snapshot.py
git commit -m "Add Brazil (BRA) — 11th country with full data, stories, glossary"
git push origin main

# Second push: live data refresh
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily snapshot with BRA live data"
git push origin main
```

**Build output confirmed:** `🇧🇷 BRA: ☁️ 14/14 metrics live`


---

## 13. ROADMAP: ADDING RUSSIA (RUS) — 12th Country

Adding Russia follows the same 5-step pattern as ZAF and BRA, but with **significantly more data challenges** due to Western sanctions.

### Key Challenges Specific to Russia

1. **FRED coverage is degraded.** Many OECD-sourced series for Russia may have stopped updating after 2022 sanctions. The standard `NAEXKP01RUQ657S` GDP series may no longer receive data. Must be verified.

2. **No USD/RUB FRED series.** Russia shut down dollar and euro trading on the Moscow Exchange (MOEX) in June 2024 after US sanctions targeted the exchange directly. The FRED series `DEXRUS` (if it exists) likely stopped updating. The CBR now sets the official rate via OTC interbank data. Yahoo Finance `USDRUB=X` may still work but reflects a different market (offshore/NDF rates vs onshore CBR fix).

3. **Yahoo Finance MOEX data is available but tricky.** The MOEX Russia Index trades on Yahoo as `IMOEX.ME` (RUB-denominated). It's been available and updating (currently ~2,800–3,200 range), but foreign investor access is restricted, so the index has decoupled from global EM flows.

4. **Heavily sanctions-distorted economy.** Unemployment at 2.2% (record low) masks wartime labor shortages. Inflation at ~5.8%. Key rate at 16% (cut from 21% peak). GDP ~0.8–1.1% growth. All data must be interpreted with heavy caveats about wartime distortion.

5. **IMF Article IV suspended.** The last IMF consultation for Russia was February 2021. WEO budget data may be stale or unavailable, which means the `fetch_weo_budget()` function may fail for Russia — will need fallback for budget deficit.

### Pre-requisite: Ralph's Sheet
Ralph needs to add a RUS row with forecasts:

| Country | GDP_Growth_2026 | Inflation_2026 | Budget_Deficit_2026 | Current_Account_2026 | Unemployment_2026 |
|---|---|---|---|---|---|
| RUS | ~0.8–1.1 | ~5.3 | ~-1.6 | ~2.5 | ~2.3 |

Suggested sources for forecasts: IMF WEO January 2026 (GDP 0.8%), Interfax/CBR survey (inflation 5.3%, GDP 1.1%), Moscow Times analysis.

### Step 1: Verify FRED Series

Run this in Terminal to test:

```bash
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in NAEXKP01RUQ657S RUSCPIALLMINMEI LRHUTTTTRUM156S IRSTCI01RUM156N IRLTLT01RUM156N DEXRUS RUSB6BLTT02STSAQ; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done
```

**My best guesses on what will happen:**

| Series | Expected Result | Fallback if dead |
|---|---|---|
| `NAEXKP01RUQ657S` (GDP) | Likely ❌ stopped post-sanctions | ~1.0% |
| `RUSCPIALLMINMEI` (CPI) | Possibly ✅ (IMF still reports) | ~5.8% |
| `LRHUTTTTRUM156S` (Unemployment) | Possibly ✅ or ❌ | ~2.2% |
| `IRSTCI01RUM156N` (Policy rate) | Possibly ✅ (OECD may still track) | 16.0% |
| `IRLTLT01RUM156N` (10Y Bond) | Likely ❌ | ~14.6% |
| `DEXRUS` (FX) | Likely ❌ (MOEX USD trading halted) | ~77 |
| `RUSB6BLTT02STSAQ` (Current Account) | Possibly ✅ | ~2.5% GDP |

**Important:** Even series that return data may have stale values (last observation 2022 or 2023). Check the `date` field — if it's more than a year old, treat it as a fallback.

Russia may need **5–7 fallback values** vs Brazil's 2 and South Africa's 0-1. This is workable — the fallback system handles it gracefully.

### Step 2: Backend — build_snapshot.py (3 edits)

```python
# 1. Add to COUNTRY_CONFIG
"RUS": {
    "name": "Russia",
    "flag": "\U0001f1f7\U0001f1fa",
    "lat": 55.75,       # Moscow
    "lon": 37.62,
    "fx_key": "USD/RUB",
    "stock_symbol": "IMOEX.ME",      # MOEX Russia Index on Yahoo
    "fx_yahoo": "USDRUB=X",          # May be unreliable — verify
    "fred": {
        # Populate only series confirmed live by Step 1
        # Likely: inflation, policy_rate, maybe current_account
        # Comment out any dead series
    },
    "inflation_is_yoy": False,       # CPI index → script computes YoY
    "rate_is_range": False,
    "fx_invert": False,              # RUB per USD matches USD/RUB
    "fx_decimals": 1,
},

# 2. Add to FALLBACK — will likely need many entries
"corp_spread":    {..., "RUS": 350},    # Heavily sanctioned
"sov_cds":        {..., "RUS": 300},    # Sovereign CDS elevated
"yield_curve":    {..., "RUS": -145},   # Inverted (10Y ~14.6% vs key rate 16%)
# Plus FRED gaps (populate based on Step 1 results):
"gdp_growth":     {..., "RUS": 1.0},
"unemployment":   {..., "RUS": 2.2},
"bond_yield_10y": {..., "RUS": 14.6},
# FX may need special handling — see note below

# 3. Update description to "12 countries"
```

**Special FX handling note:** If neither FRED `DEXRUS` nor Yahoo `USDRUB=X` returns reliable data, the script will use the FX fallback. You may want to manually update the RUS FX fallback periodically using the CBR official rate (currently ~77 RUB/USD). Alternatively, the CBR publishes its official rate at `https://www.cbr.ru/eng/currency_base/daily/` — but parsing it would require a new fetch function.

### Step 3: Frontend — macrosnaps-globe.html (via Python injection script)

Same pattern as BRA. Add a RUS object with:

**Metrics (initial values based on current data):**
- GDP Growth: +1.0%
- Inflation (CPI): 5.8%
- Unemployment: 2.2%
- Budget Deficit: -1.6% GDP
- Current Account: +2.5% GDP
- Policy Rate: 16.00%
- Stock Market YTD: ~+12% (MOEX ~3,200, up from ~2,800 at year start)
- Equity Vol: ~28
- 10Y Bond Yield: 14.6%
- Yield Curve: -140bps (inverted)
- Corp Spread: 350bps
- Sov CDS: 300bps
- USD/RUB: 77.2
- FX Vol: 18%

**Stories (3×3) — key themes to cover:**
- Beginner: War economy, very high interest rates, record-low unemployment but labor shortages
- Moderate: CBR cutting from 21% → 16%, wartime GDP slowdown from 4.3% to ~1%, fiscal pressure from defense spending (~7.3% of GDP), VAT hike to 22%
- Expert: Monetary transmission in a sanctions-distorted economy, directed lending circumventing rate hikes, ruble dynamics (capital controls vs oil revenues vs sanctions), National Wealth Fund drawdown, budget deficit structurally higher due to war

**fxRegime (3 levels):**
- Managed float with capital controls. CBR sets official rate from OTC interbank data since MOEX halted USD/EUR trading (June 2024). ~60% of exports now invoiced in rubles (was 14% in 2021). Yuan is the primary hard-currency trading pair on MOEX.

**Historical arrays (2020–2026F):** GDP, CPI, unemployment, key rate, 10Y, MOEX YTD

**Glossary terms to add:** CBR (Central Bank of Russia), MOEX, ruble, key rate (or Selic equivalent explanation)

### Step 4: Deploy
Same as BRA — git add both files, push, run data refresh.

### Estimated Time
- FRED series verification: 5 min (bash one-liner)
- Backend edits: 10 min (more fallbacks than BRA)
- Frontend script (stories are the bulk): 20 min
- Glossary: 5 min
- Total: ~40 min in one Claude session

### Things to Watch

1. **FRED will likely have MORE gaps than any previous country.** Russia may end up being almost entirely fallback-driven for FRED data, with only Yahoo Finance providing live market data (MOEX + FX). This is fine — the fallback system handles it.

2. **Yahoo `USDRUB=X` reliability.** Since MOEX halted dollar trading, the Yahoo FX rate may reflect offshore NDF pricing rather than onshore reality. The CBR official rate (~77) and Yahoo rate may diverge. Worth monitoring.

3. **Yahoo `IMOEX.ME` works.** The MOEX Russia Index is available on Yahoo Finance and actively updating (~2,200–3,200 range). This should provide live stock YTD and equity vol.

4. **WEO budget data may be stale.** The IMF's Article IV for Russia hasn't been updated since 2021. The `fetch_weo_budget()` function may return old or no data. Ralph's sheet forecast becomes the primary source for budget deficit.

5. **Political sensitivity.** Russia's economic data under sanctions is contested. Some metrics (especially GDP and unemployment) are viewed skeptically by Western analysts. The stories should acknowledge this.

6. **Sanctions could change.** If the US drafts sanctions relief (reports of this emerged in Feb 2026), data availability could improve. Conversely, new sanctions could further degrade data feeds.

7. **After adding Russia, the dashboard will have 12 countries.** Layout should hold fine — the comparison tables and weather grids loop dynamically.


---

## 14. KNOWN LIMITATIONS & TECH DEBT

1. **Stories are static** — no auto-generation. Must be manually researched and patched.
2. **No automated scheduling** — daily ritual is manual bash commands on Mac.
3. **Single HTML file** — at 13,500+ lines, edits require careful targeting. Any JSON syntax error in the embedded blocks breaks the entire app.
4. **Fallback values go stale** — corp spread, sov CDS, yield curve are hardcoded estimates that should be periodically reviewed. Russia will have more fallbacks than other countries.
5. **Historical data in HTML** — the inline historical arrays are static. The backend generates fresh historical data in snapshot.json, but the HTML's inline copy is only updated when you re-run the add-country script.
6. **No error monitoring** — if Render deploys a broken HTML file, there's no alert.
7. **Yahoo Finance rate limits** — occasional failures during data fetch; the script handles this gracefully with fallbacks.
8. **ZAF unemployment FRED series broken** — `LRHUTTTTZAM156S` started returning 400 errors as of Feb 13, 2026. Will use fallback until resolved.


---

## 15. USEFUL COMMANDS

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

# Run data refresh
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Quick push after data refresh
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main

# Hard refresh browser cache
# Cmd+Shift+R or open incognito (Cmd+Shift+N)

# Verify FRED series for a new country (replace series IDs)
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in SERIES1 SERIES2; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done

# Count countries in frontend
python3 -c "import json; html=open('frontend/macrosnaps-globe.html').read(); s=html.index('<script type=\"application/json\" id=\"countries-data\">')+len('<script type=\"application/json\" id=\"countries-data\">'); e=html.index('</script>',s); c=json.loads(html[s:e]); print(f'{len(c)} countries: {list(c.keys())}')"
```


---

## 16. CURRENT STATE (as of Feb 13, 2026)

- **Countries:** 11 (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA)
- **Commodities:** 9
- **Glossary terms:** 184
- **Stories:** Fresh as of Feb 12–13 — includes BRA stories on Selic, fiscal trajectory, labor market
- **Data:** Live as of Feb 13 run — 154 total metrics, 113 live, 40 fallback
- **Next task:** Add Russia (RUS) as 12th country
