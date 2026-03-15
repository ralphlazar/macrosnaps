# MacroSnaps - Living Brief
Last updated: March 15, 2026 (Session 14: tooling session. Root cause of RUS USD column bug found and fixed across `sync_sheet.py` and `macrosnaps-shell.html`. Daily refresh command confirmed stable. No open pipeline issues.)

Session 14 changes in detail:
(1) Root cause diagnosed: `sync_sheet.py` `run_market_sync()` was writing market values as top-level keys on the country object (e.g. `country["stock_market_ytd"]`) rather than into `country["metrics"]["market"]` with proper display keys. The shell reads exclusively from `co.metrics.market[...]`. Values were being written to the wrong location in data.json entirely.
(2) `sync_sheet.py` — three fixes:
  - `MARKET_COL_MAP` now maps sheet column names to display keys matching `metrics.market` (e.g. `"Stock_Market_YTD_USD"` → `"Stock Market YTD (USD)"`).
  - `run_market_sync()` now writes into `country["metrics"]["market"]` with correct display keys, respecting existing `{value: ..., story: ...}` dict structure where present.
  - Added `_jan1_index_from_rows()` and `_compute_local_ytd()` helpers. Local YTD is now computed from index history in the sheet (latest / jan1 - 1) and written to `metrics.market["Stock Market YTD"]`. The sheet has no `Stock_Market_YTD` column — this was always a computed value.
  - Added None-guard: blank sheet cells never overwrite existing non-null values (protects CHN/IND/BRA/RUS bond yields which have no FRED series).
  - `sh.worksheet()` call wrapped in retry-with-backoff (same pattern as `get_all_values_with_retry`) to handle 429 quota errors.
(3) `macrosnaps-shell.html` — no net change. A fallback coalesce (`??`) was briefly added and then removed once the real fix was confirmed.
(4) Bond yields for CHN (2.40%), IND (6.73%), BRA (13.80%), RUS (13.5%) were accidentally wiped by an intermediate bad run and manually restored via one-off inline Python before the None-guard was in place.
(5) Daily refresh command confirmed clean:
  `python3 update_market_sheet.py && sleep 60 && python3 sync_sheet.py --market --apply && python3 build.py --apply`

Session 13 changes in detail:
(1) `update_market_sheet.py`: added `fetch_moex_index()` which hits the MOEX public REST API (`iss.moex.com/iss/engines/stock/markets/index/securities/IMOEX/candles.json?interval=31`) for monthly candles. For RUS only, equity is now sourced from MOEX instead of yfinance (IMOEX.ME unreliable post-sanctions). `_moex_jan1` internal key carries the Jan-1 base level, bypassing sheet-history lookup. `Stock_Market_YTD_USD` is now computed for RUS using the MOEX local return adjusted by RUB/USD from the sheet.
(2) `sync_sheet.py`: `--market` flag was silently ignored (it was never implemented). Added `run_market_sync()` function. `--market` and `--apply` (macro) modes are now mutually exclusive branches in `main()`. Macro path untouched.
(3) `backfill_rus_index.py`: one-off script (keep for re-use). Fetched 6,554 MOEX daily candles from 2000-01-01. 200 blanks remain (genuine non-trading days). Script is idempotent — only writes to blank cells.

Last session note (Session 12): UI session. All changes in macrosnaps-shell.html only. (1) Deleted computeFxYtd and computeUsdReturn — USD toggle now reads co.metrics.market['Stock Market YTD (USD)'] directly. (2) Stock Market YTD ranking redesigned: two columns (Local + USD) always visible side by side, both sortable, plus sortable Countries column. (3) Hover tooltip suppressed on touch devices via @media(hover:none). (4) Logo click resets to GDP Growth home state. (5) DISPLAY_NAMES map added: 'United Kingdom'->'UK', 'United States'->'USA' in all ranked and grid table renders. (6) Value columns thinned (width:58px) and centre-aligned. All dead CSS removed.

Last session note (Session 11): tooling session. Stock_Market_YTD_USD pipeline complete. update_market_sheet.py now appends a 7th column to each MARKET-STATS tab. 11 countries had values; RUS blank (no equity data at the time).

Previous session note (Session 10): Full homepage redesign across two sessions (9 and 10). All changes are in macrosnaps-shell.html only. Key changes:

(1) Default landing page is now a GDP Growth weather map table. Globe is hidden by default, lazy-initialised on first click of the Globe toggle in the top bar. Rankings/Globe toggle added to top-bar.

(2) Weather table: 12 countries x 7 columns (2020-2026F). Icons only (no numbers in cells). Rows are clickable to open country card. Columns and country header are sortable by click. Default sort is descending by 2026F column. Icon hover shows the data value as a floating tooltip.

(3) Metric picker: clicking the "GDP Growth" title opens a dropdown of all metrics in two groups - Macro (GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account - all have full 7-year weather grid using existing weather functions and data objects) and Markets (Policy Rate, Stock Market YTD, 10Y Bond Yield, Yield Curve - show a single ranked column of current values).

(4) USD equity toggle removed. Stock Market YTD now shows Local and USD columns simultaneously, both sortable.

(5) Geo filter (All 12/G7/BRICS+) was removed. Tagline "Like learning a language" was removed.

(6) Colour scheme changed to deep navy: body #05080f, cards/overlays #0d1120, floating panels rgba(10,14,26,.98), chart hover tooltips rgba(8,12,24,.97). Globe inner sphere updated to match.

Previous session note (Session 8): extended all tooltip charts to start from Jan 2000. (1) sync_monthly_historical.py and sync_market_historical.py: START_DATE changed to 2000-01-01. (2) macrosnaps-shell.html: histMonthlyLabels IIFE now anchors at Jan 2000 and counts forward to _meta.generated; isAnnual detection fixed to use cfg.type==='bar' instead of cfg.annual; slice direction fixed - full array uses slice(0,n) left-anchored, range buttons use slice(-n) right-anchored; annual charts have no range buttons and always show full array; both All buttons use data-r="0"; initial renders pass null; renderCommodityMonthlyChart treats falsy rangeMonths as full array; fallback title updated to "History since 2000". (3) sync_sheet.py --apply run to restore annual arrays to 27 points (2000-2026F).

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

- Always present a plan before writing any code or making any changes. Wait for explicit confirmation ("go") before proceeding.
- Make surgical, minimal changes. Do not refactor, rename, or reorganise anything not directly related to the task.
- UK English spelling throughout all story content (realise, colour, behaviour, etc.).
- When in doubt, ask. Do not assume.

### ...to here

---

## PART 2 - PROJECT REFERENCE

### Site

- Live URL: https://ralphlazar.github.io/macrosnaps
- Repo: GitHub Pages, branch `master`, root directory
- Built file: `macrosnaps-globe.html` (standalone, self-contained, ~936 KB)

---

### Architecture

Three source files assemble into one output:

| File | Role |
|------|------|
| `data.json` | All content: metrics, stories, commodities, historical arrays |
| `macrosnaps-shell.html` | All UI: HTML, CSS, JS. References `data.json` via a placeholder |
| `build.py` | Assembles output: inlines data.json into shell, validates schema, diffs changes, auto-commits |

`macrosnaps-globe.html` is build output. Never edit it directly.

---

### Countries

12 countries in this order: USA, CAN, GBR, DEU, FRA, ITA, JPN, CHN, IND, BRA, RUS, ZAF

---

### Metrics

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate

**Market (5):** Stock Market YTD, Stock Market YTD (USD), 10Y Bond Yield, Yield Curve, FX (country-specific key per country)

**Market metrics in data.json** live at `country.metrics.market[display_key]` where display_key is the exact string above (e.g. `"Stock Market YTD (USD)"`). These are written by `sync_sheet.py --market --apply`.

---

### Data sources

**Annual forecasts (macro card values):**
- Source: Ralph's Google Sheet "Macro-stats" (ID: `1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo`)
- Script: `sync_sheet.py --apply`
- Writes: `metrics.macro[key].value` (2026F card value) and `_frozen_historical[key].v` (annual array, bar chart) for GDP Growth, Budget Deficit, Current Account only

**Daily market data:**
- Source: MARKET-STATS Google Sheet (ID via `MARKET_STATS_SHEET_ID` env var)
- Columns: `Date`, `Stock_Market_Index`, `FX_Rate`, `Bond_Yield_10Y`, `Bond_Yield_3M`, `Yield_Curve`, `Stock_Market_YTD_USD`
- Script: `update_market_sheet.py` appends today's row; `sync_sheet.py --market --apply` reads latest row and writes to `metrics.market`
- Local YTD computed in `sync_sheet.py` from `(latest_index / jan1_index - 1) * 100` using sheet history
- USD YTD computed in `update_market_sheet.py` as `(index_today/jan1_index) * (jan1_fx/fx_today) - 1`
- RUS equity: MOEX REST API (not yfinance). `fetch_moex_index()` in `update_market_sheet.py`
- Permanent blanks (no FRED series): CHN/IND/BRA/RUS bond yields. Values hand-maintained in data.json. The None-guard in `sync_sheet.py` prevents blank sheet cells from overwriting them.

**Monthly actuals (story context only):**
- Source: MACRO-MONTHLY Google Sheet
- Script: `sync_monthly_actuals.py`
- Writes: `monthly_actuals` field only. Never touches metrics.

---

### Daily refresh command

```bash
python3 update_market_sheet.py && sleep 60 && python3 sync_sheet.py --market --apply && python3 build.py --apply
```

The `sleep 60` prevents Sheets API 429 quota errors between the two scripts.

---

### Key data.json paths

```
data.countries[code].metrics.macro[metric_name].value       ← card display value (string)
data.countries[code].metrics.macro[metric_name].story       ← per-metric story object
data.countries[code].metrics.market[metric_name]            ← float or {value, story}
data.countries[code]._frozen_historical[metric_name].v      ← annual array (bar chart)
data.countries[code].monthly_actuals                        ← monthly context only
data.commodities.items[n].price                             ← commodity price
data._meta.generated                                        ← build date stamp
```

---

### Known permanent data gaps

| Country | Metric | Reason |
|---------|--------|--------|
| CHN, IND | Unemployment | No reliable monthly FRED series |
| CHN, IND, BRA, RUS | 10Y Bond Yield | No FRED series — values hand-maintained |
| CHN, IND, BRA, RUS | 3M Yield / Yield Curve | No FRED series — always blank |
| RUS | Equity (yfinance) | IMOEX.ME delisted post-sanctions — MOEX REST API used instead |

---

### Story levels

Three levels per metric per country: `beginner`, `moderate`, `expert`. 168 per-metric stories (12 countries × 6 macro metrics × 1 per level... wait, 3 levels = 216 metric stories + 9 commodity stories × 3 levels = 27 commodity stories). Country card stories (top-level) are separate and updated daily by `update_headlines.py`.

---

### Scripts summary

| Script | Trigger | What it does |
|--------|---------|--------------|
| `update_market_sheet.py` | Daily | Fetches equity/FX/yields, appends row to MARKET-STATS sheet |
| `sync_sheet.py --market --apply` | Daily | Reads latest MARKET-STATS row, writes to `metrics.market` in data.json |
| `sync_sheet.py --apply` | When forecasts change | Reads Macro-stats sheet, writes macro card values and historical arrays |
| `sync_monthly_actuals.py` | Monthly | Reads MACRO-MONTHLY sheet, writes `monthly_actuals` |
| `update_headlines.py` | Daily | Calls Claude API, writes country and global stories to draft JSON |
| `update_stories.py` | On metric change | Diff-driven per-metric story rewrites |
| `update_commodity_stories.py` | On price threshold | Commodity story rewrites |
| `build.py --apply` | Daily | Assembles globe.html, validates, diffs, auto-commits, pushes |

---

### Shell key facts (macrosnaps-shell.html)

- Market metrics read from `co.metrics.market[display_key]` — exact string match required
- `Stock Market YTD (USD)` is read directly at line ~6230: `co.metrics.market['Stock Market YTD (USD)']`
- Local YTD: `co.metrics.market['Stock Market YTD']`
- `_flattenMetrics()` flattens `{value, story}` objects to bare values for the shell
- `DISPLAY_NAMES` map: `'United Kingdom' → 'UK'`, `'United States' → 'USA'`
- Weather icon computed live from GDP Growth thresholds: ≥3% ☀️, ≥0% ☁️, <0% ⛈️
- `metricDisplayLabels`: `'Policy Rate' → 'Policy Rate (year-end)'`
- Globe is lazy-init (WebGL only on first toggle click)

---

### Pending work (priority order)

1. **Fix JPN inflation gap (Session 7).** `CPALTT01JPM657N` stops June 2021. Replace with `JPNCPIALLMINMEI` (OECD index level, not pre-computed YoY) in `populate_monthly_actuals.py` and `update_monthly_actuals.py`. Add `.pct_change(12) * 100` transform before writing. Re-run JPN inflation backfill only. Upload LIVING_BRIEF.md + both monthly actuals scripts.

1. **Apply USA sheet changes.** `sync_sheet.py` preview on March 11 showed USA CPI 3.1% -> 2.3% and Unemployment 4.4% -> 4.2%. These were never applied. Run: `python3 sync_sheet.py --apply && python3 update_stories.py && python3 build.py`

1. **GDP Growth stories audit.** CAN, FRA, ITA, BRA confirmed mismatches between story text and current values. Run a targeted stories session for these four countries (upload LIVING_BRIEF.md + data.json, use Part 1B prompt).

1. **Build `print_snapshot.py`.** Uses Playwright to open the built HTML file, loops through each country, expands it, and captures a full-height PDF. Output is a dated file in `snapshots/` (e.g. `macrosnaps-2026-03-09.pdf`). Audience level hardcoded to expert. For personal use only, not a public feature. Requires `pip3 install playwright` and `playwright install chromium`.

1. **Post-launch:** revisit architecture if a second person joins to update data daily.

1. **Post-launch:** replace fake contact form in "Ping Me" footer with a real form service (Formspree or similar). Currently the form shows a success message without sending anything.

1. **Post-launch:** consider user alert emails (daily or weekly digest for chosen countries/metrics/commodities). Requires server-side infrastructure. A simple early version could use Buttondown or Mailchimp for a subscriber list before building anything custom.

---

**Global stories narrative formula**

The three global story cards always follow a fixed three-act arc:
- Card 1 - Today's Story: the dominant macro event of the day
- Card 2 - Biggest Movers: which markets, currencies, or economies are reacting and how
- Card 3 - The Connection: what ties cards 1 and 2 together, the "so what" for the global picture

All three levels (beginner, moderate, expert) tell the same arc at different depths. The icon and label are identical across levels. This formula is enforced in the `build_global_system()` prompt in `update_headlines.py`.

---

### Editorial principle: forecasts vs stories

MacroSnaps has two distinct layers of truth that must not be conflated:

**Forecast values** (source: Ralph's Google Sheet) are annual consensus views for 2026. They drive the metric value displayed on each card and the weather icon. Policy Rate is the year-end forecast. These are proprietary and intentionally stable.

**Stories** should be written off recent data and trends, not off the forecast values. Monthly CPI prints, quarterly GDP flash estimates, central bank decisions, weekly jobless claims - this is the live texture that makes stories worth reading. A story that just restates the annual forecast number adds no value.

The correct approach: stories comment on what is actually happening right now. If recent data is tracking ahead of or behind the annual forecast, the story can note that tension briefly (e.g. "February CPI came in at 2.6%, above the Fed target, but full-year inflation is still expected to settle at 2.3% as base effects kick in mid-year"). But the forecast is not the anchor of the story - recent data is.

**Architectural constraint: write path separation.** `sync_sheet.py --apply` writes only annual forecast fields (GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account, Policy Rate arrays and card values). `sync_monthly_actuals.py` writes only the `monthly_actuals` field. These two scripts must never touch each other's fields. This is currently enforced by construction but must be preserved in any future refactor. No other script writes to `monthly_actuals`.

---

**Do not position against Bloomberg or data terminals.** The audience is professionals and informed non-professionals who want a daily briefing at the depth they choose, not a research platform. The competition is a good morning read, not a data subscription.
