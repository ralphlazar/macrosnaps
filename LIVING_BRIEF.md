# MacroSnaps - Living Brief
Last updated: March 10, 2026 (Daily update run; global + country + commodity stories updated; "What the project is" description updated)

---

## HOW TO USE THIS FILE

This file has two parts.

**Part 1** is the master session prompt. Copy everything between the START and END markers and paste it as your first message in any new chat.

**Part 2** is the detailed project reference. It lives below the prompt and is for Claude to read from the uploaded file. You do not need to paste it.

---

## PART 1 - MASTER SESSION PROMPT
### Copy from here...

You are helping me build and maintain MacroSnaps, a daily global macro and markets dashboard. Read this entire prompt before doing anything.

I am also uploading `LIVING_BRIEF.md`. Read it in full before responding. It contains the full project reference including architecture, current content state, key file locations, and working preferences.

**Before we start, tell me:**
- What you understand the current state of the project to be (3-4 sentences)
- Which session type this is, based on what I describe below
- Confirm you are ready

**Session types and what to upload**

Do NOT upload all files every session. The large files will fill the context window immediately.

- Tooling session (Git, validator, build script, infrastructure): upload `LIVING_BRIEF.md` + `build.py`
- UI session (tooltip, CSS, layout, JS, shell features): upload `LIVING_BRIEF.md` + `macrosnaps-shell.html`
- Content session (writing stories, updating metrics, editing data): upload `LIVING_BRIEF.md` + `data.json`
- Full build session (changes across files, final assembly): upload all four files, keep it short

If you are not sure which type applies, describe what you want to do and ask which files are needed before uploading anything.

Never upload `macrosnaps-globe.html`. It is a build output, not a source file.

**Working preferences**

⚠️ CRITICAL - PLAN BEFORE BUILDING: Never write code or make any edit without first presenting a clear plan of exactly what will change and why. Wait for explicit approval before proceeding. The word "go" is the signal to proceed. This applies to every change, no matter how small it seems.

Think before building. On any non-trivial change, share your approach and flag concerns before writing code. Wait for me to say "go."

Make surgical edits. Change the minimum needed. Do not rewrite surrounding code unless it is broken.

After each edit, briefly explain what changed and why.

If something feels architecturally wrong, say so before doing it.

Never present a task as done until the build has run successfully and the output has been copied to the outputs folder.

**Stories are written by AI**

All per-metric stories (beginner, moderate, expert) are written by Claude, not by hand. When metric values change meaningfully, `update_stories.py` calls the Claude API and rewrites the relevant stories automatically. Do not write or edit stories manually unless specifically asked to.

**Session rhythm**

We work in focused chunks. At the end of each natural unit of work (a feature shipped, a content block done, a bug fixed), before starting the next thing, you update `LIVING_BRIEF.md` and make it available for download. Do not wait until the context window is full. Write it while everything is fresh.

**Writing style (apply to every response)**

Write in plain, natural English. Do not use em dashes or en dashes. Only use a standard hyphen (-) if a dash is genuinely needed. Prefer commas, periods, or parentheses instead. Before outputting any response, scan it for the characters and. If found, rewrite those sentences. Output only the final corrected version. This rule applies to all responses including code comments and story content written into data.json.

**Story writing style (apply to all metric stories in data.json)**

The goal is for every story to read as if a knowledgeable human wrote it quickly for a smart friend. AI-sounding writing undermines the product. Apply all of the following rules to every story at every level.

- No em dashes or en dashes, ever. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural. "The Fed raised rates" not "rates were raised by the Fed."
- No hedging openers. Never start a sentence with "It is worth noting," "It is important to understand," or "This reflects the fact that."
- No AI-typical sentence starters. Do not begin consecutive sentences with "This metric," "This reflects," or "This suggests."
- Vary sentence length deliberately. Mix short punchy sentences with longer ones. Uniform sentence length is a tell.
- Write numbers as if they are real and specific. "Inflation hit 8.4%" reads better than "the inflation rate stands at 8.4%."
- No filler conclusions. Never end a story with "overall," "in summary," or "taken together."
- No committee language. Write as if explaining to a smart friend, not presenting a report.
- Before outputting any story, scan it against every rule above and rewrite any sentence that fails. Output only the final corrected version.

This style guide must also be included verbatim in the system prompt used by `update_stories.py` when calling the Claude API.

**What I am working on today:**

[describe your task here]

### ...to here

---

## PART 2 - PROJECT REFERENCE

---

### What the project is

MacroSnaps is a daily dashboard that makes global macro and market data accessible to everyone - from curious beginners to seasoned professionals.

Each day, we generate concise snapshots for 12 major economies: the G7 + BRICS. Every card includes key macro forecasts, live market data, AI-generated story bullets, and a weather icon that tells you the economic outlook at a glance.

The product is pre-launch. The architecture is intentionally simple. The goal right now is to get the product right before making it scalable.

**Live URL:** https://ralphlazar.github.io/macrosnaps/macrosnaps-globe.html
**GitHub repo:** https://github.com/ralphlazar/macrosnaps (branch: master)

---

### The 4 source files

| File | What it is | Touch it when |
|---|---|---|
| `data.json` | All content and data | Updating metrics, writing stories, changing values |
| `macrosnaps-shell.html` | The entire app shell (no data) | Changing UI, layout, CSS, JS logic |
| `build.py` | The assembly line script | Changing build logic or validation rules |
| `macrosnaps-globe.html` | The built output | Never - this is generated, not edited |

All files live in `~/Downloads/macrosnaps/`.

**To build:** run `python3 build.py` from inside `~/Downloads/macrosnaps`. The output file is written to the same folder automatically.

**To validate only (no files written):** run `python3 build.py --validate-only`. Use this before editing `data.json`.

**Never modify** `_frozen_historical` or `_frozen_weatherGrid` inside any country in `data.json` by hand. To restore or update them, run `refetch_historical.py` (see below).

---

### Daily bash ritual (run every morning)

This is the complete workflow for a standard data update day. Copy and run these commands in order.

**Step 1. Go to the project folder**
```bash
cd ~/Downloads/macrosnaps
```

**Step 2. Preview the sheet sync**

This fetches your Google Sheet and shows what will change in `data.json`. Nothing is written yet.
```bash
python3 sync_sheet.py
```
Read the output. If the changes look correct, continue. If something looks wrong, fix the sheet first and re-run this step.

**Step 3. Apply the sheet sync**

This writes the macro metric changes to `data.json`.
```bash
python3 sync_sheet.py --apply
```

**Step 4. Fetch live market data**

This pulls Stock Market YTD, 10Y Bond Yield, Yield Curve, and FX pairs from Yahoo Finance and FRED and writes them into `data.json`. The 4 data-void metrics (Equity Vol, Corp Spread, Sov CDS, FX Vol) are skipped - they display as "not available" in the UI.
```bash
python3 fetch_market_data.py
```
(Script not yet built - see Pending work.)

**Step 5. Rewrite stories where values moved**

This diffs `data.json` against the last git commit, identifies metrics that changed past threshold, calls the Claude API, and rewrites stories for those metrics at all three levels.
```bash
python3 update_stories.py
```
(Script not yet built - see Pending work.)

**Step 6. Build the output file**

This validates `data.json`, assembles `macrosnaps-globe.html`, and saves a dated backup.
```bash
python3 build.py
```
The build must say `BUILD SUCCESSFUL` before you continue. If it fails, do not push.

**Step 7. Commit and push**

```bash
git add -A && git commit -m "Daily update $(date +%Y-%m-%d)"
git push origin master
```

**Step 8. Verify the live site**

Wait about 60 seconds, then open:
```
https://ralphlazar.github.io/macrosnaps/macrosnaps-globe.html
```

---

### What the Google Sheet controls

The sheet is the single source of truth for the 6 macro metrics per country. These values are forecast-based and change infrequently. Update them in the sheet when consensus forecasts change, then run the daily ritual.

**Sheet URL (published CSV):**
```
https://docs.google.com/spreadsheets/d/e/2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj/pub?output=csv
```

**Columns synced:**
- GDP_Growth_2026
- Inflation_2026
- Budget_Deficit_2026
- Current_Account_2026
- Unemployment_2026
- Policy_Rate_2026

**What the sheet does NOT control:**
Market metrics are handled by `fetch_market_data.py` (automated) or displayed as "not available" (data-void metrics). Stories are handled by `update_stories.py`. Commodity data, global stories, metricBriefs, and historical chart data are still updated manually or via dedicated scripts.

---

### How to view the app locally

Open directly in Safari (no server needed):
```
open -a Safari ~/Downloads/macrosnaps/macrosnaps-globe.html
```
Or run a local server and open in any browser:
```
cd ~/Downloads/macrosnaps && python3 -m http.server 8000
```
Then go to `http://localhost:8000/macrosnaps-globe.html`. Keep that terminal window open while browsing.

The build inlines `window.__MACROSNAPS_DATA__` before `</head>` so the app is self-contained. Chrome blocks local file access by default. Safari works without a server.

---

### Current content state (March 10, 2026)

**Per-metric stories (beginner / moderate / expert) - ALL COMPLETE**
- USA: 14/14 complete
- CAN: 14/14 complete
- GBR: 14/14 complete
- JPN: 14/14 complete
- DEU: 14/14 complete
- FRA: 14/14 complete
- ITA: 14/14 complete
- CHN: 14/14 complete
- IND: 14/14 complete
- ZAF: 14/14 complete
- BRA: 14/14 complete
- RUS: 14/14 complete

All 168 per-metric stories are complete across all 12 countries and all 3 levels. Going forward, stories for the 4 data-void metrics (Equity Vol, Corp Spread, Sov CDS, FX Vol) will not be maintained as those metrics are moving to "not available" display state.

**Other content (all 12 countries)**
- Country-level stories (3 bullets per level): complete for all 12, last updated March 10, 2026
- metricBriefs (short summaries per metric): complete for all 12
- fxRegime descriptions (3 levels): complete for all 12

**Commodity stories (beginner / moderate / expert) - ALL COMPLETE**
All 9 commodities have a `story` object with beginner, moderate, and expert keys. Last updated March 10, 2026. Update these whenever commodity prices move meaningfully, as part of the daily content session.

**Global stories (March 10, 2026)**
- Slot 1: Oil Swings Wildly as Iran War Dominates Markets (WTI $119 to $88 intraday)
- Slot 2: US Lost 92,000 Jobs in February (stagflation signal, Fed stuck)
- Slot 3: Stock Markets Bounce Back on Peace Hopes (S&P +0.8%, Gold $5,145)

---

### Historical chart data state (March 10, 2026)

`_frozen_historical` was restored using `refetch_historical.py`. Current state:

| Country | Charts populated | Notes |
|---|---|---|
| USA | 14/14 | Yield Curve fixed 2026-03-09 (GS3M short rate) |
| CAN | 14/14 | |
| GBR | 14/14 | |
| JPN | 14/14 | |
| DEU | 14/14 | Yield Curve fixed 2026-03-09 |
| FRA | 14/14 | Yield Curve fixed 2026-03-09 |
| ITA | 14/14 | |
| CHN | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source |
| IND | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source |
| ZAF | 12/14 | Unemployment: no monthly source; Yield Curve populated |
| BRA | 12/14 | 10Y Bond Yield, Yield Curve: no free source |
| RUS | 10/14 | GDP Growth, Unemployment, USD/RUB discontinued post-2022 sanctions |

Metrics with no free public source (historical or live): Equity Vol, Corp Spread, Sov CDS, FX Vol, Budget Deficit.

---

### refetch_historical.py

The script lives in `~/Downloads/macrosnaps/`. It pulls data from FRED and Yahoo Finance and writes `_frozen_historical` into `data.json` in place. It never touches any other field.

**Requirements (one-time setup):**
```
pip3 install requests yfinance python-dotenv
```

**FRED API key** (free): https://fred.stlouisfed.org/docs/api/api_key.html

Create `~/Downloads/macrosnaps/.env` containing:
```
FRED_API_KEY=your_key_here
```

**To run:**
```
cd ~/Downloads/macrosnaps && python3 refetch_historical.py
```

**After a successful run:**
```
python3 build.py && git add -A && git commit -m "Restore _frozen_historical"
git push origin master
```

Key settings at the top of the script:
- `FORCE_OVERWRITE = False` - set to True to re-fetch countries that already have data
- `MIN_POINTS = 5` - existing point count that qualifies as already populated

---

### The 14 metrics per country

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate.

**Market (8):** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, [FX pair - varies by country], FX Vol.

**Data-void metrics (4):** Equity Vol, Corp Spread, Sov CDS, FX Vol. No reliable free daily source exists for any of these. These will be displayed as "not available" in the UI with a tooltip explanation. Stories for these metrics will not be maintained going forward. This decision can be revisited post-launch if a paid data source is added.

**Automatable market metrics (4):** Stock Market YTD (Yahoo Finance), 10Y Bond Yield (FRED), Yield Curve (FRED, derived), FX pair (Yahoo Finance). These are fetched daily by `fetch_market_data.py` (not yet built).

---

### How metric stories work

Stories live in `data.json` inside each metric entry as a `story` object with `beginner`, `moderate`, and `expert` keys.

At load time the shell reads these into the `metricStories` object (line 5605 of shell).

When a user clicks a metric, `renderMTT()` (line 6542) builds the tooltip. The story appears inline between the value and the chart, with no header label. CSS class is `tt-metric-story` (line 165 of shell).

The tooltip order is: metric name, country + value, story, chart, explanation/bluf, FX regime (if applicable), compare button.

**Stories are written and maintained by AI.** `update_stories.py` (not yet built) diffs data.json against the last git commit, identifies metrics that changed past a configurable threshold, calls the Claude API, and rewrites the affected stories at all three levels in one pass. Do not write or edit stories by hand.

---

### Architecture decisions and why

**Google Sheet for macro metrics.** The sheet holds the 6 macro metrics per country (GDP, CPI, unemployment, budget deficit, current account, policy rate). `sync_sheet.py` pulls from the sheet and writes `data.json`. The sheet is updated manually but infrequently, when year-end consensus forecasts change.

**fetch_market_data.py for live market metrics.** Pulls the 4 automatable market metrics (Stock Market YTD, 10Y Bond Yield, Yield Curve, FX pair) from Yahoo Finance and FRED daily. Skips the 4 data-void metrics entirely. Not yet built.

**update_stories.py for story maintenance.** Diffs data.json against the last git commit to detect meaningful value changes, then calls the Claude API to rewrite stories for affected metrics. Runs after both sync_sheet.py and fetch_market_data.py so it catches all changes in one pass. Not yet built. Requires ANTHROPIC_API_KEY in .env.

**No CMS.** Pre-launch solo workflow. JSON plus build script is faster to iterate with than any external system.

**GitHub Pages for hosting.** Repo is public at https://github.com/ralphlazar/macrosnaps. Deploy from master branch, root folder. The built HTML file is self-contained (data inlined) so no build step is needed on the server side.

**Git for version history.** Commit after every feature or meaningful change. `update_stories.py` uses git diff to detect what has changed since the last commit, so committing consistently is essential for correct story rewrite targeting.

---

### Vulnerabilities and mitigations

| Vulnerability | Status | Mitigation |
|---|---|---|
| No version history | Fixed | Git initialized. Commit after every build. |
| JSON corruption from manual edits | Fixed | Run `python3 build.py --validate-only` before editing. Build script also validates on every run. |
| Forgetting to rebuild | Habit-dependent | Never call a task done until build has run and output copied. |
| No preview step | Fixed | `sync_sheet.py` preview mode shows all changes before anything is written. |
| Spurious git diffs from build timestamps | Fixed | Build script stamps `_meta` in memory only. `data.json` on disk is never written by the build. |
| Daily backup only | Covered | Git provides full history. Build script saves daily backup to `backups/` and prunes after 30 days. |
| Historical chart data incomplete | Largely resolved | `refetch_historical.py` restored all charts except genuine data voids (CHN, IND, BRA, RUS gaps where no free source exists). |
| Stale or missing market data | Partially resolved | 4 automatable metrics will be fetched daily by `fetch_market_data.py` (not yet built). 4 data-void metrics display as "not available" rather than showing stale values. |
| Manual story maintenance burden | Being resolved | `update_stories.py` (not yet built) will automate story rewrites for any metric that moves past threshold. |

---

### Key shell locations

| Thing | Location |
|---|---|
| `.tt-metric-story` CSS | Line 165 |
| `metricStories` object declaration | Line 5605 |
| `metricStories` populated from data | Line 5637 |
| `renderMTT()` function | Line 6542 |
| Metric story HTML built | Line 6581-6582 |
| Full tooltip render string | Line 6589 |
| `historicalData` populated from `_frozen_historical` | Line 5638 |
| `window.__MACROSNAPS_DATA__` injected by build | Before `</head>` in built output |

---

### Pending work (priority order)

1. **Grey out 4 data-void metrics in the UI.** Equity Vol, Corp Spread, Sov CDS, and FX Vol should display as "not available" with a tooltip: "no reliable free data source - will be added post-launch." This is a UI session - upload `LIVING_BRIEF.md` + `macrosnaps-shell.html`.

2. **Build `fetch_market_data.py`.** Pulls Stock Market YTD, 10Y Bond Yield, Yield Curve, and FX pairs from Yahoo Finance and FRED. Writes directly into `data.json`. Skips data-void metrics. Design should mirror `refetch_historical.py`. Requires FRED_API_KEY in .env. This is a tooling session.

3. **Build `update_stories.py`.** Diffs data.json against last git commit. Applies per-metric thresholds to decide what warrants a rewrite. Calls Claude API (claude-sonnet-4-20250514) for affected metrics and writes all three story levels back into data.json. Requires ANTHROPIC_API_KEY in .env. This is a tooling session.

4. **Build `print_snapshot.py`.** Uses Playwright to open the built HTML file, loops through each country, expands it, and captures a full-height PDF. Output is a dated file in `snapshots/` (e.g. `macrosnaps-2026-03-09.pdf`). Audience level hardcoded to expert. For personal use only, not a public feature. Run optionally after the daily ritual. Requires `pip3 install playwright` and `playwright install chromium`.

5. **Post-launch:** revisit architecture if a second person joins to update data daily.

---

### Known bug: Weather Map out of sync with sheet values

Discovered 2026-03-10. The GDP Growth Weather Map tooltip (and equivalent CPI, Unemployment, Budget Deficit, Current Account weather maps) shows values from `_frozen_weatherGrid` inside `data.json`, not from the live metric values updated by `sync_sheet.py`. This means the Weather Map can show different numbers than the country card for the same metric. Example: USA GDP showed +2.4% in the Weather Map but +2.2% on the country card after a sheet sync.

**Root cause:** `assembleWeatherGrid()` in the shell reads from `gdpAllCountries` etc., which are populated from `c._frozen_weatherGrid` (line 5639 of shell). `sync_sheet.py` updates the live metric values but never touches `_frozen_weatherGrid`.

**Fix options:**
- Option A (tooling): have `sync_sheet.py` also update the 2026F column of `_frozen_weatherGrid` for each country when it writes a metric value.
- Option B (UI): make `assembleWeatherGrid()` read the current year value from the live metrics instead of `_frozen_weatherGrid`, keeping historical years from the frozen data.

Option B is cleaner but requires care to preserve the historical year columns. This is a tooling + UI session. Upload `LIVING_BRIEF.md` + `macrosnaps-shell.html` + `data.json` + `sync_sheet.py`.

Add to pending work list as item 5, before the post-launch note.
