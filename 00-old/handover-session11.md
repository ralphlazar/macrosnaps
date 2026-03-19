# MacroSnaps Handover Brief
## Session 11 - February 11, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard. 3D globe (Three.js) with weather-colored country dots, 9 country cards with 14 macro/market metrics, 3 expertise levels, 170-term enriched glossary, historical charts from 2010, weather icon system, comparison views, weather grids for 5 macro metrics, and Google Sheet-driven forecasts. **LIVE** with real data. **Mobile optimized** with touch support.

**Live site:** `https://macrosnaps-01.onrender.com/macrosnaps-globe.html`

**Repo:** `github.com/ralphlazar/macrosnaps-01` (private)

**Creator:** Ralph Lazar - MSc Economics (LSE), ex-Goldman Sachs Global Equity Strategy, ex-CSFB Fixed-Income Prop Trading.

---

## SESSION 11 SUMMARY

### What happened this session

1. **Fixed missing historical charts.** Found two bugs preventing Corp Spread, Sov CDS, and non-US Yield Curve charts from displaying. (a) A merge bug in `loadLiveSnapshot()` was replacing entire historical objects instead of merging per-metric -- fixed with metric-level merge. (b) Missing fallback data for 6 countries (CAN, GBR, DEU, FRA, CHN, IND had `"historical": null`) -- generated 180-point monthly synthetic fallback series for all 3 metrics across all 9 countries with realistic economic patterns (COVID spikes, yield curve inversions, eurozone crisis stress).

2. **Mobile optimization (iPhone).** Complete responsive overhaul:
   - **Touch support on globe:** Added `touch-action: none` to globe container (critical -- without this iOS Safari intercepts all touch events). Added touchstart/touchmove/touchend handlers for swipe-to-rotate, pinch-to-zoom, and tap-to-select-country.
   - **Responsive CSS:** Two breakpoints (768px and 380px). Top bar stacks vertically (logo above buttons, `position:static`). Globe shrinks to `min(52vh, 88vw)`. News icons, cards, tooltips, charts, weather grids, glossary bubbles, footer all resize.
   - **iPhone-specific:** `env(safe-area-inset-*)` for notch/home indicator. Input `font-size:16px` prevents iOS auto-zoom. `-webkit-overflow-scrolling:touch` for smooth scroll. Pixel ratio rechecked on orientation change.
   - **Weather grid scroll:** Table wrapped in `.wg-table-wrap` with horizontal scroll for narrow screens.
   - **Touch targets:** All interactive elements have min-height 28-36px.
   - **Globe hint:** Dynamically shows "Swipe to rotate / Pinch to zoom / Tap a country" on mobile, "Drag to rotate / Scroll to zoom / Click a country" on desktop.

3. **Fixed global stories not loading from snapshot.** `loadLiveSnapshot()` was updating country data but never updating `globalStories` (the 3 news icon stories). Added code to merge `snap.globalStories` into `newsData` so live stories override hardcoded fallback.

4. **Fixed daily build order bug.** The `cp snapshot.json frontend/snapshot.json` was being run AFTER `generate_stories.py`, overwriting the just-generated stories with the storyless root copy. Created `daily_build.sh` with correct order: build -> copy -> generate stories -> git push.

5. **Added 3 new weather grids (Unemployment, Budget Deficit, Current Account).** Now 5 of 6 macro metrics have weather grids (all except Policy Rate). Each grid shows 9 countries x 7 years (2020-2026F) with weather icons. Accessible via the "Over Time" button in each metric's Compare All Countries view.

   **Weather thresholds:**
   | Metric | Sunny ☀️ | Cloudy ☁️ | Stormy ⛈️ |
   |--------|----------|-----------|-----------|
   | GDP Growth | ≥3% | 0-3% | <0% |
   | Inflation (CPI) | 1-3% | 0-1% or 3-5% | <0% or >5% |
   | Unemployment | <5% | 5-8% | >8% |
   | Budget Deficit | >-3% GDP | -3% to -5% | <-5% |
   | Current Account | >0% GDP | -3% to 0% | <-3% |

   Frontend changes: Added `unempAllCountries`, `budgetAllCountries`, `caAllCountries` data structures. Extended `assembleWeatherGrid()` to handle all 5 metrics. Added `unempWeather()`, `budgetWeather()`, `caWeather()` threshold functions. Wired "Over Time" button for all 5 metrics.

   Backend changes: Extended `build_snapshot.py` to generate `unemp`, `budget`, `ca` entries in each country's `weatherGrid` object. Unemployment uses monthly-to-annual averaging (same pattern as CPI). Budget Deficit and Current Account use direct annual extraction (same pattern as GDP). All append 2026F forecast from Google Sheet.

---

## IMPORTANT: TERMINAL USAGE

**Always use your Mac's Terminal app** (not Claude Code) for:
- Running scripts (`python3 backend/build_snapshot.py`)
- Git commands (`git add`, `git commit`, `git push`)
- Moving files into your repo (`cp`)
- Any command that touches your actual project files or API keys

**Claude Code** is a separate tool that had permission issues with the repo in this session. Avoid using it for MacroSnaps work.

**Claude's computer** is a temporary workspace that resets between conversations. Claude edits files there, then gives them to you to download and place in your repo.

**Workflow for code changes:**
1. Upload files to Claude
2. Claude edits on temporary computer
3. You download the edited files
4. You place them in your repo (in Mac Terminal)
5. You push to GitHub (in Mac Terminal)

---

## SITE ARCHITECTURE

### How it works: the newspaper model

Every day, a script runs on your laptop. It collects all numbers from free data sources and Ralph's Google Sheet, asks Claude to write stories, and packages everything into a single JSON file. The website reads that file. There is no server, no database, no backend running 24/7.

```
Daily build (your laptop)          Static site (Render)
+----------------------+           +----------------------+
| build_snapshot.py    |           | macrosnaps-globe.html |
|   -> FRED API        |  git push | snapshot.json         |
|   -> Yahoo Finance   | --------> | glossary/*.json       |
|   -> IMF WEO         |           | index.html            |
|   -> Google Sheets   |           +----------------------+
| generate_stories.py  |           Auto-deploys from GitHub
|   -> Anthropic API   |
| Output: snapshot.json|
+----------------------+
```

### Data flow
1. `build_snapshot.py` fetches metrics from 3 sources + Google Sheet forecasts, computes derived metrics, fetches historical time series from 2010, assigns weather status, populates weather grid (5 metrics), outputs `snapshot.json`
2. `generate_stories.py` reads `snapshot.json`, sends metric context to Claude, writes stories back into `frontend/snapshot.json`
3. `daily_build.sh` runs both scripts in correct order
4. `git push` triggers Render auto-deploy (~30 seconds)
5. Frontend loads `snapshot.json` on page load, merges live data over hardcoded fallback

### Frontend data merge logic (IMPORTANT)

The HTML has hardcoded fallback data for all 9 countries. On page load, `loadLiveSnapshot()` fetches `snapshot.json` and merges it:

- **Country metrics/weather:** Direct replacement (`dst.metrics = src.metrics`)
- **Historical data:** Metric-level merge (snapshot supplements, doesn't replace fallback) -- this was a bug fix in Session 11
- **Country stories:** Only replaced if snapshot has non-empty stories
- **Global stories:** Merged into `newsData` -- this was a bug fix in Session 11
- **Weather grid:** Direct replacement if snapshot has data
- **FX regime:** Only replaced if snapshot has label

This means: hardcoded data in the HTML acts as a safety net. If `snapshot.json` fails to load or is missing a field, the site still works with fallback data. Fallback data for Corp Spread, Sov CDS, and non-US Yield Curve is synthetic (realistic patterns but not real market data).

---

## DAILY UPDATE WORKFLOW

### The daily build script

Location: `backend/daily_build.sh`

```bash
#!/bin/bash
set -a && source .env && set +a

echo "=== Building snapshot ==="
python3 backend/build_snapshot.py

echo "=== Copying to frontend ==="
cp snapshot.json frontend/snapshot.json

echo "=== Generating stories ==="
python3 backend/generate_stories.py

echo "=== Deploying ==="
git add frontend/snapshot.json
git commit -m "daily update"
git push

echo "=== Done ==="
```

### To run it

```bash
cd ~/Downloads/macrosnaps-repo
bash backend/daily_build.sh
```

### CRITICAL ORDER OF OPERATIONS

The order matters:
1. `build_snapshot.py` writes `snapshot.json` (root level) with metrics but no stories
2. `cp snapshot.json frontend/snapshot.json` copies it to frontend
3. `generate_stories.py` reads `frontend/snapshot.json`, generates stories via Anthropic API, writes them back into `frontend/snapshot.json`
4. Git push deploys the file WITH stories

**If you run `cp` AFTER `generate_stories.py`, it overwrites stories with the storyless root copy.** This bug bit us in Session 11.

### Full build vs daily build

```bash
# Full build with historical data (first time or weekly, ~3 min)
set -a && source .env && set +a && python3 backend/build_snapshot.py

# Daily build skipping historical (~1 min)
set -a && source .env && set +a && python3 backend/build_snapshot.py --skip-historical
```

The `daily_build.sh` script runs without `--skip-historical`. To speed up daily runs, edit the script to add `--skip-historical` and do a full build once a week.

### Pushing HTML changes (not part of daily build)

When Claude gives you an updated `macrosnaps-globe.html`:

```bash
cp ~/Downloads/macrosnaps-globe.html ~/Downloads/macrosnaps-repo/frontend/macrosnaps-globe.html
cd ~/Downloads/macrosnaps-repo
git add frontend/macrosnaps-globe.html && git commit -m "description of change" && git push
```

### Pushing backend changes

When Claude gives you an updated `build_snapshot.py`:

```bash
cp ~/Downloads/build_snapshot.py ~/Downloads/macrosnaps-repo/backend/build_snapshot.py
cd ~/Downloads/macrosnaps-repo
git add backend/build_snapshot.py && git commit -m "description of change" && git push
```

### Environment variables

**IMPORTANT:** `source .env` alone does NOT export variables. Must use `set -a && source .env && set +a` to make API keys available to Python.

Required keys in `.env`:
- `FRED_API_KEY` -- for FRED economic data
- `ANTHROPIC_API_KEY` -- for Claude story generation

---

## FILE LOCATIONS

### On your Mac
```
~/Downloads/macrosnaps-repo/          <-- THE repo (git-connected)
  .env                                 # API keys (git-ignored)
  .env.example
  .gitignore
  CLAUDE.md
  README.md
  render.yaml
  requirements.txt
  snapshot.json                        # Build output (root level, NOT deployed)

  backend/
    build_snapshot.py                  # Daily data fetcher + historical (~1580 lines)
    generate_stories.py                # Claude story generator (320 lines)
    daily_build.sh                     # Runs both scripts in correct order
    multilevel_claude_service.py       # Original (reference)
    *_fetcher.py / *_loader.py         # 18 original files (superseded)

  frontend/
    macrosnaps-globe.html              # THE product (~8,700 lines)
    snapshot.json                      # Live data (deployed to Render)
    index.html                         # Redirects to macrosnaps-globe.html
    glossary/
      macro.json                       # 64 terms
      credit.json                      # 28 terms
      equity.json                      # 25 terms
      fx.json                          # 26 terms
      trade.json                       # 8 terms
      institutions.json                # 19 terms

  glossary/                            # Source of truth (same files)
  docs/
    data-backend-spec.md
    handover-session7.md
    handover-session8.md
    handover-session10.md
    handover-session11.md              # This file
```

### On GitHub
`github.com/ralphlazar/macrosnaps-01` (private) -- mirrors `~/Downloads/macrosnaps-repo/`

### On Render
Static site serving `frontend/` directory. Auto-deploys on push to `main`.

---

## DATA SOURCES AND COVERAGE

### Live data (94 metrics)

| Source | Metrics | What |
|--------|---------|------|
| FRED API | 58 | GDP, inflation, unemployment, policy rate, bond yields, FX rates, current account |
| Yahoo Finance | 27 | Stock YTD returns, equity vol (realized), FX vol (realized) |
| IMF WEO | 9 | Budget deficit for all 9 countries |

### Google Sheet forecasts (absolute truth for macro)

| URL | Published CSV |
|-----|---------------|
| `https://docs.google.com/spreadsheets/d/e/2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj/pub?gid=0&single=true&output=csv` | |

Columns: Country, GDP_Growth_2026, Inflation_2026, Budget_Deficit_2026, Current_Account_2026, Unemployment_2026

These values override the macro section in country cards. They also populate the weather grid 2026F column and the 2026F bar in annual charts.

### Fallback data (32 metrics - hardcoded in HTML)

| Metric | Count | Why |
|--------|-------|-----|
| Corp Spread | 9 | Requires Bloomberg/Markit -- synthetic fallback data added Session 11 |
| Sov CDS | 9 | Requires Bloomberg/Markit -- synthetic fallback data added Session 11 |
| Yield Curve (non-USA) | 8 | No 2Y bond series in FRED -- synthetic fallback data added Session 11 |
| USA Corp Spread | 1 | Hardcoded 60-point series (pre-Session 11, preserved by merge fix) |
| USA Sov CDS | 1 | Hardcoded 60-point series (pre-Session 11, preserved by merge fix) |
| Japan/Italy Yield Curve | 2 | Hardcoded from earlier sessions |
| Japan inflation | 1 | Not in FRED |
| China/India historical gaps | varies | Limited FRED coverage for some Chinese/Indian series |

Note: Corp Spread, Sov CDS, and non-US Yield Curve fallback data is **synthetic** (realistic patterns modeled on actual market behavior but not real data). If Bloomberg/Markit access is obtained, `build_snapshot.py` can be extended and the live data will automatically override fallback via the metric-level merge.

### Weather grid data (in snapshot.json → weatherGrid per country)

| Key | Metric | Source | Method |
|-----|--------|--------|--------|
| `gdp` | GDP Growth | Historical annual from WEO/FRED + 2026F from Google Sheet | Direct annual values (index 10-15 = 2020-2025) |
| `cpi` | Inflation | Historical monthly from FRED + 2026F from Google Sheet | Monthly-to-annual averaging |
| `unemp` | Unemployment | Historical monthly from FRED + 2026F from Google Sheet | Monthly-to-annual averaging |
| `budget` | Budget Deficit | Historical annual from WEO + 2026F from Google Sheet | Direct annual values (index 10-15) |
| `ca` | Current Account | Historical annual from FRED + 2026F from Google Sheet | Direct annual values (index 10-15) |

Each has 7 values: [2020, 2021, 2022, 2023, 2024, 2025, 2026F]

---

## FRONTEND STRUCTURE (macrosnaps-globe.html ~8,700 lines)

### Major sections

| Lines (approx) | Content |
|----------------|---------|
| 1-600 | CSS (all styles including mobile responsive) |
| 600-620 | HTML body (top bar, tagline, hero, news icons, globe container, footer) |
| 620-7500 | JSON data blocks (countries, glossary, config, footer content) |
| 7500-7580 | JavaScript: data initialization (parse JSON, build lookup structures) |
| 7580-7640 | Live snapshot loader + live glossary loader |
| 7640-7880 | Globe setup + interaction handlers (mouse + touch) |
| 7880-8100 | Country card assembly + rendering |
| 8100-8350 | Metric tooltip (popover) assembly + rendering + chart rendering |
| 8350-8430 | Weather grid assembly + rendering (5 metrics) |
| 8430-8550 | Compare view assembly + rendering |
| 8550-8700 | Footer tooltips, glossary bubble system, event wiring, init |

### Key JavaScript objects

| Variable | Purpose |
|----------|---------|
| `_countries` | Canonical country data (merged from hardcoded + snapshot) |
| `countries` | Array version (used by globe hit targets) |
| `glossary` | Term definitions at 3 levels |
| `newsData` | Global stories at 3 levels (updated from snapshot) |
| `historicalData` | Time series per country per metric |
| `gdpAllCountries` | Weather grid GDP values per country |
| `cpiAllCountries` | Weather grid CPI values per country |
| `unempAllCountries` | Weather grid Unemployment values per country |
| `budgetAllCountries` | Weather grid Budget Deficit values per country |
| `caAllCountries` | Weather grid Current Account values per country |
| `cardStories` | Per-country stories at 3 levels |
| `fxRegime` | FX regime descriptions per country |
| `currentLevel` | Active expertise level (beginner/moderate/expert) |

### Mobile responsive breakpoints

| Breakpoint | Target |
|------------|--------|
| `@media(max-width:768px)` | Main mobile (iPhone 6/7/8/X/11/12/13/14/15) |
| `@media(max-width:380px)` | Extra small (iPhone SE) |

Key mobile CSS:
- `.globe-wrap { touch-action: none }` -- CRITICAL for iOS touch to work
- `.top-bar { flex-direction: column; position: static }` -- unstacks header
- `.hint-mobile / .hint-desktop` -- toggled by media query
- `.wg-table-wrap { overflow-x: auto }` -- horizontal scroll for weather grids
- `input, textarea { font-size: 16px }` -- prevents iOS zoom on focus
- `body { padding: env(safe-area-inset-*) }` -- notch handling

---

## GLOSSARY STATUS

### 170/170 enriched and live on site

| File | Entries | GitHub Commit |
|------|---------|---------------|
| trade.json | 8/8 | 96e76df |
| institutions.json | 19/19 | 291ae9c |
| credit.json | 28/28 | acd674b |
| equity.json | 25/25 | 0d35fc5 |
| fx.json | 26/26 | 5ff1d79 |
| macro.json | 64/64 | 34d43c3 |

Glossary does NOT update daily. Only changes when manually edited and pushed.

---

## WHAT WORKS RIGHT NOW

- 3D globe with 9 country dots, drag/swipe to rotate, scroll/pinch to zoom, click/tap to open card
- **Mobile optimized** -- touch support, responsive layout, iPhone-safe
- Country cards with 14 metrics (6 macro forecasts from Google Sheet + 8 market from live data)
- Weather icons (sunny/cloudy/stormy) computed from live data
- 3 expertise levels (beginner/moderate/expert) - toggle in top bar
- Stories generated by Claude at all 3 levels (global + per-country)
- **Global stories load from snapshot** (fixed Session 11)
- 170-term enriched glossary with BLUF + expandable sections
- News icons (fire/lightning/lightbulb) with global stories
- Historical charts from 2010 (10-12 metrics per country)
- **Synthetic fallback charts** for Corp Spread, Sov CDS, Yield Curve (added Session 11)
- 2026F forecast bars in annual charts (lighter styling, cyan label)
- **Weather grids for 5 macro metrics** (GDP, CPI, Unemployment, Budget Deficit, Current Account) -- each showing 9 countries x 7 years with weather icons
- Compare views (bar charts across countries) with "Over Time" weather button
- Metric popovers with navigation arrows
- Footer links (What/How/Who/Legalese/Ping Me)
- Live on Render, auto-deploys on push
- **Daily build script** (`daily_build.sh`) with correct operation order

---

## WHAT DOESN'T WORK YET / KNOWN ISSUES

### Policy Rate weather grid
- Not built. Policy Rate is context-dependent (5% can be sunny or stormy depending on inflation). Could tie to real rate (policy - inflation) but not trivial.

### Corp Spread, Sov CDS, Yield Curve (non-US)
- Charts display synthetic fallback data (realistic but not real). No free data source available. If Bloomberg/Markit access obtained, add fetching to `build_snapshot.py` and the merge logic will automatically override.

### Commodities card
- Spec exists from Session 7 (8 commodities, 8 metrics) but not built. This is the next priority item.

### Other (from previous sessions)
- Password protection: site is public, private by obscurity only
- Automated daily builds: currently manual. Needs GitHub Action or cron (6am London suggested)
- Weather dot globe: Session 8 prototype not integrated into main frontend
- Paywall/trial UI: not started

---

## DESIGN RULES (MUST OBEY)

### 0. THE UX MANDATE
**Clarity, smoothness, freshness and simplicity.** The site must look completely different from anything else.

### 1. Weather Icon System - 3 States Only
| State | Icon | CSS Filter |
|-------|------|------------|
| Sunny | sun emoji | `filter: none` |
| Cloudy | cloud emoji | `filter: brightness(.65) contrast(1.05) saturate(.3)` |
| Stormy | cloud emoji | `filter: brightness(.15) contrast(1.2) saturate(0) drop-shadow(...)` |

### 2. Visual language
- Cyan accent (#00d4ff), black background, Space Mono monospace, DM Sans body
- Card overlay: full-screen dark backdrop with blur, cyan-bordered card
- News icons above globe with color-coded hover states
- Text colors: navigation/labels #888-#bbb range (never below #888 against black)
- This is the established design. Do not change it without asking.

### 3. No em dashes. No emoji in UI (except weather icons and story labels). US spelling throughout.

### 4. Google Sheet is absolute truth
Ralph's forecast spreadsheet overrides any computed or fallback values for macro metrics. If the sheet says GDP is 2.1%, the site shows 2.1%.

---

## MONETIZATION AND GO-TO-MARKET

### Model: Freemium + Trial
- Beginner + Moderate: FREE for university students
- Beginner: FREE FOREVER for everyone
- 3-day trial for Expert (no credit card)
- Subscription for Expert after trial

### Pitch Line
"Bloomberg charges $24k/year and assumes you understand macro. We charge $79/year and make sure you do."

### University-first GTM
1. Start with 5 LSE professors
2. Scale via testimonials and student org outreach
3. Other channels: X, Reddit, Product Hunt, CFA/FRM communities

---

## ARCHITECTURE DECISIONS (Cumulative)

1. Single source of truth: glossary JSON files
2. Structured data, no HTML in JSON
3. 6 glossary categories: macro, credit, equity, fx, trade, institutions
4. 3 expertise levels: beginner, moderate, expert
5. BLUF + deep dive pattern
6. GitHub as persistence
7. Uniform country cards (same 14 metrics)
8. US spelling throughout
9. Mobile priority (60-70% of users expected)
10. Goldman-grade content, startup-grade infrastructure
11. University-first go-to-market
12. Historical data target: 2010 (IMPLEMENTED in Session 10)
13. Commodities: 8 commodities, 8 metrics (not yet built)
14. Weather icons are visual shorthand only - no weather language in writing
15. Daily static build model - no server, no database
16. Fallback-first resilience - every fetch has a fallback, script never crashes
17. Frontend wiring is additive - hardcoded data stays as fallback
18. Google Sheet is absolute truth for macro forecasts (Session 10)
19. `set -a && source .env && set +a` required to export env vars (Session 10)
20. `--skip-historical` flag for daily builds that don't need 15 years re-fetched (Session 10)
21. Metric-level historical merge - snapshot supplements, doesn't replace (Session 11)
22. Weather grids for all macro metrics except Policy Rate (Session 11)
23. `touch-action: none` required on globe container for iOS (Session 11)
24. Daily build order: build -> copy -> stories -> push (Session 11)

---

## SESSION HISTORY

### Sessions 1-6
Built prototype: globe, 9 countries, cards, 14 metrics, 3 levels, glossary, charts, weather grids, compare views. Major refactors: data layer separation, assemble/render split, defensive rendering.

### Session 7
GitHub repo created, Claude Code installed. Glossary enrichment: 170/170 via parallel agents. Commodities card designed. Marketing strategy. Monetization model.

### Session 8
Data backend audited. FRED series matrix documented. Launch tightrope resolved. Weather map explored (flat map rejected, globe with weather dots approved, floating card approved). New prototype delivered.

### Session 9
**The site went live.** Built `build_snapshot.py` (94 live metrics from FRED/Yahoo/WEO). Built `generate_stories.py` (90 Claude-generated story pieces). Wired frontend to `snapshot.json`. Wired enriched glossary (170 terms). Deployed to Render as static site. Established daily update workflow.

### Session 10
**Historical data from 2010, Google Sheet forecasts, UI polish.** Extended `build_snapshot.py` with full time series fetching from 2010 (~440 new lines). Wired Ralph's Google Sheet as absolute truth for macro forecasts. Forecasts now populate macro section, weather grid 2026F column, and annual chart 2026F bars. Updated all daily stories. Brightened all UI text for readability (systematic color pass from #333-#666 to #888-#bbb). Added `--skip-historical` flag for daily builds.

### Session 11
**Mobile optimization, bug fixes, weather grids.** Fixed missing historical charts (merge bug + synthetic fallback data). Full mobile/iPhone optimization (touch handlers, responsive CSS, iOS fixes). Fixed global stories not loading from snapshot. Fixed daily build order (created `daily_build.sh`). Added weather grids for Unemployment, Budget Deficit, and Current Account (frontend + backend). Extended `build_snapshot.py` to generate 5 weather grid metrics.

---

## WHAT TO DO NEXT SESSION

### Priority 1: Build commodities card
Spec from Session 7: 8 commodities (Oil, Gold, Copper, Natural Gas, Wheat, Iron Ore, Lithium, Soybeans), 8 metrics each. Needs:
- New data fetching in `build_snapshot.py` (Yahoo Finance has commodity tickers)
- New UI entry point (separate from country cards -- could be a globe icon, a nav button, or a dedicated section)
- Card design following existing visual language
- Stories generated per commodity at 3 levels

### Other (lower priority)
- Automate daily builds (GitHub Action at 6am London)
- Password protection
- Integrate weather dot globe concept
- Paywall/trial UI
- Policy Rate weather grid (if a good threshold model is found)
