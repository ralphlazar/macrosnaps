# MacroSnaps - Living Brief
Last updated: March 31, 2026 (Session 62: Daily ritual completed; sync_edu.py path fix — script runs from macrosnaps repo, not macedu; Daily Bash Ritual updated accordingly.)

Session 62 changes in detail:

(1) **Daily ritual completed 2026-03-31.** Full ritual ran successfully. Silver commodity story rewritten (5.2% move). Headlines 13/13. Metric stories 12/12 (CAN failed on first run, succeeded on retry). Build successful, pushed to master. macedu synced and pushed to main.

(2) **`sync_edu.py` path fix.** Script lives in the macrosnaps repo (`/Users/lisaswerling/RALPH/AI/macrosnaps/`), not in macedu. Daily Bash Ritual updated to run it explicitly from the macrosnaps directory.

---

Session 61 changes in detail:

(1) **Daily ritual completed 2026-03-29.** Full ritual ran successfully. Notable: `update_headlines.py` failed on first attempt (JSON parse error batch 1), succeeded on retry. All 12/12 metric stories completed in 86s (parallel). Build successful, pushed to master. macedu daily sync pushed to main.

(2) **`update_commodity_stories.py` — migrated to bullet arrays.** Stories now stored as arrays `["bullet1", "bullet2", "bullet3"]` per level, matching the country story schema. Changes:
- `LEVEL_GUIDANCE` updated to specify 3 bullets per level.
- Prompt updated to request JSON arrays not prose strings.
- `apply_stories` stores arrays.
- Batching fixed: was attempting all 9 commodities in one call (output truncated). Fixed by splitting into `draft_batch` (3 commodities per call) + `draft_stories` wrapper (3 batches of 3). All 9 commodity stories regenerated as bullet arrays.
- Shell renderer at line 56864 already handled both formats (`Array.isArray` → `<ol>`, string → `<div>`). No shell change needed.

(3) **`sync_market_historical.py` — CHN tab crash fixed.** Root cause: `get_all_values()` pads all rows to the width of the widest row, creating empty-string duplicate column names. `pd.to_numeric()` received a DataFrame instead of a Series. Fix: strip trailing empty headers; truncate data rows to match header length.

(4) **`audit_ritual.py` — two fixes:**
- Global stories: audit now accepts either `body` or `bullets` field (was requiring `body`, failing since Session 59 schema change to `bullets`).
- Commodity spark threshold: changed from `EXPECTED_SPARK_PTS - 3` to `300`. Commodity data starts 2000-07-17 (Yahoo Finance limit), giving ~307–309 pts max, not 315.

(5) **`build.py` — globalStories validator updated.** Accepts `bullets` or `body` (not both required). Committed as `"audit_ritual: accept bullets as well as body for global stories"`.

(7) **`update_commodity_stories.py` — prompt overhauled.** Commodity stories were too long and the beginner level was effectively commodity-101 boilerplate rather than price-anchored interpretation. Two changes:
- Bullet length: "each a complete sentence or two" → "one sentence only, maximum 20 words per bullet"
- Beginner LEVEL_GUIDANCE rewritten: all 3 bullets now anchored to current price. Bullet 1: what the current price tells us right now in plain English. Bullet 2: one real-world effect ordinary people would recognise (fuel, food, energy bills). Bullet 3: one concrete implication for ordinary people — what does this price level actually mean for their wallet, their savings, or their daily costs? (Previous beginner guidance opened with "what this commodity is and why it exists" — evergreen boilerplate, not interpretation.)

 `export_brent_csv.py` built and run. `brent_backfill.csv` (1,687 rows, 2000-07-17 to ~2007) pasted into Commodities tab; `sync_commodity_data.py --apply` + `build.py` run successfully.

---

Session 60 changes in detail:

(1) **MARKET-STATS daily append fixed.** `fetch_market_data.py` was not writing daily rows to MARKET-STATS country tabs (USA–RUS). Root cause: the append function was never built. Patched to append one row per country per day with columns: Date, Stock_Market_Index, FX_Rate, Bond_Yield_10Y, Bond_Yield_3M, Yield_Curve, Stock_Market_YTD_USD. New helper `yf_ytd_and_level()` added to fetch index level alongside YTD% in one Yahoo call. Tab names in MARKET-STATS match country codes exactly (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS).

(2) **MARKET-STATS backfilled Mar 16–27.** `backfill_market_stats.py` built to insert missing trading days into all 12 country tabs in date order. Idempotent. Rate-limited to avoid Google Sheets quota (1.2s/row, 3s between countries). `patch_bond_yields.py` built to fill missing bond yield columns for the backfill period using FRED carry-forward values.

(3) **MACRO-MONTHLY Unemployment — IND and ZAF backfilled.** `backfill_unemployment.py` built:
- ZAF: FRED `LRUNTTTTZAQ156S` (OECD quarterly, SA) → linear interpolation to monthly. Covers Q3 2000–Q4 2024.
- IND: World Bank `SL.UEM.TOTL.ZS` (annual) → July midpoint interpolation to monthly. Covers 1991–2025.
- `MACRO_MONTHLY_SHEET_ID=1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI` added to .env.
- CHN: no free programmatic source — permanent blank.

(4) **MACRO-MONTHLY Unemployment — BRA wired into daily ritual.** `update_monthly_actuals.py` patched to fetch BRA unemployment from IBGE SIDRA table 6381 (PNAD Contínua, monthly, free, no key). BRA removed from `UNEMP_BLANK` and `KNOWN_BLANKS`. IBGE SIDRA period key is `D3C` (format: `YYYYMM`). Historical gap Jan 2000–Dec 2011 backfilled via FRED `LRUNTTTTBRM156S`. Jan–Feb 2012 remain blank (PNAD Contínua started Mar 2012).

(5) **MACRO-MONTHLY historical gaps filled.** `backfill_historical_gaps.py` built and run:
- Unemployment DEU 2000–2006: FRED `LRHUTTTTDEM156S` (84 cells)
- Unemployment FRA 2000–2002: FRED `LRHUTTTTFRM156S` (36 cells)
- Policy Rate JPN 2000–2006 and 2013–2016: FRED `IRSTCI01JPM156N` (106 cells)
- Policy Rate DEU/FRA/ITA 2000–2008: hardcoded ECB MRO step function (297 cells) — FRED and ECB APIs both non-functional for this series; hardcoded from official ECB historical rate table.
- RUS unemployment 2000–2009: permanent gap — no free programmatic source exists.

(6) **MACRO-MONTHLY backfill applied.** `update_monthly_actuals.py --backfill --apply` run: 13 cells filled (inflation Feb 2026 for 9 countries; ITA unemployment Dec 2025; ECB policy rate Mar 2026 for DEU/FRA/ITA).

---

Session 59 changes in detail:

(1) **Metric story pipeline fixed.** `update_metric_stories.py` was failing on all batches due to Haiku output truncation. Fixed by reducing to 1 country per call, then parallelised all 12 calls using `concurrent.futures.ThreadPoolExecutor`. Runtime dropped from 990s to ~74s. The script now uses `from concurrent.futures import ThreadPoolExecutor, as_completed`.

(2) **JSON file renames.** All draft/approved JSON filenames renamed for clarity:

| Old name | New name |
|---|---|
| `stories_draft_YYYY-MM-DD.json` | `HEADLINES_draft_YYYY-MM-DD.json` |
| `stories_approved_YYYY-MM-DD.json` | `HEADLINES_approved_YYYY-MM-DD.json` |
| `metric_stories_draft_YYYY-MM-DD.json` | `METRICS_draft_YYYY-MM-DD.json` |
| `metric_stories_approved_YYYY-MM-DD.json` | `METRICS_approved_YYYY-MM-DD.json` |
| `harvest_YYYY-MM-DD.json` | unchanged (internal only, never loaded in a UI) |

Files patched: `update_headlines.py`, `update_metric_stories.py`, `headline_review.html`, `metric_story_review.html`.

(3) **Schema change: globalStories `bullets` array.** Session 59 changed the globalStories schema from a `body` string to a `bullets` array. Three files updated to handle this:
- `headline_review.html` — normalises `bullets` → `body` (newline-joined) on load; splits back to `bullets` array on export.
- `build.py` — validator updated to accept either `body` or `bullets` field (not both required).

(4) **Daily Bash Ritual updated.** Metric stories step added as a parallel review gate alongside headlines. See updated ritual below.

---

Session 58 changes in detail:

(1) **Forecast CMS added.** `forecast_server.py` and `forecast_cms.html` added to the repo. The Forecast CMS is a local Flask proxy for reviewing and editing 2026 forecast values (Column AB) in the Macro-stats Google Sheet. Run every Friday before the Daily Bash Ritual:
```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 forecast_server.py
```
Then open `forecast_cms.html` in your browser. The server runs on `http://localhost:5050`.

(2) **Friday pre-ritual rule added.** Every Friday, run the Forecast CMS before starting the Daily Bash Ritual. The Daily Bash Ritual now detects Fridays and prompts accordingly.

---

Session 57 changes in detail:

(1) **Favicon added.** `favicon.ico` (16x16, 32x32, 48x48) and `favicon-192.png` generated from the MacroSnaps logo and added to the repo root. Two `<link>` tags added to `macrosnaps-shell.html` just before `</head>`:
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
```
X Card Validator confirmed the icon is picked up successfully.

---

Session 56 changes in detail:

(1) **Repo moved.** MacroSnaps repo relocated from `~/Downloads/macrosnaps` to `/Users/lisaswerling/RALPH/AI/macrosnaps`. All ritual commands updated. `MARKET_STATS_KEY_FILE` env var added to `.env` to fix sheet append key path for `fetch_market_data.py` and `sync_commodity_data.py`.

(2) **node_modules scrubbed from both repos.** `node_modules` and `package.json` (a legacy Cloudflare adapter) were accidentally committed to macrosnaps history, blocking GitHub pushes. Scrubbed via `git filter-repo`. Same fix applied to macedu repo. Both repos now clean.

(3) **Daily Bash Ritual fixed.** `sync_edu.py` repositioned to run after `build.py --apply` and before `audit_ritual.py`. macedu push step added explicitly after `sync_edu.py`.

---

Session 55 changes in detail:

(1) **macroeconomics.education data layer complete.** `sync_edu.py` reads `data.json` and writes `edu-data.json` to the macedu app, providing live snapshot values and 10-year historical chart series for all six education concepts across all six countries. Added as final step of the Daily Bash Ritual.

(2) **macedu GitHub repo created.** `https://github.com/ralphlazar/macedu` -- separate from macrosnaps. All six chart components now read from `edu-data.json` (not hardcoded). Design pass complete (fonts, colours, section compartmentalisation). Deployed to Cloudflare Pages.

---

Session 54 changes in detail:

(1) **US educator outreach complete.** All required US university contacts have been compiled. Campaign paused per Ralph's instruction -- no further batches needed.

(2) **UK educator outreach complete.** All required UK university contacts have been compiled. Campaign paused per Ralph's instruction -- no further batches needed.

---

Session 53 changes in detail:

(1) **US educator outreach: ranks 55-51 complete.** One batch produced, 10 contacts across 5 universities (plus one skip note for Georgia Tech). CSV file:

| File | Ranks | Universities | Contacts |
|------|-------|-------------|----------|
| us_outreach_55_51.csv | 55-51 | Kentucky, Tennessee-Knoxville, Georgia Tech, Georgia State, UGA | 10 |

(2) **Georgia Tech confirmed skip.** Georgia Tech's School of Economics has no dedicated macroeconomics or monetary economics researcher on faculty. Research focus areas are energy/environmental, health, development, trade, and IO. PhD programme has no macroeconomics field. Recommend skip entirely.

(3) **Running totals.** Ranks 100-51 complete: 125 contacts across 50 universities (Harvey Mudd and Georgia Tech skipped).

(4) **Key macro faculty from ranks 55-51:** Removed. See us_outreach_55_51.csv.

(5) **Batch sizing reminder.** Ranks 50-31: continue at 5 universities per batch. Ranks 30-1: switch to 1 university at a time (per Session 49 rule).

(6) **Next US institution: rank 50, Brigham Young University.**

---

Session 52 changes in detail:

(1) **Teaching-staff-first rule formalised.** The campaign target has been clarified. The primary audience is teaching staff -- faculty who directly assign or recommend tools to students in macro courses. This means:
- **Primary targets:** Teaching professors, lecturers, instructors, professors of practice, and clinical faculty who teach Principles of Macroeconomics, Intermediate Macroeconomics, Money and Banking, or International Finance/Macro
- **Secondary targets:** Research-active faculty who also hold teaching duties in macro courses
- **Exclude:** Pure researchers with no visible teaching role in macro; faculty whose macro connection is only through research group affiliation with no macro teaching listed

This rule applies to all future US outreach batches and should be reflected in notes (flag whether the contact is a teaching-primary or research-primary contact).

(2) **Session prompt for ranks 55-1 revised.** Teaching-staff-first rule incorporated.

(3) **Campaign status at start of session 52:** Ranks 100-56 complete. Next university: rank 55, University of Kentucky.

---

Session 51 changes in detail:

(1) **US educator outreach: ranks 70-56 complete.** Three batches produced, 59 contacts across 15 universities. CSV files produced per batch:

| File | Ranks | Universities | Contacts |
|------|-------|-------------|----------|
| us_outreach_70_66.csv | 70-66 | George Mason, American, GWU, Drexel, Temple | 23 |
| us_outreach_65_61.csv | 65-61 | Syracuse, Buffalo, Stony Brook, Rutgers, Miami | 18 |
| us_outreach_60_56.csv | 60-56 | Florida State, Clemson, South Carolina, Auburn, Alabama | 15 |

(2) **Running totals at end of session 51.** Ranks 100-56 complete: ~115 contacts across 45 universities.

(3) **High-priority Fed connections from ranks 70-56:** Removed. See us_outreach_70_66.csv, us_outreach_65_61.csv, us_outreach_60_56.csv.

---

Session 50 changes in detail:

(1) **Social Media Bash documented.** After completing the Daily Bash Ritual, run:
```bash
python3 digest_server.py
```
This starts the local server and automatically opens the MacroSnaps Digest UI at `http://localhost:PORT`. From there, generate, edit, and copy content for Substack, X, and LinkedIn. The UI file is `digest_ui.html` (note: `macrosnaps-digest.html` is an older redundant version).

(2) **Local preview rule added.** Since the site and app are live, all changes must be tested locally before pushing to git. Claude must always provide a local preview step before giving any git push command. Never combine build and push into a single command.

---

Session 49 changes in detail:

(1) **US educator outreach: ranks 100-71 complete.** Five batches produced, 76 contacts across 30 universities. Harvey Mudd (84) confirmed skip -- no macro faculty since Evans retirement in 2020. CSV files produced per batch:

| File | Ranks | Universities | Contacts |
|------|-------|-------------|----------|
| us_outreach_100_91.csv | 100-91 | Lehigh, Bucknell, Haverford, Vassar, Kenyon, Reed, Oberlin, Carleton, Macalester, Grinnell | 23 |
| us_outreach_90_86.csv | 90-86 | Bates, Bowdoin, Wesleyan, Hamilton, Colgate | 10 |
| us_outreach_85_81.csv | 85-81 | Davidson, Pomona, CMC, Middlebury (Harvey Mudd skipped) | 9 |
| us_outreach_80_76.csv | 80-76 | Wellesley, Swarthmore, Amherst, Williams, Brandeis | 19 |
| us_outreach_75_71.csv | 75-71 | Tufts, Northeastern, Boston College, UConn, Delaware | 14 |
| **Total** | **100-71** | **30 universities** | **76** |

(2) **Batch sizing going forward.** Ranks 70-31: continue at 5 universities per batch. Ranks 30-1: switch to 1 university at a time.

(3) **High-priority Fed connections identified (US campaign, ranks 100-71):** Removed. See us_outreach CSV files for ranks 100-71.

(4) **Swarthmore note.** Philip Jefferson (former Swarthmore macro faculty) is now Fed Vice Chair -- useful personalisation context.

(5) **Williams note.** Ranks 49th on IDEAS across all US econ departments -- exceptional for a liberal arts college.

---

Session 48 changes in detail:

(1) **UK educator outreach campaign: top 20 complete.** All 20 universities in the Complete University Guide 2026 economics rankings processed. 178 confirmed macro contacts across 20 UK universities. Grand total by cohort:

| Ranks | Universities | Contacts |
|-------|-------------|----------|
| 1-5   | Oxford, Cambridge, LSE, UCL, Warwick | ~45 |
| 6-10  | Edinburgh, Manchester, Bristol, Nottingham, Bath | ~40 |
| 11-15 | Exeter, Durham, Birmingham, Leeds, Sheffield | ~40 |
| 16-20 | Southampton, Glasgow, King's, Newcastle, St Andrews | ~35 |
| **Total** | **20** | **178** |

---

## Standing rules

### Target audience for outreach
1. Teaching professors, lecturers, instructors who teach macro courses (primary)
2. Research faculty who also hold clear teaching duties in macro courses
3. Do not include pure researchers with no visible macro teaching role

In the Notes field, flag whether a contact is teaching-primary or research-primary.

### ABSOLUTE NON-NEGOTIABLE OUTPUT RULES

These apply to EVERY SINGLE RESPONSE. No exceptions. Ever.

**RULE 1 — FILE DOWNLOADS: ALWAYS provide the cp command.**
After presenting any file for download, ALWAYS provide the bash command to copy it into the correct repo path, followed by the run command. Always in that order. ALWAYS. ALWAYS. ALWAYS. ALWAYS. ALWAYS.

Format (every time, no exceptions):
```bash
cp ~/Downloads/filename /Users/lisaswerling/RALPH/AI/macrosnaps/filename
```
Then the run command.

Never present a file without this. Never give only the run command. Never skip the cp step. ALWAYS. ALWAYS. ALWAYS.

**RULE 2 — URLs: ALWAYS format as clickable links.**
Every URL in every response must be a clickable markdown link. Never paste a bare URL. ALWAYS. ALWAYS. ALWAYS. ALWAYS. ALWAYS.

Example: [http://localhost:8080](http://localhost:8080) — never `http://localhost:8080` as plain text.


Since the site and app are live, all changes must be tested locally before pushing to git. Claude must always provide a local preview step before giving any git push command. Never combine build and push into a single command.

### Daily Bash Ritual
**Friday only -- run this first, before anything else:**
```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 forecast_server.py
```
Open `forecast_cms.html` in your browser, review and update forecasts, then close the server before proceeding.

Run in order, pasting output after each step:

```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps
python3 fetch_market_data.py
python3 sync_market_historical.py --apply
python3 sync_commodity_data.py --apply
python3 update_commodity_stories.py
python3 update_headlines.py
python3 update_metric_stories.py
```

Manual gate 1: open `headline_review.html` (via http://localhost:8080), load `HEADLINES_draft_YYYY-MM-DD.json`, review and edit, export `HEADLINES_approved_YYYY-MM-DD.json`.

Manual gate 2: open `metric_story_review.html` (via http://localhost:8080), load `METRICS_draft_YYYY-MM-DD.json`, review and edit, export `METRICS_approved_YYYY-MM-DD.json`.

```bash
python3 update_headlines.py --apply HEADLINES_approved_YYYY-MM-DD.json
python3 update_metric_stories.py --apply METRICS_approved_YYYY-MM-DD.json
python3 build.py
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 sync_edu.py
cd /Users/lisaswerling/RALPH/AI/macedu && git add -A && git commit -m "Daily sync YYYY-MM-DD" && git push origin main
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 audit_ritual.py
```

Note: to open review UIs locally without CORS errors, run `python3 -m http.server 8080` in the macrosnaps directory first, then use http://localhost:8080.

### Social Media Bash
Run immediately after the Daily Bash Ritual:

```bash
python3 digest_server.py
```

This starts the local server and automatically opens the MacroSnaps Digest UI (`digest_ui.html`) at `http://localhost:PORT`. From there: select format (Daily Post, Weekly Digest, or Substack Notes), generate, edit, and copy content for Substack, X, and LinkedIn. Note: `macrosnaps-digest.html` is an older redundant file -- ignore it.

### Outreach email (default)

Subject: MacroSnaps: a free macro resource for your students

Dear [Name],

I'm a former macro strategist. I've recently built MacroSnaps, a free resource covering live macro and market data across 12 major economies, with every metric explained at beginner, moderate, and expert levels.

I'd love to know if you think it could be useful for your students. I'm in soft launch, so I'm actively looking for feedback from people who know this material well.

macrosnaps.app/educators.html has the details.

Best wishes,
Ralph Lazar

### Tracking spreadsheet columns
Country | University | Rank | Name | Role | Email | Email Confidence | Sent Date | Reply Date | Reply Type | Follow-up Sent | Notes

Reply Type values: Positive / Negative / Neutral / No reply
Email Confidence values: High / Medium / Low

---

## MacroSnaps product overview

MacroSnaps (macrosnaps.app) is a free daily macro and markets dashboard covering 12 major economies with data explained at beginner / moderate / expert levels. Built by Ralph Lazar, former macro strategist at Goldman Sachs and fixed-income prop trader at CSFB. Educator landing page: macrosnaps.app/educators.html.

---

## Substack strategy

**Goal for first 3 months:** audience building only. No paywall, no monetisation pressure.

**Cadence: daily posts + weekly digest**

- Daily post: short, low-friction, almost verbatim from the pipeline's three-act global story output. Proves the pipeline is alive, creates a scrollable archive, feeds Substack's algorithm.
- Weekly digest: longer and more considered; what mattered this week, which countries moved, what surprised, what to watch next week.

Keep daily posts genuinely short.

**Funnel: glossary links + one CTA per post.** Every glossary term hyperlinked to live glossary on macrosnaps.app (first occurrence per post only). One explicit CTA at end of every post.

**Depth levels and future monetisation:** beginner free, moderate/expert behind paywall after 3 months.

**Voice:** Substack readers follow people, not products. A 2-3 sentence human intro each day (written by Ralph) is important.

**Promotion (first 3 months), in priority order:**
1. Personal outreach -- first 50-100 subscribers from known network
2. LinkedIn -- weekly post with chart or insight + link
3. Cross-recommendations on Substack
4. Twitter/X -- slow burn, worth maintaining for macro community
5. Ask early subscribers to forward to one person

What not to bother with in first 3 months: paid promotion, SEO, press outreach, ProductHunt-style launches.

Do not position against Bloomberg or data terminals. The competition is a good morning read, not a data subscription.

---

## Architecture notes (latest state)

Key invariants:
- sync_sheet.py --apply writes only annual forecast fields
- sync_monthly_actuals.py writes only the monthly_actuals field
- These two scripts must never touch each other's fields
- build.py fails with a clear error if value_at_generation differs from current value for any metric story

### Story formula (three-act global arc)
- Card 1 - The Trigger: one economic event or data print driving global attention
- Card 2 - Biggest Movers: which markets, currencies, or economies are reacting and how
- Card 3 - The Connection: what ties cards 1 and 2 together, the "so what" for the global picture

All three levels (beginner, moderate, expert) tell the same arc at different depths.

### Editorial principle: forecasts vs stories
Forecast values (source: Ralph's Google Sheet) are annual consensus views for 2026. They drive the metric value and weather icon. Stories should be written off recent data and trends, not off the forecast values.

### JSON file naming (as of Session 59)
- `harvest_YYYY-MM-DD.json` — raw web search data; internal only; consumed by `update_metric_stories.py`; never loaded in a UI
- `HEADLINES_draft_YYYY-MM-DD.json` — country card + global stories draft; loaded in `headline_review.html`
- `HEADLINES_approved_YYYY-MM-DD.json` — approved headlines; applied via `update_headlines.py --apply`
- `METRICS_draft_YYYY-MM-DD.json` — per-metric bullet stories draft; loaded in `metric_story_review.html`
- `METRICS_approved_YYYY-MM-DD.json` — approved metric stories; applied via `update_metric_stories.py --apply`

### MACRO-MONTHLY sheet (as of Session 60)
- Sheet ID: `1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI` (env var: `MACRO_MONTHLY_SHEET_ID`)
- Three tabs: Inflation, Unemployment, Policy_Rate
- Unemployment sources by country:
  - USA: FRED `UNRATE` (BLS, monthly)
  - CAN/JPN/DEU/FRA/ITA/RUS: IMF LS dataset (monthly)
  - GBR: FRED `LRHUTTTTGBM156S` (ONS via FRED, monthly)
  - BRA: IBGE SIDRA table 6381 (PNAD Contínua, monthly) — wired into `update_monthly_actuals.py`
  - ZAF: FRED `LRUNTTTTZAQ156S` (OECD quarterly, interpolated) — backfilled via `backfill_unemployment.py`
  - IND: World Bank `SL.UEM.TOTL.ZS` (annual, interpolated) — backfilled via `backfill_unemployment.py`
  - CHN: no free programmatic source — permanent blank
  - RUS 2000–2009: no free programmatic source — permanent blank

---

## Full session history

Session 62: Daily ritual completed 2026-03-31; sync_edu.py path fix (runs from macrosnaps repo, not macedu); Daily Bash Ritual updated.
Session 61: Daily ritual completed 2026-03-29; commodity stories migrated to bullet arrays; sync_market_historical.py/audit_ritual.py/build.py bug fixes; Brent Crude backfill complete; macedu deployed to Cloudflare Pages; commodity story prompt overhauled.
Session 60: MARKET-STATS daily append fixed (fetch_market_data.py patched; yf_ytd_and_level() added); Mar 16–27 backfill run across 12 country tabs (backfill_market_stats.py); bond yield patch script built (patch_bond_yields.py); MACRO-MONTHLY unemployment backfilled for IND/ZAF (backfill_unemployment.py) and BRA (update_bra_unemployment.py); BRA IBGE SIDRA wired into update_monthly_actuals.py; historical unemployment and policy rate gaps filled via backfill_historical_gaps.py (DEU/FRA unemployment 2000–2006, JPN policy rate 2000–2016, DEU/FRA/ITA policy rate 2000–2008 from hardcoded ECB MRO table); backfill --apply run (13 cells); MACRO_MONTHLY_SHEET_ID added to .env.
Session 59: Metric story pipeline fixed (Haiku truncation → 1 country per call → parallelised to 12 concurrent calls, 990s → 74s); JSON file renames (HEADLINES/METRICS); headline_review.html patched for bullets schema; build.py validator updated; Daily Bash Ritual updated.
Session 58: Forecast CMS added (forecast_server.py + forecast_cms.html); Friday pre-ritual rule added to Daily Bash Ritual.
Session 57: Favicon added (favicon.ico + favicon-192.png); favicon link tags added to macrosnaps-shell.html; X Card Validator confirmed icon picked up.
Session 56: Repo moved to /Users/lisaswerling/RALPH/AI/macrosnaps; MARKET_STATS_KEY_FILE env var added; node_modules scrubbed from macrosnaps and macedu repos; Daily Bash Ritual fixed (sync_edu.py before audit_ritual.py; macedu push added).
Session 55: macroeconomics.education data layer complete. sync_edu.py added to Daily Bash Ritual. macedu pushed to GitHub.
Session 54: US and UK educator outreach campaigns complete/paused per Ralph's instruction.
Session 53: US educator outreach ranks 55-51 complete; 10 contacts, 5 universities (Georgia Tech skip confirmed); LIVING_BRIEF updated; session prompt for ranks 50-1 created.
Session 52: Teaching-staff-first rule formalised; session prompt for ranks 55-1 revised.
Session 51: US educator outreach ranks 70-56 complete; 59 contacts, 15 universities; 3 CSV files produced.
Session 50: Social Media Bash documented; local preview rule added to standing rules.
Session 49: US educator outreach ranks 100-71 complete; 76 contacts, 30 universities; 5 CSV files produced.
Session 48: UK top 20 educator outreach complete (178 contacts); US top 100 outreach plan built.
Session 47: Educator cold email outreach campaign built; UK university macro contacts database started ranks 20-13.
Session 46: educators.html created; Twitter/OG meta tags added; Subscribe + Educators buttons moved to footer; #ping hash handler added; educator outreach strategy added to brief.
Session 45: build.py structural date fix; US to Commodities nav flash fixed.
[Earlier sessions: see full LIVING_BRIEF history for complete record]
