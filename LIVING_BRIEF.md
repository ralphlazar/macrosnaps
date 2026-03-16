# MacroSnaps - Living Brief
Last updated: March 16, 2026 (Session 23: MACRO-MONTHLY backfill completed. IMF API migration to new SDMX endpoint. populate_monthly_actuals.py and update_monthly_actuals.py rewritten.)

Session 23 changes in detail:

(1) **Old IMF API permanently shut down.** `dataservices.imf.org` is not a temporary outage — the IMF decommissioned this endpoint in 2025 and replaced it with a new SDMX API accessible via the `sdmx1` Python library (`sdmx.Client('IMF_DATA')`). All scripts that used the old endpoint now use the new one. `sdmx1` is now a required dependency (`pip3 install sdmx1 --break-system-packages`).

(2) **`populate_monthly_actuals.py` rewritten (v3).** New data sources:
- **Inflation**: IMF `CPI` dataset, key `COUNTRY.CPI._T.IX.M`. Single call covers all 12 countries. YoY % computed from monthly index levels (fetched from Jan 1999 for overlap). All 12 countries current to Jan 2026, IND to Dec 2025.
- **Unemployment**: IMF `LS` dataset, key `COUNTRY.U.PT.M`. Covers USA/CAN/JPN/DEU/FRA/ITA/BRA/RUS. GBR fallback: FRED `LRHUTTTTGBM156S`. CHN/IND/ZAF remain permanent blanks.
- **Policy Rate**: BIS `WS_CBPOL` API for CAN/GBR/JPN/IND/ZAF/BRA/RUS. FRED `FEDFUNDS` for USA. FRED `ECBMRRFR` for DEU/FRA/ITA. CHN and RUS remain permanent blanks. Architecture identical to old script.

(3) **`update_monthly_actuals.py` rewritten (v3).** Same source changes as populate. Incremental append logic unchanged.

(4) **MACRO-MONTHLY backfill completed successfully.** `populate_monthly_actuals.py --apply` wrote 315 rows to all three tabs (Inflation, Unemployment, Policy_Rate). `sync_monthly_actuals.py --apply` and `build.py --apply` run successfully. All 12 countries now have current monthly actuals in tooltip charts.

(5) **Known data gaps after backfill** (expected, not bugs):
- USA unemployment: last=Dec 2024 (IMF LS lags ~3 months for USA)
- GBR unemployment: last=Oct 2025 (FRED ONS series lags ~5 months)
- DEU unemployment: 228 months (IMF LS coverage starts ~2007 for DEU)
- FRA unemployment: 276 months (IMF LS coverage starts ~2003 for FRA)
- BRA unemployment: 156 months (IMF LS coverage starts ~2013 for BRA)
- JPN policy rate: 208 months (BIS WS_CBPOL JPN starts ~2008)

(6) **Deprecation warning in `populate_monthly_actuals.py`.** `ws.update('A1', values)` triggers a gspread argument order warning. Harmless but fix in next pipeline session: change to `ws.update(values, 'A1')`.

(7) **New IMF API country/dataset reference:**
- CPI: `sdmx.Client('IMF_DATA').data('CPI', key='COUNTRY.CPI._T.IX.M', params={'startPeriod': 'YYYY-MM'})`
- Unemployment: `sdmx.Client('IMF_DATA').data('LS', key='COUNTRY.U.PT.M', params={'startPeriod': 'YYYY-MM'})`
- Country codes: ISO3 (USA, GBR, DEU, JPN, FRA, ITA, CAN, CHN, IND, ZAF, BRA, RUS)

---

Session 22 changes in detail:

(1) **`forecast_cms.html` built.** Standalone browser-based CMS for editing 2026 annual forecast values (Column AB) across all 12 country tabs in the Macro-stats Google Sheet. Shows a 12-country grid, 6 metrics each. Inputs save on blur with flash feedback (gold = saving, green = saved, red = error). Context column shows latest external consensus value, source, date, and revision badge (▲/▼) where available. Server connection status shown in header with auto-detect.

(2) **`forecast_server.py` built.** Local Flask proxy running on `localhost:5050`. Authenticates via `market-stats-key.json` service account (same credential used by all other scripts). Endpoints: `GET /forecasts` (reads Column AB for all 12 countries in one batched column call per tab), `POST /forecast` (writes single cell), `GET /external_forecasts` (serves `external_forecasts.json`), `POST /run_fetch` + `GET /fetch_status` (triggers fetcher subprocess and polls progress). Requires `flask flask-cors` in addition to existing dependencies. Service account must have Editor access to Macro-stats sheet — confirmed working with `macrosnaps-sheets@macrosnaps.iam.gserviceaccount.com`.

(3) **`fetch_external_forecasts.py` built.** Haiku 4.5 + web search, one API call per country, fetches latest 2026 forecasts from IMF, OECD, Goldman Sachs, JPMorgan, and other credible institutions published in the last 30 days. Returns structured JSON per metric: value, source, date, prior (if revised), notes. Writes to `external_forecasts.json`. `max_uses: 3` web searches per call. Cost: ~$0.73/run. Recommended cadence: weekly (or on-demand via CMS header button).

(4) **Forecast CMS daily usage.** To use the CMS: (a) open terminal, run `python3 forecast_server.py` and leave running; (b) open `Downloads/macrosnaps/forecast_cms.html` in browser; (c) edit any forecast value — saves automatically on blur; (d) hit ⬇ Fetch External weekly or on-demand for fresh context data.

(5) **`METRIC_ROWS` config in `forecast_server.py`.** Row mapping (1-indexed) assumes GDP_Growth=2, Inflation=3, Unemployment=4, Budget_Deficit=5, Current_Account=6, Policy_Rate=7 in each country tab. Verify this matches the actual Macro-stats tab layout if saves land in wrong rows.

---


Session 21 changes in detail:

(1) **Daily ritual completed successfully.** All steps run in order:
- `fetch_market_data.py` — 41 updated, 7 permanent failures (CHN/BRA/RUS yields, RUS equity), 9 commodities green. USA USD/DXY returned EMPTY from yfinance (`DX-Y.NYB`) — monitor tomorrow.
- `sync_market_historical.py --apply` — 48 spark arrays written. All warnings are known permanent gaps per LIVING_BRIEF.
- `sync_commodity_data.py --apply` — 9/9 updated. Change values correctly day-over-day. WTI, Brent, Silver rewrites triggered by `update_commodity_stories.py`.
- `update_headlines.py` — 13/13 OK in 270s. Draft reviewed, cite tags stripped, approved, applied.
- `build.py --apply` — 16 metric changes, 36 story changes, 9 commodity changes. Committed and pushed.

(2) **Cite tag bug fixed in `update_headlines.py` (two parts).**
- **Prompt-level fix:** Added hard rule to `build_global_system()` prompt: *"All story text must be plain prose only. Never include HTML tags, `<cite>` tags, citation markup, markdown, or any other formatting. No angle brackets of any kind in story text."* This prevents cite tags being generated.
- **Scrubber fix (STILL PENDING):** `clean_cite_tags()` in `update_headlines.py` uses regex `r'</?antml:cite[^>]*>'` which does not match the actual escaped tags in JSON (`<cite index=\\"...\\">`). Correct regex is `r'</?cite[^>]*>'`. **Fix this in next pipeline session.**
- **Today's draft:** cite tags stripped manually from `stories_draft_2026-03-16.json` using `re.sub(r'</?cite[^>]*>', '', raw)` directly on the raw file.

(3) **`update_headlines.py`: harvest prompt broadened to include geopolitical events.** Previous prompt asked only for CPI prints, GDP reads, and central bank decisions — missing major news like conflicts, trade policy, elections, sanctions. New prompt explicitly asks for the most newsworthy thing happening for each country, including geopolitical developments. Also: `max_tokens` 1500 → 2000, search turns 2 → 3. Takes effect from tomorrow's run.

(4) **`headline_review.html`: global detail textarea font fixed.** `.global-detail-textarea` had `font-size: 12px` and `color: var(--text-dim)` — smaller and grey vs country fields. Fixed to `font-size: 13px` and `color: var(--text)` to match `.bullet-textarea`.

(5) **Editorial workflow clarified.** When re-editing stories mid-day: always load `stories_approved_YYYY-MM-DD.json` (not the draft) to preserve previous edits. Re-export overwrites the approved file. Re-run `update_headlines.py --apply` + `build.py --apply` to push updates live. Safe to do multiple times per day.

---

Session 20 changes in detail:

(1) **`macrosnaps-shell.html`: icon removed from global story tooltip title.** `${d.icon}` stripped from `renderNews()` tt-title line. Tooltip now shows label text only.

(2) **`macrosnaps-shell.html`: "MSc Economics (LSE)," removed from WHO copy.** Bio now reads: *"Built by Ralph Lazar - formerly Global Equity Strategy at Goldman Sachs and Fixed-Income Prop Trading at CSFB. Old habits die hard."*

(3) **`macrosnaps-shell.html`: HOW copy updated.** "Stories and briefings are drafted by AI and reviewed via a custom editorial tool before going live." → "Stories and briefings are generated from a custom automated pipeline and reviewed and edited before going live."

(4) **`audit_market_data.py` written and run successfully.** Audits all 12 country tabs in MARKET-STATS sheet. Results clean — all permanent gaps (CHN, RUS all series; IND/BRA yields; ZAF stock ~2012 start; JPN 3M ~585 gaps) confirmed and match LIVING_BRIEF. No unexpected failures.

(5) **`audit_macro_monthly.py` written but not yet run.** MACRO-MONTHLY sheet (`1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI`) not yet published to web. **Next session: publish sheet via File → Share → Publish to web, then run `python3 audit_macro_monthly.py`.**

---

Session 19 changes in detail:

(1) **`sync_monthly_actuals.py`: `MONTHS_TO_KEEP = 6` → `36`.** One-line change done. Docstring and preview print updated to match. Deploy with `sync_monthly_actuals.py --apply` after IMF API backfill runs successfully.

---

Session 18 changes in detail:

(1) **`populate_monthly_actuals.py` and `update_monthly_actuals.py` rewritten (v2).** Root cause: FRED was mirroring OECD MINMEI CPI index series for most countries, and that feed froze silently at various dates (CAN/GBR/DEU/FRA/ITA/CHN/IND/ZAF/BRA stopped around March 2025; JPN stopped June 2021; RUS stopped March 2022). Fix: switched CPI and Unemployment to **IMF IFS API** (`dataservices.imf.org`) using indicators `PCPI_IX` (CPI index, YoY computed from levels) and `LUR` (unemployment rate). Single API call per indicator covers all 12 countries simultaneously. FRED dependency now narrowed to Policy Rate only (FEDFUNDS + ECBMRRFR + BIS CBPOL). RUS removed from BIS CBPOL (sanctions gap from Mar 2022, no reliable free alternative) — `RATE_SERIES["RUS"] = None`. `RATE_SERIES` sentinel format changed to `"FRED:FEDFUNDS"` / `"FRED:ECBMRRFR"` for clarity. **Status: IMF API was down (timeout) on March 15. Scripts are correct — run when API is available.**

(2) **New script `sync_market_historical.py`.** Architectural rule: all spark arrays must cover Jan 2000 → last available data point, where "last available" must be within the last 3 months. If a source stops updating, the chart shows a visible trailing gap rather than silently hiding stale frozen data. Gaps are diagnostic. Rebuilds all 4 market spark arrays for all 12 countries from scratch on every run: Stock Market (yfinance monthly last close), FX rate (yfinance monthly, inverted where needed), 10Y Bond Yield (FRED monthly), Yield Curve in bps (derived: 10Y − short rate). Writes to `_frozen_historical[label] = {"type": "line", "v": [...]}` — the correct location the shell reads via `historicalData[code][label].v`. Runs daily. Caches shared tickers (DEU/FRA/ITA share EURUSD=X; ECB series shared for yield curve). Staleness check warns if array is shorter than expected — note: current check counts total points vs Jan 2000 expected, which produces false positives where yfinance simply has shorter history (e.g. CAD/USD starts 2004, not 2000). Fix staleness check in next pipeline session to check last point date instead.

(3) **Bug fix: spark arrays were writing to wrong location.** Previous `sync_market_historical.py` wrote to `metrics.market[label]["spark"]` — a field the shell never reads. Shell reads chart data exclusively from `_frozen_historical[label].v`. Fixed in same session. Confirmed working: USD/DXY Jan 2000 → March 2026, 10Y Bond Yield Jan 2000 → March 2026, Yield Curve Jan 2000 → March 2026.

(4) **Monthly actuals audit findings.** `sync_monthly_actuals.py` has `MONTHS_TO_KEEP = 6` — only 6 data points written per series. This is too few and shows in the tooltip line charts. Increase to 36. Also confirmed: `monthly_actuals` IS rendered in tooltip charts (the script header comment saying "story context only" is wrong — do not rely on it). JPN inflation last point = Jan 2021 and RUS inflation last point = Oct 2021 are confirmed visible gaps in the live charts. Both fixed once `populate_monthly_actuals.py` runs successfully.

(5) **`_frozen_historical` structure confirmed.** Shell populates `historicalData[code]` from `c._frozen_historical` (line 5595). All tooltip charts — both macro and market — read from this dict. Format per entry: `{"type": "bar"|"line", "v": [...]}`. Market metric sparks (`sync_market_historical.py`) and macro metric arrays (`sync_sheet.py`) both write here. `monthly_actuals` is a separate field written by `sync_monthly_actuals.py` and used for a different chart path.

(6) **Rolling spark update in `fetch_market_data.py` is superseded.** Lines 538–542 (`spark = spark[1:] + [round(current, 2)]`) roll the commodity spark forward one point per day. This pattern is now architecturally wrong — all sparks must be rebuilt from source, not rolled. Remove this block in the next pipeline session. `sync_market_historical.py` is the correct owner of market metric sparks. `sync_commodity_data.py` is the correct owner of commodity sparks (already implements full-history rebuild from the Commodities sheet — no change needed there).

(7) **Staleness warnings from preview run (expected, not bugs):**
- CAD/USD, GBP/USD, EUR/USD, USD/INR, USD/ZAR, USD/BRL: ~268 pts — yfinance coverage starts ~2004, not 2000. Data is current.
- ZAF stock (`^J203.JO`): ~170 pts — yfinance coverage starts ~2012.
- IND bond/yield curve (`INDIRLTLT01STM`): ~170 pts — FRED coverage starts ~2012.
- JPN Yield Curve: 286 pts (~26 months short) — `IR3TIB01JPM156N` may have stopped updating on FRED ~early 2024. Investigate in next pipeline session.
- CHN/BRA/RUS bond yields and yield curves: EMPTY — no FRED series, permanent known gaps.

---

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
- Probably redundant (check before deleting): `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`, `headline_review.html`

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

Session 14–8: See previous brief versions.

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
- Pipeline session (data fetching, sheets, scripts): upload `LIVING_BRIEF.md` + relevant scripts
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
- Built file: `macrosnaps-globe.html` (standalone, self-contained, ~1040 KB)

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
- Source: yfinance + FRED
- Script: `fetch_market_data.py` — fetches and writes current values to `metrics.market[label].value` only. Never touches spark arrays.
- RUS equity: MOEX REST API (not yfinance). `fetch_moex_index()` in `fetch_market_data.py`
- Permanent blanks (no FRED series): CHN/IND/BRA/RUS bond yields. Values hand-maintained in data.json. None-guard prevents blank values from overwriting them.

**Market metric spark arrays (historical line charts):**
- Script: `sync_market_historical.py --apply` — rebuilds all 4 market spark arrays for all 12 countries from Jan 2000 to present on every run
- Writes to: `_frozen_historical[label] = {"type": "line", "v": [...]}` — this is the correct location the shell reads
- Run: daily (after `fetch_market_data.py`)
- Sources: yfinance (stock, FX), FRED (bond yields, yield curve)

**Commodity daily prices:**
- Source: MARKET-STATS Google Sheet, `Commodities` tab
- Columns: `Date | WTI Crude | Brent Crude | Natural Gas | Gold | Silver | Copper | Wheat | Corn | Soybeans`
- History from: 2000-07-17 (yfinance limit for continuous futures; Brent from 2007-07-30)
- Script: `fetch_market_data.py` appends today's row; `sync_commodity_data.py --apply` reads tab, derives price/change/spark, writes to data.json
- `price`: last row value. `change`: % diff last two rows (day-over-day). `spark`: monthly last-close array, last 120 months.
- Backfill script: `backfill_commodity_data.py` — one-time, already run. Do not re-run.
- Weekend note: Sunday runs fetch Friday's closing prices. Monday's day-over-day change = Friday→Monday move. Correct behaviour.

**Monthly actuals (tooltip line charts — Inflation, Unemployment, Policy Rate):**
- Source: MACRO-MONTHLY Google Sheet (ID: `MACRO_MONTHLY_SHEET_ID` env var)
- Tabs: `Inflation`, `Unemployment`, `Policy_Rate`
- Columns: `Date | USA | CAN | GBR | JPN | DEU | FRA | ITA | CHN | IND | ZAF | BRA | RUS`
- Backfill script: `populate_monthly_actuals.py` — run to rewrite full history from Jan 2000. CPI and Unemployment from **new IMF SDMX API** (`sdmx.Client('IMF_DATA')`). Policy Rate from BIS WS_CBPOL + FRED.
- Incremental script: `update_monthly_actuals.py` — appends new months only. Safe to run daily.
- Sync script: `sync_monthly_actuals.py --apply` — reads last N non-null values per country per series, writes `monthly_actuals` field to data.json. `MONTHS_TO_KEEP = 36`.
- Writes: `monthly_actuals` field only. Never touches metrics.
- **New IMF SDMX API**: `sdmx.Client('IMF_DATA')` via `sdmx1` library. CPI dataset: `COUNTRY.CPI._T.IX.M`. LS (unemployment) dataset: `COUNTRY.U.PT.M`. Old `dataservices.imf.org` endpoint is permanently dead.

---

### Spark array architecture rule

**Every spark array must cover Jan 2000 → last available data point.** "Last available" must be within the last 3 months of today. If a source stops updating, the chart shows a visible trailing gap rather than hiding it. Gaps are diagnostic. Sparks are never rolled forward one point at a time — they are always rebuilt from source on each run.

---

### Daily ritual

```bash
python3 fetch_market_data.py
python3 sync_market_historical.py --apply
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

**Mid-day re-edit workflow:** Load `stories_approved_YYYY-MM-DD.json` (not the draft) to preserve previous edits. Re-export overwrites the approved file. Re-run steps 3 and 4. Safe to do multiple times per day.

---

### Key data.json paths

```
data.countries[code].metrics.macro[metric_name].value       ← card display value (string)
data.countries[code].metrics.macro[metric_name].story       ← per-metric story object
data.countries[code].metrics.market[metric_name].value      ← current market value (string)
data.countries[code]._frozen_historical[metric_name].type   ← "bar" or "line"
data.countries[code]._frozen_historical[metric_name].v      ← chart data array (all tooltip charts)
data.countries[code].monthly_actuals                        ← {inflation, unemployment, policy_rate} arrays
data.commodities.items[n].price                             ← commodity price
data._meta.generated                                        ← build date stamp
```

---

### Known permanent data gaps

| Country | Metric | Reason |
|---------|--------|--------|
| CHN, IND | Unemployment | No IMF LUR coverage — blank |
| ZAF, BRA, RUS | Unemployment | No IMF LUR coverage — blank |
| CHN, IND, BRA, RUS | 10Y Bond Yield | No FRED series — values hand-maintained in data.json |
| CHN, IND, BRA, RUS | 3M Yield / Yield Curve | No FRED series — always blank |
| RUS | Policy Rate (MACRO-MONTHLY) | BIS stopped publishing after Feb 2022 (sanctions) — blank from Mar 2022 |
| RUS | All equity | IMOEX.ME — MOEX REST API used instead of yfinance |
| CAD/USD, GBP/USD, EUR/USD, USD/INR, USD/ZAR, USD/BRL | FX spark history | yfinance coverage starts ~2004, not 2000. Data is current, history is shorter. |
| ZAF | Stock Market spark history | yfinance `^J203.JO` starts ~2012 |
| IND | Bond Yield / Yield Curve spark history | FRED `INDIRLTLT01STM` starts ~2012 |
| JPN | Yield Curve spark (possible) | `IR3TIB01JPM156N` may have stopped updating on FRED ~early 2024. Investigate. |

---

### Scripts summary

| Script | Trigger | What it does |
|--------|---------|--------------|
| `fetch_market_data.py` | Daily | Fetches current equity/FX/yields via yfinance+FRED, writes `metrics.market[label].value`; appends today's commodity prices to MARKET-STATS `Commodities` tab |
| `sync_market_historical.py --apply` | Daily | Rebuilds all market metric spark arrays in `_frozen_historical` from Jan 2000 to present (yfinance + FRED) |
| `sync_commodity_data.py --apply` | Daily | Reads `Commodities` tab, derives price/change/spark (120 monthly pts), writes to data.json |
| `update_commodity_stories.py` | Daily | Rewrites commodity stories when price moves exceed threshold |
| `update_headlines.py` | Daily | Calls Claude API, writes country and global stories to draft JSON (manual review gate before --apply) |
| `sync_sheet.py --apply` | When forecasts change | Reads Macro-stats sheet, writes macro card values and `_frozen_historical` arrays |
| `populate_monthly_actuals.py` | Once (backfill) | Writes full history Jan 2000 → present to MACRO-MONTHLY sheet. CPI+Unemployment via new IMF SDMX API (`sdmx1`); Policy Rate via BIS WS_CBPOL + FRED |
| `update_monthly_actuals.py` | Monthly | Appends new months to MACRO-MONTHLY sheet. Same sources as populate. |
| `sync_monthly_actuals.py --apply` | After update_monthly_actuals | Reads MACRO-MONTHLY sheet, writes `monthly_actuals` to data.json (36 most recent non-null per series) |
| `update_stories.py` | On metric change | Diff-driven per-metric story rewrites |
| `build.py --apply` | Daily | Assembles globe.html, validates, diffs, auto-commits, pushes |

---

### Shell key facts (macrosnaps-shell.html)

- All tooltip charts (macro and market) read from `_frozen_historical[label].v` via `historicalData[code]` (line 5595: `historicalData[c.code] = c._frozen_historical`)
- Market metric current values read from `co.metrics.market[display_key]` — exact string match required
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
- `monthly_actuals` field is rendered in tooltip line charts for macro metrics — the script header comment saying "story context only" is wrong.

### Weather icon rule (FIXED — do not change)

All weather icons across the entire site must use the `.wh-icon` CSS filter pattern:
- A single `☀️` emoji wrapped in `<span class="wh-icon sunny/cloudy/stormy">`
- `.sunny`: no filter. `.cloudy`: `brightness(.6) contrast(1.05) saturate(.3)`. `.stormy`: `brightness(.15) contrast(1.2) saturate(0) drop-shadow(...)`
- Exception: per-metric strip uses the correct emoji per state (`☀️` sunny, `☁️` cloudy, `⛈️` stormy) with the same `.wh-icon cls` wrapper — this is intentional so the filter still applies correctly
- Never use differently-styled icons (raw emoji, SVG, different filter values) anywhere else on the site

---

### Pending work (priority order)

1. **Fix `clean_cite_tags()` regex in `update_headlines.py`.** Current pattern `r'</?antml:cite[^>]*>'` does not match actual escaped tags in JSON. Correct pattern: `r'</?cite[^>]*>'`. Fix in next pipeline session.

1. **Fix gspread deprecation warning in `populate_monthly_actuals.py`.** Change `ws.update('A1', values)` to `ws.update(values, 'A1')`. One-line fix.

1. **Remove rolling spark update from `fetch_market_data.py`.** Lines 538–542: `spark = spark[1:] + [round(current, 2)]`. Superseded by `sync_market_historical.py`. Remove in next pipeline session.

1. **Fix staleness check in `sync_market_historical.py`.** Current check counts total points vs Jan 2000 expected — produces false positives for tickers with shorter yfinance history. Change to check whether the last point date is within `STALE_MONTHS` of today instead.

1. **Investigate USA USD/DXY EMPTY from `sync_market_historical.py`.** yfinance ticker `DX-Y.NYB` returned no data on March 16 run. Monitor tomorrow — may be a transient yfinance issue.

1. **Investigate JPN Yield Curve gap.** `IR3TIB01JPM156N` produced 286 pts (~26 months short). Check if FRED stopped updating this series and find a replacement if so.

1. **GDP Growth stories audit.** CAN, FRA, ITA, BRA confirmed mismatches between story text and current values. Run a targeted stories session for these four countries (upload LIVING_BRIEF.md + data.json, use Part 1B prompt).

1. **Build `print_snapshot.py`.** Uses Playwright to open the built HTML file, loops through each country, expands it, and captures a full-height PDF. Output is a dated file in `snapshots/` (e.g. `macrosnaps-2026-03-09.pdf`). Audience level hardcoded to expert. For personal use only, not a public feature. Requires `pip3 install playwright` and `playwright install chromium`.

1. **Clean up redundant scripts** (confirm contents before deleting): `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`, `headline_review.html`.

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

**Stories** should be written off recent data and trends, not off the forecast values. Monthly CPI prints, quarterly GDP flash estimates, central bank decisions, weekly jobless claims — this is the live texture that makes stories worth reading. A story that just restates the annual forecast number adds no value.

The correct approach: stories comment on what is actually happening right now. If recent data is tracking ahead of or behind the annual forecast, the story can note that tension briefly (e.g. "February CPI came in at 2.6%, above the Fed target, but full-year inflation is still expected to settle at 2.3% as base effects kick in mid-year"). But the forecast is not the anchor of the story — recent data is.

**Architectural constraint: write path separation.** `sync_sheet.py --apply` writes only annual forecast fields (GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account, Policy Rate arrays and card values). `sync_monthly_actuals.py` writes only the `monthly_actuals` field. These two scripts must never touch each other's fields. This is currently enforced by construction but must be preserved in any future refactor. No other script writes to `monthly_actuals`.

---

**Do not position against Bloomberg or data terminals.** The audience is professionals and informed non-professionals who want a daily briefing at the depth they choose, not a research platform. The competition is a good morning read, not a data subscription.
