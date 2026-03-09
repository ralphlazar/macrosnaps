# MacroSnaps - Living Brief
Last updated: March 9, 2026 (end of session)

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

Think before building. On any non-trivial change, share your approach and flag concerns before writing code. Wait for me to say "go."

Make surgical edits. Change the minimum needed. Do not rewrite surrounding code unless it is broken.

After each edit, briefly explain what changed and why.

If something feels architecturally wrong, say so before doing it.

Never present a task as done until the build has run successfully and the output has been copied to the outputs folder.

**Session rhythm**

We work in focused chunks. At the end of each natural unit of work (a feature shipped, a content block done, a bug fixed), before starting the next thing, you update `LIVING_BRIEF.md` and make it available for download. Do not wait until the context window is full. Write it while everything is fresh.

**Writing style (apply to every response)**

Write in plain, natural English. Do not use em dashes or en dashes. Only use a standard hyphen (-) if a dash is genuinely needed. Prefer commas, periods, or parentheses instead. Before outputting any response, scan it for the characters and. If found, rewrite those sentences. Output only the final corrected version. This rule applies to all responses including code comments and story content written into data.json.

**What I am working on today:**

[describe your task here]

### ...to here

---

## PART 2 - PROJECT REFERENCE

---

### What the project is

MacroSnaps is a daily global macro and markets dashboard. It shows key economic metrics, market data, stories, and historical charts for 12 countries and 9 commodities. It is designed for three audience levels: beginner, moderate, and expert. The user toggles between levels and everything in the UI adapts - stories, terminology, glossary definitions.

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

This writes the changes to `data.json`.
```bash
python3 sync_sheet.py --apply
```

**Step 4. Build the output file**

This validates `data.json`, assembles `macrosnaps-globe.html`, and saves a dated backup.
```bash
python3 build.py
```
The build must say `BUILD SUCCESSFUL` before you continue. If it fails, do not push.

**Step 5. Commit and push**

```bash
git add -A && git commit -m "Sheet sync $(date +%Y-%m-%d)"
git push origin master
```

**Step 6. Verify the live site**

Wait about 60 seconds, then open:
```
https://ralphlazar.github.io/macrosnaps/macrosnaps-globe.html
```

That is it. Five steps from terminal to live site.

---

### What the Google Sheet controls

The sheet is the single source of truth for the 6 macro metrics per country. Update these values in the sheet, then run the daily ritual above.

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
Market metrics (yields, spreads, FX, vol, equities) and commodity data are still updated manually in `data.json`. So are all stories, metricBriefs, and historical chart data.

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

### Current content state (March 9, 2026)

**Per-metric stories (beginner / moderate / expert)**
- USA: 14/14 complete
- CAN: 14/14 complete
- GBR: 0/14 - not started
- JPN: 0/14 - not started
- DEU: 0/14 - not started
- FRA: 0/14 - not started
- ITA: 0/14 - not started
- CHN: 0/14 - not started
- IND: 0/14 - not started
- ZAF: 0/14 - not started
- BRA: 0/14 - not started
- RUS: 0/14 - not started

**Other content (all 12 countries)**
- Country-level stories (3 bullets per level): complete for all 12
- metricBriefs (short summaries per metric): complete for all 12
- fxRegime descriptions (3 levels): complete for all 12

**Global stories (March 9, 2026)**
- Slot 1: Oil Crosses $100 for First Time Since 2022 (Saudi cuts + Hormuz blockade)
- Slot 2: Stock Markets Tumble, Global Risk-Off (Nikkei -5%, VIX 30, DXY 99.7)
- Slot 3: US February Payrolls Shock: -92K, Unemployment 4.4%

---

### Historical chart data state (March 9, 2026)

`_frozen_historical` was restored using `refetch_historical.py`. Current state:

| Country | Charts populated | Notes |
|---|---|---|
| USA | 13/14 | Yield Curve gap: FRED date alignment issue |
| CAN | 14/14 | |
| GBR | 13/14 | Yield Curve populated |
| JPN | 14/14 | |
| DEU | 13/14 | Yield Curve gap: FRED date alignment issue |
| FRA | 13/14 | Yield Curve gap: FRED date alignment issue |
| ITA | 14/14 | |
| CHN | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source |
| IND | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source |
| ZAF | 12/14 | Unemployment: no monthly source; Yield Curve populated |
| BRA | 12/14 | 10Y Bond Yield, Yield Curve: no free source |
| RUS | 10/14 | GDP Growth, Unemployment, USD/RUB discontinued post-2022 sanctions |

Metrics that cannot be restored for any country (no free public source): Equity Vol, Corp Spread, Sov CDS, FX Vol, Budget Deficit.

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

---

### How metric stories work

Stories live in `data.json` inside each metric entry as a `story` object with `beginner`, `moderate`, and `expert` keys.

At load time the shell reads these into the `metricStories` object (line 5605 of shell).

When a user clicks a metric, `renderMTT()` (line 6542) builds the tooltip. The story appears inline between the value and the chart, with no header label. CSS class is `tt-metric-story` (line 165 of shell).

The tooltip order is: metric name, country + value, story, chart, explanation/bluf, FX regime (if applicable), compare button.

---

### Architecture decisions and why

**Google Sheet for macro metrics.** The sheet holds the 6 macro metrics per country (GDP, CPI, unemployment, budget deficit, current account, policy rate). `sync_sheet.py` pulls from the sheet and writes `data.json`. The sheet is updated manually with year-end consensus forecasts. Market metrics remain in `data.json` and are updated manually.

**No CMS.** Pre-launch solo workflow. JSON plus build script is faster to iterate with than any external system.

**GitHub Pages for hosting.** Repo is public at https://github.com/ralphlazar/macrosnaps. Deploy from master branch, root folder. The built HTML file is self-contained (data inlined) so no build step is needed on the server side.

**Git for version history.** Commit after every feature or meaningful change.

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
| Historical chart data incomplete | Largely resolved | `refetch_historical.py` restored 95 of a possible 107 charts. Remaining 12 gaps are genuine data voids with no free source. |
| .DS_Store committed | Fixed | Added to `.gitignore` and removed from git history. |

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

1. **Add per-metric stories to 10 remaining countries.** 10 countries x 14 metrics x 3 levels = 420 story fields. Do one country per content session. Next up: GBR.

2. **Add alert scanner as hidden page at `#alerts`.** Full instructions below.

3. **Resolve 3 Yield Curve gaps (USA, DEU, FRA).** The FRED short rate series for these countries returns data starting in the 1960s while the 10Y series starts later, causing a date overlap failure. Fixable with a better short rate series ID or a different date windowing approach in `refetch_historical.py`.

4. **Post-launch:** revisit architecture if a second person joins to update data daily.

---

### Alert scanner: detailed build instructions (UI session)

**Session type:** UI session. Upload `LIVING_BRIEF.md` + `macrosnaps-shell.html`.

**Do NOT upload** `macrosnaps-alerts.jsx`. The JSX file is React. The shell is vanilla JS. Claude must translate, not copy-paste.

**Goal**

Add a hidden page to the existing app accessible at:
```
https://ralphlazar.github.io/macrosnaps/macrosnaps-globe.html#alerts
```
When the user navigates to that URL, the main content area is replaced with the MacroSnaps alert scanner. The globe and all normal UI is hidden. Navigating away from `#alerts` (or hitting back) restores the normal app.

This page is intentionally undiscoverable. No link to it in the nav. No mention of it in the UI. Just a bookmarkable URL for internal use.

**Exact prompt to give Claude**

> Add a hidden alert scanner page to the shell, accessible only at `#alerts`. When the URL hash is `#alerts`, hide the main app content and show the scanner UI instead. When the hash changes away from `#alerts`, restore the normal app. Translate the scanner logic from the reference below into the shell's existing vanilla JS and CSS pattern. No new libraries, no React, no imports.
>
> Here is the reference implementation to translate (not copy): [paste the full contents of `macrosnaps-alerts.jsx` below this line]

**What Claude needs to build inside the shell**

A hash-change listener:
```javascript
window.addEventListener('hashchange', handleHashChange);
window.addEventListener('load', handleHashChange);

function handleHashChange() {
  if (window.location.hash === '#alerts') {
    showAlertsPage();
  } else {
    hideAlertsPage();
  }
}
```

A `showAlertsPage()` function that hides the normal app container and injects or reveals the alerts div.

A `hideAlertsPage()` function that restores the normal app container.

The full scanner UI rendered as a regular DOM div with inline styles, matching the dark terminal aesthetic from the JSX reference.

The API call translated to vanilla JS fetch. The critical headers are:
```javascript
headers: {
  "Content-Type": "application/json",
  "anthropic-version": "2023-06-01",
}
```
Model: `claude-sonnet-4-20250514`. Tool: `{ type: "web_search_20250305", name: "web_search" }`.

Response parsing: filter `data.content` for blocks where `b.type === "text"`, take the first one, strip any markdown fences, then `JSON.parse`. Do not assume `data.content[0]` is the text block - this will break when web search is active.

**Things to flag to Claude before it starts**

- Tell Claude to share its approach before writing any code and wait for you to say go.
- Ask Claude to confirm which element is the main app container (it needs to find the right div to hide/show).
- The scanner UI should be appended to `document.body`, not inserted inside the main app container, so hiding the app container does not affect it.
- The `#alerts` page should have its own back link: a small `← MacroSnaps` text link in the top left that sets `window.location.hash = ''` to return to the main app.

**After the build**

Run `python3 build.py` and confirm `BUILD SUCCESSFUL`. Then:
```bash
git add -A && git commit -m "Add hidden alerts page at #alerts"
git push origin master
```
Test by navigating to `macrosnaps-globe.html#alerts` in Safari locally before pushing. Confirm SCAN NOW fires and returns results. Confirm navigating to `macrosnaps-globe.html` (no hash) restores the normal globe.
