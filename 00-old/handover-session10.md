# MacroSnaps Handover Brief
## Session 10 - February 11, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard. 3D globe (Three.js) with weather-colored country dots, 9 country cards with 14 macro/market metrics, 3 expertise levels, 170-term enriched glossary, historical charts from 2010, weather icon system, comparison views, and Google Sheet-driven forecasts. **LIVE** with real data.

**Live site:** `https://macrosnaps-01.onrender.com/macrosnaps-globe.html`

**Repo:** `github.com/ralphlazar/macrosnaps-01` (private)

**Creator:** Ralph Lazar - MSc Economics (LSE), ex-Goldman Sachs Global Equity Strategy, ex-CSFB Fixed-Income Prop Trading.

---

## SESSION 10 SUMMARY

### What happened this session

1. **Historical data from 2010.** Extended `build_snapshot.py` with ~440 new lines. Added `fetch_fred_historical()`, `fetch_yahoo_historical()`, and full resampling pipeline (daily to monthly averages, monthly to annual, YoY computation, realized vol series). `build_historical_data()` now builds 10-12 metrics per country going back to 2010. Annual chart labels extended from 6 (2020-2025) to 17 (2010-2026F). Monthly labels extended from 60 to 180 (Jan 2011-Dec 2025). Added `--skip-historical` flag for daily runs. All 9 countries now have 8-12 historical metrics each.

2. **Google Sheet forecasts wired up.** `build_snapshot.py` now fetches Ralph's published Google Sheet CSV on every build. The sheet is absolute truth for macro forecasts. Macro section (GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account) now shows Ralph's 2026 forecasts instead of latest actuals. Policy Rate remains from FRED. Weather grid (2020-2026F) is now populated from historical actuals + 2026F forecast. 2026F values appended to annual bar charts (GDP Growth, Budget Deficit, Current Account). Forecast bars render lighter (25% opacity) to distinguish from actuals. "2026F" label styled in cyan on chart x-axis.

3. **Updated daily stories.** Ran `generate_stories.py` to refresh all 3 global stories and 9 country stories at all 3 expertise levels (90 story pieces). Stories now reference live metric data.

4. **Brightened all UI text.** Systematic pass over every dark text color in the app. All navigation, chart labels, date range buttons, level toggles, weather grid text, compare buttons, footer links, and chart axis ticks moved from #333-#666 range up to #888-#bbb for better readability against black background.

---

## IMPORTANT: TERMINAL USAGE

**Always use your Mac's Terminal app** (not Claude Code) for:
- Running scripts (`python3 backend/build_snapshot.py`)
- Git commands (`git add`, `git commit`, `git push`)
- Moving files into your repo (`cp`)
- Any command that touches your actual project files or API keys

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
1. `build_snapshot.py` fetches metrics from 3 sources + Google Sheet forecasts, computes derived metrics, fetches historical time series from 2010, assigns weather status, populates weather grid, outputs `snapshot.json`
2. `generate_stories.py` reads `snapshot.json`, sends metric context to Claude, writes stories back into `frontend/snapshot.json`
3. `daily_build.sh` runs both scripts in sequence
4. `git push` triggers Render auto-deploy (~30 seconds)
5. Frontend loads `snapshot.json` on page load, replaces hardcoded data

### Daily update workflow
```bash
cd ~/Downloads/macrosnaps-repo

# Full build with historical data (first time or weekly, ~3 min)
set -a && source .env && set +a && python3 backend/build_snapshot.py

# Daily build skipping historical (~1 min)
set -a && source .env && set +a && python3 backend/build_snapshot.py --skip-historical

# Generate stories (~2.5 min)
set -a && source .env && set +a && python3 backend/generate_stories.py

# Deploy
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json && git commit -m "daily update" && git push
```

**IMPORTANT:** `source .env` alone does NOT export variables. Must use `set -a && source .env && set +a` to make API keys available to Python.

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
    build_snapshot.py                  # Daily data fetcher + historical (1541 lines)
    generate_stories.py                # Claude story generator (320 lines)
    daily_build.sh                     # Runs both scripts
    multilevel_claude_service.py       # Original (reference)
    *_fetcher.py / *_loader.py         # 18 original files (superseded)

  frontend/
    macrosnaps-globe.html              # THE product (~8,400 lines)
    snapshot.json                      # Live data (copy of root snapshot.json)
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
    handover-session10.md              # This file
```

### Also on your Mac (older, not needed)
```
~/Downloads/00-old/macrosnaps-repo     # Old copy, ignore
~/macrosnaps/                          # Older project version, ignore
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

### Fallback data (32 metrics - hardcoded)

| Metric | Count | Why |
|--------|-------|-----|
| Corp Spread | 9 | Requires Bloomberg/Markit |
| Sov CDS | 9 | Requires Bloomberg/Markit |
| Yield Curve (non-USA) | 8 | No 2Y bond series in FRED for most countries |
| Japan inflation | 1 | Not in FRED |
| China GDP, unemployment, bond yield | 3 | Not in FRED |
| India unemployment, bond yield | 2 | Not in FRED |

### Historical data from 2010

All FRED series fetched back to 2010-01-01. Yahoo Finance stock/FX prices from 2011-01-01. Per country:

| Country | Historical metrics | Notes |
|---------|-------------------|-------|
| USA | 12 | Includes yield curve (2Y + 10Y both in FRED) |
| CAN, GBR, DEU, FRA, ITA | 11 each | No yield curve (no 2Y in FRED) |
| JPN | 10 | No inflation in FRED, no yield curve |
| IND | 9 | No unemployment, no bond yield, no yield curve |
| CHN | 8 | No GDP, unemployment, bond yield, yield curve |

**NO historical data for:** Corp Spread, Sov CDS (no free API exists)

### Environment variables needed
- `FRED_API_KEY` - get from https://fred.stlouisfed.org/docs/api/api_key.html
- `ANTHROPIC_API_KEY` - for story generation
- `.env` file in repo root (git-ignored)

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

- 3D globe with 9 country dots, drag to rotate, click to open card
- Country cards with 14 metrics (6 macro forecasts from Google Sheet + 8 market from live data)
- Weather icons (sunny/cloudy/stormy) computed from live data
- 3 expertise levels (beginner/moderate/expert) - toggle in top bar
- Stories generated by Claude at all 3 levels (global + per-country)
- 170-term enriched glossary with BLUF + expandable sections
- News icons (fire/lightning/lightbulb) with global stories
- Historical charts from 2010 (10-12 metrics per country)
- 2026F forecast bars in annual charts (lighter styling, cyan label)
- Weather grid (countries x years 2020-2026F) with live data
- Compare views (bar charts across countries)
- Metric popovers with navigation arrows
- Footer links (What/How/Who/Legalese/Ping Me)
- Brightened UI text for readability against black background
- Live on Render, auto-deploys on push

---

## WHAT DOESN'T WORK YET / KNOWN ISSUES

### Charts missing for certain metrics

**USA:**
- Corp Spread: no chart (no free historical source)
- Sov CDS: no chart (no free historical source)

**All other countries (CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND):**
- Yield Curve: no chart (no 2Y bond series in FRED for non-US countries)
- Corp Spread: no chart (no free historical source)
- Sov CDS: no chart (no free historical source)

These show "No historical data" in the chart area.

### Mobile optimization
- App works on mobile but is not optimized. Globe, cards, charts, and navigation need responsive treatment for iPhone screens.

### Other (from previous sessions)
- Password protection: site is public, private by obscurity only
- Automated daily builds: currently manual. Needs GitHub Action or cron.
- Weather dot globe: Session 8 prototype not integrated into main frontend
- Commodities card: spec exists but not built
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

---

## WHAT TO DO NEXT SESSION

### Priority 1: Fix missing charts
Currently these metrics show "No historical data" in charts:
- **USA:** Corp Spread, Sov CDS
- **All other countries:** Yield Curve, Corp Spread, Sov CDS

Options:
- Source free historical data for yield curves (some available via OECD or World Bank APIs)
- For Corp Spread and Sov CDS, consider generating synthetic/approximate data or simply hiding the chart button for those metrics
- Alternatively, display a better "not available" message explaining why

### Priority 2: Mobile optimization (iPhone)
The globe and entire app need to work properly on iPhone screens. Key areas:
- Globe sizing and touch interactions
- Card overlay responsive layout
- Chart sizing within cards
- Navigation/level toggle touch targets
- Font sizes for small screens
- Weather grid horizontal scroll on narrow screens

### Other (lower priority)
- Automate daily builds (GitHub Action at 6am London)
- Password protection
- Integrate weather dot globe concept
- Build commodities card
- Paywall/trial UI
