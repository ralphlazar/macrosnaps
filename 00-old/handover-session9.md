# MacroSnaps Handover Brief
## Session 9 - February 11, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard. 3D globe (Three.js) with weather-colored country dots, 9 country cards with 14 macro/market metrics, 3 expertise levels, 170-term enriched glossary, historical charts, weather icon system, and comparison views. **NOW LIVE** with real data.

**Live site:** `https://macrosnaps-01.onrender.com/macrosnaps-globe.html`

**Repo:** `github.com/ralphlazar/macrosnaps-01` (private)

**Creator:** Ralph Lazar - MSc Economics (LSE), ex-Goldman Sachs Global Equity Strategy, ex-CSFB Fixed-Income Prop Trading.

---

## SESSION 9 SUMMARY: THE SITE WENT LIVE

### What happened this session

1. **Glossary enrichment completed.** All 170/170 entries across 6 files enriched, validated (BLUF length, US spelling, structural checks), committed and pushed. macro.json was the last file - 64/64 entries done.

2. **Built the daily data pipeline.** Created `build_snapshot.py` (966 lines) - a single script that fetches all 14 metrics x 9 countries from FRED, Yahoo Finance, and IMF WEO. Outputs `snapshot.json`. 94 live metrics, 32 known fallbacks, 0 failures. Runs in ~1 minute.

3. **Built story generation.** Created `generate_stories.py` (320 lines) - calls Claude Sonnet to generate 3 global stories + 9 country stories at all 3 expertise levels (90 story pieces total). Uses live metric data as context. Runs in ~2.5 minutes.

4. **Created daily build runner.** `daily_build.sh` runs both scripts in sequence. Total pipeline: ~3.5 minutes.

5. **Wired frontend to live data.** Added 30 lines to `macrosnaps-globe.html` that fetch `snapshot.json` on page load and replace hardcoded data. Falls back silently to hardcoded data if fetch fails. No other frontend code touched.

6. **Wired enriched glossary.** Copied 6 glossary JSON files to `frontend/glossary/`. Added loader that fetches all 6 in parallel, merges into one object, and replaces embedded short definitions. Full enriched content now shows in popovers: BLUF + expandable sections (Why it matters, Intuition, Example, What to watch) + formal definition. Falls back to embedded glossary on fetch failure.

7. **Deployed to Render.** Static site serving `frontend/` directory. Auto-deploys on every push to `main`. Site is live and public (no password gate - private by obscurity for now).

---

## SITE ARCHITECTURE (Current State)

### How it works: the newspaper model

Every day, a script runs locally. It collects all numbers from free data sources, asks Claude to write stories, and packages everything into a single JSON file. The website reads that file. There is no server, no database, no backend running 24/7.

```
Daily build (your laptop)          Static site (Render)
┌──────────────────────┐           ┌──────────────────────┐
│ build_snapshot.py    │           │ macrosnaps-globe.html │
│   -> FRED API        │  git push │ snapshot.json         │
│   -> Yahoo Finance   │ ────────> │ glossary/*.json       │
│   -> IMF WEO         │           │ index.html            │
│ generate_stories.py  │           └──────────────────────┘
│   -> Anthropic API   │           Auto-deploys from GitHub
│ Output: snapshot.json│
└──────────────────────┘
```

### Data flow
1. `build_snapshot.py` fetches metrics from 3 sources, computes derived metrics, assigns weather status, outputs `snapshot.json`
2. `generate_stories.py` reads `snapshot.json`, sends metric context to Claude, writes stories back into `snapshot.json`
3. `daily_build.sh` runs both scripts, copies result to `frontend/`
4. `git push` triggers Render auto-deploy (~30 seconds)
5. Frontend loads `snapshot.json` on page load, replaces hardcoded data

### Daily update workflow
```bash
cd ~/Downloads/macrosnaps-repo
bash backend/daily_build.sh
git add frontend/snapshot.json && git commit -m "daily update" && git push
```

That's it. Three commands. Site updates in ~30 seconds after push.

---

## DATA SOURCES AND COVERAGE

### Live data (94 metrics)

| Source | Metrics | What |
|--------|---------|------|
| FRED API | 58 | GDP, inflation, unemployment, policy rate, bond yields, FX rates, current account |
| Yahoo Finance | 27 | Stock YTD returns, equity vol (realized), FX vol (realized) |
| IMF WEO | 9 | Budget deficit for all 9 countries |

### Fallback data (32 metrics - hardcoded)

| Metric | Count | Why |
|--------|-------|-----|
| Corp Spread | 9 | Requires Bloomberg/Markit |
| Sov CDS | 9 | Requires Bloomberg/Markit |
| Yield Curve (non-USA) | 8 | No 2Y bond series in FRED for most countries |
| Japan inflation | 1 | Not in FRED |
| China GDP, unemployment, bond yield | 3 | Not in FRED (politically managed data) |
| India unemployment, bond yield | 2 | Not in FRED |

### What's NOT connected
- **Google Sheets forecasts** - the original frontend had "MACRO FORECASTS (2026)" from Ralph's spreadsheet. Not wired up yet. Would need Google Sheets API.
- **Historical time series** - charts currently show 2020-2025 hardcoded data. Extending to 2010 requires fetching full FRED time series. Infrastructure exists, just needs extending.
- **Consensus forecasts** - no forward-looking data of any kind

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

All entries validated: BLUF length in range, US spelling, structural checks pass.

Glossary files copied to `frontend/glossary/` and loaded by frontend on page load. Full enriched content renders in popovers: BLUF + expandable sections + formal definition. Level toggle switches between beginner/moderate/expert content.

Glossary does NOT update daily. It only changes when you manually edit entries and push to GitHub.

---

## FILE STRUCTURE (Current)

```
macrosnaps-01/
  .env                          # API keys (git-ignored)
  .env.example                  # Template
  .gitignore
  CLAUDE.md                     # Claude Code context
  README.md                     # Updated with deployment instructions
  render.yaml                   # Render static site config
  requirements.txt              # Python dependencies
  
  backend/
    build_snapshot.py            # Daily data fetcher (966 lines)
    generate_stories.py          # Claude story generator (320 lines)
    daily_build.sh               # Runs both scripts
    multilevel_claude_service.py # Original story service (reference)
    fred_fetcher.py              # Original fetcher (reference)
    yahoo_fetcher.py             # Original fetcher (reference)
    weo_fetcher.py               # Original fetcher (reference)
    *_fetcher.py / *_loader.py   # 18 original files (superseded by build_snapshot.py)
  
  frontend/
    macrosnaps-globe.html        # THE product (~8,200 lines)
    snapshot.json                # Live data (generated daily)
    index.html                   # Redirects to macrosnaps-globe.html
    glossary/
      macro.json                 # 64 terms
      credit.json                # 28 terms
      equity.json                # 25 terms
      fx.json                    # 26 terms
      trade.json                 # 8 terms
      institutions.json          # 19 terms
  
  glossary/                      # Source of truth (same files)
  docs/
    data-backend-spec.md         # FRED series matrix, architecture spec
    handover-session7.md
    handover-session8.md
```

---

## WHAT WORKS RIGHT NOW

- 3D globe with 9 country dots, drag to rotate, click to open card
- Country cards with 14 metrics (6 macro + 8 market), live data
- Weather icons (sunny/cloudy/stormy) computed from live data
- 3 expertise levels (beginner/moderate/expert) - toggle in top bar
- Stories generated by Claude at all 3 levels
- 170-term enriched glossary with BLUF + expandable sections
- News icons (fire/lightning/lightbulb) with global stories
- Historical charts (2020-2025, hardcoded)
- Compare views (bar charts across countries)
- Weather grid (countries x years)
- Metric popovers with navigation arrows
- Footer links (What/How/Who/Legalese/Ping Me)
- Live on Render, auto-deploys on push

---

## WHAT DOESN'T WORK YET

1. **Historical charts from 2010** - currently 2020-2025 hardcoded. Needs full FRED time series fetch added to build_snapshot.py.
2. **Google Sheets forecasts** - "MACRO FORECASTS (2026)" section needs Google Sheets API connection.
3. **Password protection** - site is public. No auth. Private by obscurity only.
4. **Automated daily builds** - currently manual (run script, git push). Needs GitHub Action or cron.
5. **Weather dot globe** - Session 8 prototype with glowing amber/grey/purple dots on globe surface. Explored and liked but not integrated into main `macrosnaps-globe.html`. The main file still uses the original globe style (cyan dots, cyan labels).
6. **Commodities card** - spec exists (`docs/commodities-spec.md`) but not built.
7. **Mobile optimization** - works but not specifically tuned.
8. **Paywall/trial UI** - not started.

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
- This is the established design. Do not change it without asking.

### 3. No em dashes. No emoji in UI (except weather icons and story labels). US spelling throughout.

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
12. Historical data target: 2010 (not yet implemented)
13. Commodities: 8 commodities, 8 metrics (not yet built)
14. Weather icons are visual shorthand only - no weather language in writing
15. **Daily static build model** (Session 9) - no server, no database. Script runs daily, outputs JSON, frontend loads it. Deploy as static site.
16. **Fallback-first resilience** (Session 9) - every fetch has a fallback. Script never crashes. Partial data beats no data.
17. **Frontend wiring is additive** (Session 9) - hardcoded data stays as fallback. Live data overlays it. If fetch fails, site works exactly as before.

---

## SESSION HISTORY

### Sessions 1-6
Built prototype: globe, 9 countries, cards, 14 metrics, 3 levels, glossary, charts, weather grids, compare views. Major refactors: data layer separation, assemble/render split, defensive rendering.

### Session 7
GitHub repo created, Claude Code installed. Glossary enrichment: 170/170 via parallel agents. Commodities card designed. Marketing strategy. Monetization model.

### Session 8
Data backend audited. FRED series matrix documented. Launch tightrope resolved. Weather map explored (flat map rejected, globe with weather dots approved, floating card approved). New prototype `macrosnaps-globe-weather.html` delivered.

### Session 9
**The site went live.** Built `build_snapshot.py` (94 live metrics from FRED/Yahoo/WEO). Built `generate_stories.py` (90 Claude-generated story pieces). Wired frontend to `snapshot.json`. Wired enriched glossary (170 terms). Deployed to Render as static site. Established daily update workflow: run script, git push, auto-deploy.

---

## WHAT TO DO NEXT SESSION

### Priority 1: Verify and polish
- Open the live site, click every country, check every metric looks right
- Toggle all 3 levels, verify stories change appropriately
- Click glossary terms, verify enriched content shows
- Check charts and compare views still work
- Note any bugs or visual issues

### Priority 2: Historical data from 2010
- Extend `build_snapshot.py` to fetch full FRED time series back to 2010-01-01
- Add to `snapshot.json` in the format frontend charts expect
- Frontend chart code already exists - just needs more data points

### Priority 3: Automate daily builds
- GitHub Action that runs `daily_build.sh` at 6am London time
- Commits and pushes `snapshot.json` automatically
- No more manual runs

### Priority 4: Google Sheets forecasts
- Connect to Ralph's forecast spreadsheet via Google Sheets API
- Restore the "MACRO FORECASTS (2026)" section in country cards

### Priority 5: Password protection
- Simple password gate on the HTML, or Render paid tier with basic auth

### Other (lower priority)
- Integrate weather dot globe concept into main frontend
- Build commodities card
- Mobile optimization pass
- Paywall/trial UI
