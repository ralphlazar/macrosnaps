# MacroSnaps - Living Brief
Last updated: March 15, 2026 (Session 17: Tooling/pipeline session. Full daily ritual run. Audit of Downloads/macrosnaps directory. Security fix: stale API key file deleted + scrubbed from git history. Sort order fix in macrosnaps-shell.html.)

Session 17 changes in detail:

(1) **Security — stale API key file deleted.** File `.envsk-ant-api03-...` (accidentally created by `touch $ANTHROPIC_API_KEY`) was deleted and scrubbed from git history using `git filter-repo`. Key was already rotated in a prior session. `.env.save` also deleted (stale shell backup of `.env`).

(2) **Sort order fix in macrosnaps-shell.html.** When switching metric via the dropdown, `_whSortCol` was being reset to `6` or `1` (a year column), overriding nominal GDP order. Fixed: line 6428 now sets `_whSortCol = -1` on metric change. All ranking metrics (Inflation, Unemployment, etc.) now open in nominal GDP order, consistent with the homepage and logo-click behaviour. `_whSortAsc = false` also removed from that block (redundant).

(3) **Daily ritual completed successfully.** All steps run in order:
- `fetch_market_data.py` — 41 updated, 7 permanent failures (CHN/BRA/RUS yields, RUS equity), 9 commodities green. Sunday run = Friday closing prices, as expected.
- `sync_commodity_data.py --apply` — 9/9 updated, change values flipped from YTD to day-over-day correctly.
- `update_commodity_stories.py` — no rewrites triggered (all within threshold).
- `update_headlines.py` — 13/13 OK in 214s (one rate limit pause, auto-recovered). Draft reviewed and applied.
- `build.py --apply` — assembled, validated, committed, pushed.

(4) **Redundant files identified** in Downloads/macrosnaps (not yet deleted — confirm before removing):
- Safe to delete: `__pycache__/`, `.env.save` (done), stale API key file (done), `refetch_historical.py` (one-off, complete), `rebackfill_jpn_inflation.py` (superseded)
- Probably redundant (check before deleting): `sync_market_historical.py`, `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`, `headline_review.html`

---

Session 16 changes in detail (all in macrosnaps-shell.html only):
(1) Logo click from Globe view now calls switchToRankings() before renderMetricTable() — navigates back to homepage correctly from any view.
(2) Nav simplified to logo-only. Rankings, Globe, and Commodities buttons hidden via `.view-toggle{display:none}`. All button code intact — do not delete. Globe remains lazy-init, accessible by restoring display if needed post-launch.
(3) Commodities FAB: `<button id="btnCommFab">🛢️</button>` added fixed bottom-right (bottom:72px, right:20px). Amber emoji, cyan border, wired to switchToCommodities(). This is the sole entry point to the Commodities card from the homepage.
(4) Yield Curve and 10Y Bond Yield rankings: ranked table now renders `num + cfg.unit` (parsed float + config unit string) instead of raw string. Eliminates mixed bps/no-bps and %/no-% inconsistency. Applies to all ranked metrics.
(5) Mobile rankings grid: columns 0–1 (2020–2021) hidden via `.wh-col-old{display:none}` at ≤768px breakpoint. Shows 5 years (2022–2026F) on mobile, all 7 on desktop.
(6) Per-metric weather strip added to country cards. 7 icons (2020–2026F) shown inline right of the metric value inside `.m-val-row` (flex, space-between). Appears on all 5 hasGrid macro metrics (GDP Growth, Inflation CPI, Unemployment, Budget Deficit, Current Account). Not on Policy Rate or market metrics. 2026F icon has `opacity:.6` and tiny `F` subscript. Desktop: CSS `::before` hover tooltip showing `2024 · +2.5%`. Mobile: tap strip to show/dismiss year+value overlay. Tapping strip does not open the metric tooltip.
(7) Icon rule (FIXED, do not change): all weather icons site-wide must use the `.wh-icon` CSS filter pattern — a single ☀️ emoji styled via `filter: brightness/contrast/saturate`. Classes: `.wh-icon.sunny` (no filter), `.wh-icon.cloudy` (desaturated dim), `.wh-icon.stormy` (near-black with drop-shadow). This is the only permitted icon rendering method. Per-metric strip uses `☀️/☁️/⛈️` with `.wh-icon cls` wrapper — correct emoji per state, consistent with ranking tables.
(8) Country cards: `Stock Market YTD (USD)`, `Stock Market Index`, and `FX Rate` excluded from card market metrics via `CARD_MARKET_EXCLUDE` set. Cards show: Stock Market YTD (local), FX cross vs USD, 10Y Bond Yield, Yield Curve, Policy Rate only.
(9) Navy palette applied everywhere (body, cards, overlays, top bar, panels):
  - `#05080f` → `#091426` (body/page background)
  - `#0d1120` → `#0e1d35` (cards, comm items)
  - `rgba(10,14,26,...)` → `rgba(9,20,38,...)` (all panels/overlays/tooltips)
  - `#2a2e3d` → `#243650` (card borders)
(10) Default rankings sort changed to nominal GDP order via `GDP_NOMINAL_ORDER` constant. `_whSortCol` initialised to `-1` (new state meaning nominal order). Handled in both `renderGridTable` and `renderRankedTable` sort functions. Logo click also resets `_whSortCol = -1`. User column-header clicks still override to dynamic sort. Nominal order: USA, CHN, DEU, JPN, IND, GBR, FRA, ITA, CAN, BRA, RUS, ZAF.
(11) Compare All Countries and ☀️☁️☁️ Over Time buttons removed from macro metric tooltips. Both buttons now only appear for market metrics (`d.section === 'market'`). Rationale: weather strip and homepage grid make these redundant for macro. Compare button listener guarded with null check.

---

Session 15 changes in detail:
(1) New tab `Commodities` in MARKET-STATS sheet. Columns: `Date | WTI Crude | Brent Crude | Natural Gas | Gold | Silver | Copper | Wheat | Corn | Soybeans`. Daily close prices. Actual date coverage starts 2000-07-17 (earliest yfinance has for these continuous futures contracts — Brent starts 2007-07-30).
(2) New script `backfill_commodity_data.py` — one-time only, already run. Pulled full history via yfinance, wrote 6,466 rows to the sheet in batches of 500. Do not re-run unless rebuilding the tab from scratch.
(3) Modified `fetch_market_data.py` — after `process_commodities()`, now calls new `append_commodity_row_to_sheet()` which appends today's prices as a new row. Idempotent (skips if today's row already present). Failure is non-fatal (logs warning, never blocks data.json write). Requires gspread + google-auth.
(4) New script `sync_commodity_data.py` — reads the `Commodities` tab via gspread, derives three fields per commodity and writes to data.json: `price` (last row), `change` (% diff last two rows, day-over-day), `spark` (monthly last-close, last 120 months). Preview by default; `--apply` to write.
(5) spark: upgraded from 12 → 120 points (10 years of monthly last-closes). Tooltip charts now have full history.
(6) change: now day-over-day (e.g. Gold +0.2%) not YTD. Previous YTD values (e.g. +17.3%) were replaced on first sync_commodity_data.py --apply run.
(7) Daily ritual is now:
  ```
  python3 fetch_market_data.py
  python3 sync_commodity_data.py --apply
  python3 update_commodity_stories.py
  python3 build.py
  ```

Session 14 changes in detail:
(1) Root cause diagnosed: `sync_sheet.py` `run_market_sync()` was writing market values as top-level keys on the country object rather than into `country["metrics"]["market"]` with proper display keys.
(2) `sync_sheet.py` — three fixes: MARKET_COL_MAP corrected; run_market_sync() writes to correct location; _jan1_index_from_rows() and _compute_local_ytd() helpers added; None-guard added; worksheet() call wrapped in retry-with-backoff.
(3) Bond yields for CHN (2.40%), IND (6.73%), BRA (13.80%), RUS (13.5%) hand-maintained in data.json. None-guard protects them.

Session 13 changes in detail:
(1) `update_market_sheet.py`: RUS equity now sourced from MOEX REST API via fetch_moex_index(). Stock_Market_YTD_USD computed for RUS using MOEX local return adjusted by RUB/USD.
(2) `sync_sheet.py`: --market flag implemented via run_market_sync(). --market and --apply are mutually exclusive branches.
(3) `backfill_rus_index.py`: one-off script, keep for re-use. 6,554 MOEX daily candles from 2000-01-01.

Session 12: UI session. (1) computeFxYtd and computeUsdReturn deleted. (2) Stock Market YTD ranking: Local + USD columns always visible, both sortable. (3) Hover tooltip suppressed on touch devices. (4) Logo click resets to GDP Growth home state. (5) DISPLAY_NAMES map added. (6) Value columns thinned and centre-aligned.

Session 10–11: Full homepage redesign. Default landing page is GDP Growth weather grid. Globe lazy-init. Metric picker added. USD equity toggle removed.

Session 8: All tooltip charts extended to Jan 2000.

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
- Script: `fetch_market_data.py` fetches and writes to data.json directly (yfinance + FRED); also appends today's commodity row to MARKET-STATS `Commodities` tab
- Local YTD computed in `fetch_market_data.py` from Jan 1 index baseline
- RUS equity: MOEX REST API (not yfinance). `fetch_moex_index()` in `fetch_market_data.py`
- Permanent blanks (no FRED series): CHN/IND/BRA/RUS bond yields. Values hand-maintained in data.json. None-guard prevents blank values from overwriting them.

**Commodity daily prices:**
- Source: MARKET-STATS Google Sheet, `Commodities` tab (same sheet as daily market data)
- Columns: `Date | WTI Crude | Brent Crude | Natural Gas | Gold | Silver | Copper | Wheat | Corn | Soybeans`
- History from: 2000-07-17 (yfinance limit for continuous futures; Brent from 2007-07-30)
- Script: `fetch_market_data.py` appends today's row; `sync_commodity_data.py --apply` reads tab, derives price/change/spark, writes to data.json
- `price`: last row value. `change`: % diff last two rows (day-over-day). `spark`: monthly last-close array, last 120 months.
- Backfill script: `backfill_commodity_data.py` — one-time, already run. Do not re-run.
- Weekend note: Sunday runs fetch Friday's closing prices. Monday's day-over-day change = Friday→Monday move. Correct behaviour.

**Monthly actuals (story context only):**
- Source: MACRO-MONTHLY Google Sheet
- Script: `sync_monthly_actuals.py`
- Writes: `monthly_actuals` field only. Never touches metrics.

---

### Daily ritual

```bash
python3 fetch_market_data.py
python3 sync_commodity_data.py --apply
python3 update_commodity_stories.py
python3 update_headlines.py
python3 build.py --apply
```

`update_headlines.py` has a manual review gate:
1. Run `python3 update_headlines.py` — produces `stories_draft_YYYY-MM-DD.json`
2. Open `headline_review.html`, load draft, review/edit, export `stories_approved_YYYY-MM-DD.json`
3. Run `python3 update_headlines.py --apply stories_approved_YYYY-MM-DD.json`
4. Run `python3 build.py --apply`

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
| ZAF | Unemployment | No reliable monthly FRED series |
| RUS | All equity | IMOEX.ME delisted post-sanctions — MOEX REST API used instead |

---

### Story levels

Three levels per metric per country: `beginner`, `moderate`, `expert`. 216 per-metric stories (12 countries × 6 macro metrics × 3 levels) + 27 commodity stories (9 commodities × 3 levels). Country card stories (top-level) are separate and updated daily by `update_headlines.py`.

---

### Scripts summary

| Script | Trigger | What it does |
|--------|---------|--------------|
| `fetch_market_data.py` | Daily | Fetches equity/FX/yields via yfinance+FRED, updates data.json; appends today's commodity prices to MARKET-STATS `Commodities` tab |
| `sync_commodity_data.py --apply` | Daily | Reads `Commodities` tab, derives price/change/spark (120 monthly pts), writes to data.json |
| `update_commodity_stories.py` | Daily | Rewrites commodity stories when price moves exceed threshold |
| `update_headlines.py` | Daily | Calls Claude API, writes country and global stories to draft JSON (manual review gate before --apply) |
| `sync_sheet.py --apply` | When forecasts change | Reads Macro-stats sheet, writes macro card values and historical arrays |
| `sync_monthly_actuals.py` | Monthly | Reads MACRO-MONTHLY sheet, writes `monthly_actuals` |
| `update_stories.py` | On metric change | Diff-driven per-metric story rewrites |
| `build.py --apply` | Daily | Assembles globe.html, validates, diffs, auto-commits, pushes |

---

### Shell key facts (macrosnaps-shell.html)

- Market metrics read from `co.metrics.market[display_key]` — exact string match required
- `Stock Market YTD (USD)` read at rankings table only — excluded from country cards via `CARD_MARKET_EXCLUDE`
- `Stock Market Index` and `FX Rate` also excluded from country cards via `CARD_MARKET_EXCLUDE`
- Local YTD: `co.metrics.market['Stock Market YTD']`
- `_flattenMetrics()` flattens `{value, story}` objects to bare values for the shell
- `DISPLAY_NAMES` map: `'United Kingdom' → 'UK'`, `'United States' → 'USA'`
- Weather icon computed live from GDP Growth thresholds: ≥3% ☀️, ≥0% ☁️, <0% ⛈️
- `metricDisplayLabels`: `'Policy Rate' → 'Policy Rate (year-end)'`
- Globe is lazy-init (WebGL only on first toggle click). Nav buttons hidden, globe accessible by restoring `.view-toggle{display:flex}` if needed.
- Default sort: `_whSortCol = -1` = nominal GDP order (GDP_NOMINAL_ORDER constant). Logo click resets to this. Metric dropdown change also resets to `-1` (Session 17 fix).
- `CARD_MARKET_EXCLUDE` set: `'Stock Market YTD (USD)'`, `'Stock Market Index'`, `'FX Rate'`

### Weather icon rule (FIXED — do not change)

All weather icons across the entire site must use the `.wh-icon` CSS filter pattern:
- A single `☀️` emoji wrapped in `<span class="wh-icon sunny/cloudy/stormy">`
- `.sunny`: no filter. `.cloudy`: `brightness(.6) contrast(1.05) saturate(.3)`. `.stormy`: `brightness(.15) contrast(1.2) saturate(0) drop-shadow(...)`
- Exception: per-metric strip uses the correct emoji per state (`☀️` sunny, `☁️` cloudy, `⛈️` stormy) with the same `.wh-icon cls` wrapper — this is intentional so the filter still applies correctly
- Never use differently-styled icons (raw emoji, SVG, different filter values) anywhere else on the site

---

### Pending work (priority order)

1. **Fix JPN inflation gap.** `CPALTT01JPM657N` stops June 2021. Replace with `JPNCPIALLMINMEI` (OECD index level, not pre-computed YoY) in `populate_monthly_actuals.py` and `update_monthly_actuals.py`. Add `.pct_change(12) * 100` transform before writing. Re-run JPN inflation backfill only. Upload LIVING_BRIEF.md + both monthly actuals scripts. **Next session: audit all MACRO-MONTHLY gaps across all countries.**

1. **Apply USA sheet changes.** `sync_sheet.py` preview on March 11 showed USA CPI 3.1% -> 2.3% and Unemployment 4.4% -> 4.2%. These were never applied. Run: `python3 sync_sheet.py --apply && python3 update_stories.py && python3 build.py --apply`

1. **GDP Growth stories audit.** CAN, FRA, ITA, BRA confirmed mismatches between story text and current values. Run a targeted stories session for these four countries (upload LIVING_BRIEF.md + data.json, use Part 1B prompt).

1. **Build `print_snapshot.py`.** Uses Playwright to open the built HTML file, loops through each country, expands it, and captures a full-height PDF. Output is a dated file in `snapshots/` (e.g. `macrosnaps-2026-03-09.pdf`). Audience level hardcoded to expert. For personal use only, not a public feature. Requires `pip3 install playwright` and `playwright install chromium`.

1. **Clean up redundant scripts** (confirm contents before deleting): `sync_market_historical.py`, `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`, `headline_review.html`.

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
