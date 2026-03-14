# MacroSnaps - Living Brief
Last updated: March 14, 2026 (Session 7: investigated JPN CPI series swap. Both CPALTT01JPM657N and JPNCPIALLMINMEI stop at Jun 2021 on FRED - same OECD MEI source cutoff. e-Stat (Statistics Bureau of Japan) has current data but requires a free API registration. Decision: accept the JPN CPI gap for now. No code changes made. populate_monthly_actuals.py and update_monthly_actuals.py remain unchanged with CPALTT01JPM657N in CPI_YOY_SERIES. If JPN CPI gap is prioritised post-launch, register at e-stat.go.jp/api/en and build a fetcher against table ID 0003427113.)

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

CRITICAL - PLAN BEFORE BUILDING: Never write code or make any edit without first presenting a clear plan of exactly what will change and why. Wait for explicit approval before proceeding. The word "go" is the signal to proceed. This applies to every change, no matter how small it seems.

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

Write in plain, natural English. Do not use em dashes or en dashes. Only use a standard hyphen (-) if a dash is genuinely needed. Prefer commas, periods, or parentheses instead. Before outputting any response, scan it for those characters. If found, rewrite those sentences. Output only the final corrected version. This rule applies to all responses including code comments and story content written into data.json.

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
- Write in UK English. Use British spelling throughout (e.g. "analyse" not "analyze", "colour" not "color", "realise" not "realize").
- Before outputting any story, scan it against every rule above and rewrite any sentence that fails. Output only the final corrected version.

This style guide must also be included verbatim in the system prompt used by `update_stories.py` when calling the Claude API.

**What I am working on today:**

[describe your task here]

### ...to here

---

## PART 1B - STORIES SESSION PROMPT (use this instead of the master prompt when doing a story rewrite session)
### Copy from here...

You are helping me rewrite stale metric stories for MacroSnaps, a daily global macro and markets dashboard.

I am uploading two files: `LIVING_BRIEF.md` and `data.json`. Read both in full before doing anything. The brief contains the full project reference and story writing rules. The data file contains all current metric values and existing story text.

**Your job this session:**

Rewrite the stories listed in the "Known value/story drift" section of the brief. These are metrics where the value has been updated but the story text still references old numbers.

For each metric, rewrite all three levels (beginner, moderate, expert) so they are consistent with the current `value` field in data.json.

**Before writing anything, present a plan:**
- List exactly which country/metric pairs you will rewrite
- Confirm the current value you will write to for each one
- Wait for me to say "go"

**Story writing rules (apply to every story at every level):**
- No em dashes or en dashes. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural.
- No hedging openers ("It is worth noting", "It is important to understand", "This reflects the fact that").
- No AI-typical sentence starters. Do not begin consecutive sentences with "This metric," "This reflects," or "This suggests."
- Vary sentence length deliberately. Mix short punchy sentences with longer ones.
- Write numbers as real and specific. "Inflation hit 8.4%" not "the inflation rate stands at 8.4%."
- No filler conclusions ("overall," "in summary," "taken together").
- No committee language. Write as if explaining to a smart friend.
- Write in UK English. Use British spelling throughout.
- Scan every story against these rules before outputting. Output only the final corrected version.

**Story length guidelines:**
- Beginner: 2-3 short sentences. No jargon. One plain-English explanation of what the number means for everyday life.
- Moderate: 3-4 sentences. Include one piece of context (historical comparison, regional comparison, or causal driver).
- Expert: 4-5 sentences. Include specific numbers, a directional signal, and one forward-looking implication.

**Output format:**

For each rewrite, output a JSON block that can be copied directly into data.json. Use this format exactly:

```json
"story": {
  "beginner": "...",
  "moderate": "...",
  "expert": "..."
}
```

After all rewrites are done, output a summary table of every country/metric pair that was updated.

Then update `LIVING_BRIEF.md` to clear the rewritten entries from the "Known value/story drift" section and make it available for download.

Equity Vol, FX Vol, Corp Spread, and Sov CDS have all been removed from the product entirely. Do not write or reference stories for any of these metrics.

**What I am working on today:** Rewriting stale metric stories. All current values are in data.json.

### ...to here

---

## PART 1C - COMMODITIES SESSION PROMPT (use this when updating commodity stories)
### Copy from here...

You are helping me update commodity stories for MacroSnaps, a daily global macro and markets dashboard.

I am uploading two files: `LIVING_BRIEF.md` and `data.json`. Read both in full before doing anything.

**Your job this session:**

Review the current `value` field for each of the 9 commodities in data.json and compare it to what the existing stories say. Rewrite any stories where the current price has moved meaningfully since the story was last written (roughly 5% or more for most commodities, 10% for more volatile ones like Natural Gas).

**The 9 commodities:** Oil (WTI), Natural Gas, Gold, Silver, Copper, Wheat, Corn, Iron Ore, Lithium.

**Before writing anything, present a plan:**
- List which commodities have meaningful drift between value and story text
- Show the current value vs what the story references
- Wait for me to say "go"

**Story writing rules:** Same as metric stories. No em dashes or en dashes. No passive voice. No hedging openers. Vary sentence length. Write numbers as real and specific. No filler conclusions. No committee language. Write in UK English.

**Story length guidelines:**
- Beginner: 2-3 sentences. What this commodity is and why its price matters to ordinary people.
- Moderate: 3-4 sentences. Include one driver of the current price level and one downstream effect.
- Expert: 4-5 sentences. Include specific price, directional trend, supply/demand driver, and one forward implication.

**Output format:** Same JSON block format as metric stories. After all rewrites, output a summary of what changed.

Then update `LIVING_BRIEF.md` to note the commodity story update date and make it available for download.

**What I am working on today:** Reviewing and updating commodity stories based on current prices in data.json.

### ...to here

---

## PART 2 - PROJECT REFERENCE

---

### What the project is

MacroSnaps is a daily dashboard that makes global macro and market data accessible to everyone, from curious beginners to seasoned professionals.

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

**Never modify** `_frozen_historical` or `_frozen_weatherGrid` inside any country in `data.json` by hand. Annual macro arrays (GDP Growth, Budget Deficit, Current Account) are maintained by `sync_sheet.py`. Monthly arrays are maintained by `refetch_historical.py`. To update annual data, edit the Macro-stats sheet and run `sync_sheet.py --apply`.

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

**Step 4. Append today's market data to MARKET-STATS sheet**

This fetches today's values for all 12 countries (equity index levels, FX rates, bond yields) and appends one row per country tab to the MARKET-STATS Google Sheet.
```bash
python3 update_market_sheet.py
```

Dry run first on any new machine or after a long gap:
```bash
python3 update_market_sheet.py --dry-run
```

**Step 4b. Sync market data from sheet to data.json**

This reads the latest row per country from MARKET-STATS, computes Stock Market YTD from index levels, and writes all 4 market metric values into data.json.
```bash
python3 sync_market_sheet.py --preview
python3 sync_market_sheet.py --apply
```

Always preview first. If the changes look correct, apply.

**Step 4c. Append new months to MACRO-MONTHLY sheet**

This checks the last date in each tab and appends any new months from FRED and BIS. Safe to run daily - exits cleanly if nothing is new.
```bash
python3 update_monthly_actuals.py
```

**Step 4d. Sync monthly actuals to data.json**

This reads the last 6 non-null months per country per series and writes the monthly_actuals block into data.json. Always preview first.
```bash
python3 sync_monthly_actuals.py --preview
python3 sync_monthly_actuals.py --apply
```

**Step 4e. Sync monthly historical arrays to data.json**

This reads the MACRO-MONTHLY sheet from Jan 2020 and writes _frozen_historical for Inflation, Unemployment, and Policy Rate across all 12 countries.
```bash
python3 sync_monthly_historical.py --apply
```

**Step 4f. Sync market historical arrays to data.json**

This reads the MARKET-STATS sheet from Jan 2020, resamples daily to monthly, and writes _frozen_historical for Stock Market, FX Rate, 10Y Bond Yield, and Yield Curve across all 12 countries.
```bash
python3 sync_market_historical.py --apply
```

**Step 5. Update commodity stories where prices moved**

This checks each commodity's current price against the price recorded when the story was last written. Any commodity that has moved past its threshold (10% for Natural Gas, 5% for all others) gets a fresh story written at all three levels. If nothing has moved, it exits in under a second.
```bash
python3 update_commodity_stories.py
```

**Step 6. Rewrite stories where values moved**

This diffs `data.json` against the last git commit, identifies metrics that changed past threshold, calls the Claude API, and rewrites stories for those metrics at all three levels.
```bash
python3 update_stories.py
```

**Step 7. Draft and review country + global headlines**

This calls the Claude API with web search enabled and drafts fresh country-level story bullets and global stories. It writes a preview file but does NOT touch data.json.
```bash
python3 update_headlines.py
```
Wait for the draft to complete (8-10 minutes, 13 API calls). Then open `headline_review.html` in your browser, load the draft file, review and edit each country and global, approve, and export `stories_approved_YYYY-MM-DD.json`.

Then apply the approved draft:
```bash
python3 update_headlines.py --apply stories_approved_YYYY-MM-DD.json
```

**Step 8. Build the output file**

This validates `data.json`, assembles `macrosnaps-globe.html`, saves a dated backup, and automatically commits and pushes to GitHub Pages.
```bash
python3 build.py
```
The build must say `BUILD SUCCESSFUL`. A successful build prints `✓ git commit` and `✓ git push` at the end. If either line shows a warning, push manually.

**Step 9. Verify the live site**

Wait about 60 seconds, then open:
```
https://ralphlazar.github.io/macrosnaps/macrosnaps-globe.html
```

**Quick-reference one-liner (after sheet sync is done):**
```bash
cd ~/Downloads/macrosnaps && python3 update_market_sheet.py && python3 sync_market_sheet.py --apply && python3 update_monthly_actuals.py && python3 sync_monthly_actuals.py --apply && python3 sync_monthly_historical.py --apply && python3 sync_market_historical.py --apply && python3 update_commodity_stories.py && python3 update_stories.py && python3 update_headlines.py && python3 build.py
```

---

### What the Google Sheet controls

**Macro-stats** is the single source of truth for all 6 annual macro metrics across all 12 countries. It is a separate Google Sheet from the old MacroSnaps_Forecasts_2026 sheet, which is now retired.

**Sheet ID:** `1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo`
**Sheet URL:** `https://docs.google.com/spreadsheets/d/1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo`
**Access:** Anyone with the link can view (no auth required, enables unauthenticated CSV export)

**Layout:** 12 tabs, one per country, named by 3-letter country code (USA, CAN, GBR, etc.). Each tab has years 2000-2025 as labelled columns, plus one unlabelled column immediately after that holds the 2026F forecast. Row 1 is the year header. Rows 2-7 are GDP_Growth, Inflation, Budget_Deficit, Current_Account, Unemployment, Policy_Rate.

**What sync_sheet.py writes to data.json:**

| Metric | Card value (2026F) | _frozen_historical written? |
|---|---|---|
| GDP Growth | Yes | Yes, 27 points (2000-2026F), bar chart |
| Budget Deficit | Yes | Yes, 27 points (2000-2026F), bar chart |
| Current Account | Yes | Yes, 27 points (2000-2026F), bar chart |
| Inflation (CPI) | Yes | No (monthly sparkline stays) |
| Unemployment | Yes | No (monthly sparkline stays) |
| Policy Rate | Yes | No (monthly sparkline stays) |

**Important:** The `value` field for macro metrics holds the 2026F year-end forecast, not the current live reading. For example, USA Policy Rate shows 3.25% (year-end forecast) even though the Fed funds rate is currently higher. Stories should reference both the current reading and the forecast where relevant.

**Important:** When a forecast changes in the Macro-stats sheet, run `sync_sheet.py --apply`. It updates both the card value and the full 27-point historical array automatically. No manual array editing is needed.

**What the sheet does NOT control:** Market metrics (handled by `fetch_market_data.py`), stories (handled by `update_stories.py`), commodity data, global stories, metricBriefs, or monthly/quarterly historical data.

---

### What the MARKET-STATS sheet controls

**MARKET-STATS** is the source of truth for all 4 daily market metrics across all 12 countries. It replaces `fetch_market_data.py` for these series.

**Sheet ID:** stored in `.env` as `MARKET_STATS_SHEET_ID`
**Access:** via service account (key file at `~/Downloads/macrosnaps/market-stats-key.json`, never commit this file)

**Layout:** 12 tabs, one per country, named by 3-letter country code. Each tab has daily rows from 2000-01-01 with 6 columns:

```
Date | Stock_Market_Index | FX_Rate | Bond_Yield_10Y | Bond_Yield_3M | Yield_Curve
```

**Sources:**
- Stock index levels: Yahoo Finance (raw closing price, not YTD %)
- FX rates: Yahoo Finance
- 10Y bond yields: FRED (DGS10 for USA, IRLTLT01XXM156N monthly series for G7, blank for CHN/IND/BRA/RUS)
- 3M bond yields: FRED DGS3MO for USA, IR3TIB01XXM156N monthly series for CAN/GBR/JPN/DEU/FRA/ITA/ZAF, blank for CHN/IND/BRA/RUS
- Yield Curve: (Bond_Yield_10Y - Bond_Yield_3M) * 100, in basis points. 8 countries (USA/CAN/GBR/JPN/DEU/FRA/ITA/ZAF).

**Known gaps (expected, not bugs):**
- 3M yields and Yield Curve: blank for CHN, IND, BRA, RUS (no FRED series)
- CHN, IND, BRA: no bond yield data at all
- RUS equity: truncates at June 2024 (MOEX delisted on Yahoo post-sanctions). No forward-fill past last real observation.
- ZAF equity: yfinance history starts ~2013, earlier rows blank
- FX: most countries start ~2003-2004, earlier rows blank

**What sync_market_sheet.py writes to data.json:**
- Stock Market YTD: computed at read time as (latest index - first trading day of year) / first trading day * 100
- FX Rate: latest non-blank FX_Rate value
- 10Y Bond Yield: latest non-blank Bond_Yield_10Y value
- Yield Curve: latest non-blank Yield_Curve value (bps)

**Three scripts:**

| Script | Purpose | When to run |
|---|---|---|
| `populate_market_sheet.py` | One-time full backfill from 2000-01-01 | Once, or to re-backfill after changes |
| `update_market_sheet.py` | Appends today's row to all 12 tabs | Daily (step 4 of ritual) |
| `sync_market_sheet.py` | Reads sheet, writes values to data.json | Daily (step 4b of ritual) |

**Security:** `market-stats-key.json` must never be committed. It is in `.gitignore`. If accidentally committed, delete the key in Google Cloud console, generate a new one, scrub history with `git filter-repo`, and force push.



### What the MACRO-MONTHLY sheet controls

**MACRO-MONTHLY** is the source of truth for monthly actuals for Inflation (CPI YoY %), Unemployment (%), and Policy Rate (%) across all 12 countries from Jan 2000.

**Sheet ID:** `1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI`
**Access:** via service account (same market-stats-key.json as MARKET-STATS)
**Env var:** `MACRO_MONTHLY_SHEET_ID`

**Layout:** 3 tabs (Inflation, Unemployment, Policy_Rate). Column A = date (YYYY-MM-01), columns B-M = one per country in order: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS.

**Sources:**
- Inflation: FRED CPI index series per country, YoY % computed as (current / 12-months-ago - 1) x 100
- Unemployment: FRED monthly harmonised series (UNRATE for USA, LRHU/LRUNN prefix for G7). CHN, IND, ZAF, RUS: no reliable monthly FRED series, columns blank.
- Policy Rate: FEDFUNDS (USA), BOERUKM (GBR), ECBMRRFR daily resampled to monthly (DEU/FRA/ITA), IRSTCB01 series for others.

**Three scripts:**

| Script | Purpose | When to run |
|---|---|---|
| `populate_monthly_actuals.py` | One-time backfill from Jan 2000 | Done. Re-run only to rebuild from scratch. |
| `update_monthly_actuals.py` | Appends new months from FRED | Daily (step 4c of ritual, after market sheet update) |
| `sync_monthly_actuals.py` | Reads last 6 non-null months, writes monthly_actuals to data.json | Daily (step 4d of ritual) |

**What sync_monthly_actuals.py writes to data.json (per country):**
```json
"monthly_actuals": {
  "inflation": [{"month": "2026-02", "value": 3.1}, ...],
  "unemployment": [...],
  "policy_rate": [...]
}
```
6 entries per series, newest first. Null/blank cells skipped. Field is story context only, never displayed in UI.

---

The following decisions were made in a planning session on March 13, 2026. Implementation starts March 14.

**1. Remove Corp Spread and Sov CDS (pre-launch)**

Corp Spread and Sov CDS are being removed from the dashboard before launch. Free data sources for these metrics are unreliable across 12 countries, and legitimate sources (Markit, Bloomberg) are paywalled. The 4 remaining market metrics (Equity, FX Rate, Bond Yield, Yield Curve) are price-based, source-reliable, and tell a coherent story without them. Corp Spread and Sov CDS may return post-launch once a proper data solution is identified. This follows the same pattern as the Equity Vol / FX Vol removal on March 13, 2026.

**2. Google Sheet for market data (4 series, daily, 2020 onwards)**

The 4 remaining market metrics will move to a Google Sheet with daily granularity from 2020. This gives full visibility into the data and full control over the source. yfinance is the right source for all 4 (pure market prices with reliable tickers). The sheet will feed into data.json via an extension of `sync_sheet.py`. Architecture TBD at build time.

**3. Google Sheet for monthly macro actuals (3 series)**

Inflation, Unemployment, and Policy Rate will get a separate monthly sheet from 2020 onwards. This lives as a separate tab or sheet from the annual Macro-stats data given the different granularity and update rhythm. Sources: FRED for most countries, ILO for harder emerging market unemployment series (ZAF, IND etc), central bank websites for Policy Rate edge cases.

**4. Annual forecast vs monthly actuals: architecture**

The annual forecast remains the single source of truth for card values, weather icons, and the proprietary view. It never changes based on monthly actuals.

Monthly actuals are story fuel only. They live in data.json as a separate field (e.g. `monthly_actuals`), invisible in the UI, but passed as context to both `update_stories.py` and `update_headlines.py`. The story writer can reference the most recent monthly print and note any tension with the annual forecast.

Correct approach in a story: "February CPI came in at 3.1%, above target, but full-year inflation is still expected to settle at 2.3% as base effects kick in mid-year." The card always shows the annual forecast. The story can reference both.

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

---

### Current content state (March 11, 2026)

**Per-metric stories (beginner / moderate / expert)**

All per-metric stories are complete across all 12 countries and all 3 levels (10 metrics x 12 countries = 120 stories). Equity Vol, FX Vol, Corp Spread, and Sov CDS have all been removed from the product entirely.

**Other content (all 12 countries)**
- Country-level stories (3 bullets per level): complete for all 12, last updated March 10, 2026
- metricBriefs (short summaries per metric): complete for all 12
- fxRegime descriptions (3 levels): complete for all 12

**Commodity stories (beginner / moderate / expert)**
All 9 commodities have a `story` object with beginner, moderate, and expert keys. Commodity prices are updated automatically by `fetch_market_data.py` daily. Stories are now also updated automatically by `update_commodity_stories.py`, which runs daily and rewrites any commodity whose price has moved past threshold (10% for Natural Gas, 5% for all others). All 9 stories bootstrapped and `storyWrittenAtPrice` set on March 12, 2026. No manual story session needed unless you want to override the automated output.

**Global stories (March 10, 2026)**
- Slot 1: Oil Swings Wildly as Iran War Dominates Markets (WTI $119 to $88 intraday)
- Slot 2: US Lost 92,000 Jobs in February (stagflation signal, Fed stuck)
- Slot 3: Stock Markets Bounce Back on Peace Hopes (S&P +0.8%, Gold $5,145)

---

### Known value/story drift (as of March 11, 2026)

These are metrics where the live value has been updated by `fetch_market_data.py` but the stories still reference older numbers. Use the Stories Session Prompt in Part 1B to clear this backlog. Do not fix these manually outside a dedicated story session.

**USA - values as of March 11 dry run:**

| Metric | Current value | What stories say |
|---|---|---|
| Stock Market YTD | -1.1% | +2% |
| 10Y Bond Yield | 4.12% | 4.28% |
| Yield Curve | +52bps | +8bps |
| USD/DXY | 99.1 | 104.2 |
| Policy Rate | Rewritten March 11, 2026 | |
| Budget Deficit | Rewritten March 11, 2026 | |

**CAN - values as of March 11 dry run:**

| Metric | Current value | What stories say |
|---|---|---|
| GDP Growth | Rewritten March 11, 2026 | |
| Stock Market YTD | +4.1% | 6.8% |
| 10Y Bond Yield | 3.40% | (check story) |
| Yield Curve | +121bps | +30bps |
| CAD/USD | 0.74 | (check story) |

**Other countries - live values as of March 11 dry run:**

| Country | Metric | Current value |
|---|---|---|
| GBR | Stock Market YTD | +3.8% |
| GBR | 10Y Bond Yield | 4.45% |
| GBR | Yield Curve | +74bps |
| GBR | GBP/USD | 1.34 |
| JPN | Stock Market YTD | Rewritten March 11, 2026 |
| JPN | 10Y Bond Yield | 2.24% |
| JPN | Yield Curve | +112bps |
| JPN | USD/JPY | 158.6 |
| DEU | Stock Market YTD | -3.8% |
| DEU | 10Y Bond Yield | 2.81% |
| DEU | Yield Curve | +81bps |
| DEU | EUR/USD | 1.1589 |
| FRA | Stock Market YTD | -2.2% |
| FRA | 10Y Bond Yield | 3.53% |
| FRA | Yield Curve | +153bps |
| ITA | Stock Market YTD | -1.4% |
| ITA | 10Y Bond Yield | 3.49% |
| ITA | Yield Curve | +149bps |
| CHN | Stock Market YTD | +2.7% |
| CHN | USD/CNY | 6.86 |
| IND | Stock Market YTD | -9.8% |
| IND | 10Y Bond Yield | 6.73% |
| IND | Yield Curve | +123bps |
| IND | USD/INR | 92.04 |
| ZAF | Stock Market YTD | +0.5% |
| ZAF | 10Y Bond Yield | 8.62% |
| ZAF | Yield Curve | +187bps |
| ZAF | USD/ZAR | 16.38 |
| BRA | Stock Market YTD | +15.1% |
| BRA | USD/BRL | 5.16 |
| RUS | USD/RUB | 79.1 |

**Minor rounding gaps only (not material):** CHN GDP, IND GDP, ZAF GDP. All within 0.2-0.5pp of story figure. Low priority.

---

### fetch_market_data.py

The script lives in `~/Downloads/macrosnaps/`. It pulls all 4 market metrics and writes `value` and `last_updated` fields directly into `data.json`. It never touches historical arrays, stories, macro metrics, or any other field.

**Metrics fetched:**

| Metric | Source | Notes |
|---|---|---|
| Stock Market YTD | Yahoo Finance | YTD % change from Jan 1 close |
| 10Y Bond Yield | FRED | Daily series per country |
| Yield Curve | FRED (derived) | 10Y minus short rate |
| FX pair | Yahoo Finance | Varies by country |
| Commodity prices (9) | Yahoo Finance | Continuous futures tickers (CL=F, BZ=F, NG=F, GC=F, SI=F, HG=F, ZW=F, ZC=F, ZS=F); updates price, change (YoY %), spark (rolling 12-point array), and asOf |

**Known gaps (expected, not bugs):**
- RUS: `IMOEX.ME` is delisted on Yahoo. Stock Market YTD will always fail. FX comes through.
- CHN and BRA: No FRED 10Y series. 10Y Bond Yield and Yield Curve will always fail.

**Dry run results (March 14, 2026):** Corp Spread and Sov CDS removed. 4 market metrics now fetched per country (Stock Market YTD, 10Y Bond Yield, Yield Curve, FX pair). Known gaps: RUS Stock Market YTD, CHN/BRA 10Y Bond Yield and Yield Curve.

**Requirements (one-time setup):**
```
pip3 install requests yfinance python-dotenv
```

**FRED API key** (free): https://fred.stlouisfed.org/docs/api/api_key.html

The `.env` file lives at `~/Downloads/macrosnaps/.env` and contains:
```
FRED_API_KEY=your_key_here
MACRO_STATS_SHEET_ID=1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo
```

This file exists as of March 11, 2026.

**To run (dry run first):**
```bash
cd ~/Downloads/macrosnaps
python3 fetch_market_data.py --dry-run
python3 fetch_market_data.py
```

**After a successful live run:**
```bash
python3 build.py && git add -A && git commit -m "Daily market update $(date +%Y-%m-%d)" && git push origin master
```

---

### Historical chart data state (updated March 14, 2026)

**Chart data ownership - which script writes which metric:**

| Metric | Owner script | Data window | Format |
|---|---|---|---|
| GDP Growth | sync_sheet.py | 2000-2026F, 27 points | Annual bar |
| Budget Deficit | sync_sheet.py | 2000-2026F, 27 points | Annual bar |
| Current Account | sync_sheet.py | 2000-2026F, 27 points | Annual bar |
| Inflation (CPI) | sync_monthly_historical.py | Jan 2020 onwards, ~63-75 points | Monthly line |
| Unemployment | sync_monthly_historical.py | Jan 2020 onwards, ~70-73 points | Monthly line |
| Policy Rate | sync_monthly_historical.py | Jan 2020 onwards, ~74-75 points | Monthly stepped line |
| Stock Market YTD | sync_market_historical.py | Jan 2020 onwards, ~75 points | Monthly line (raw index, indexLabel:true) |
| FX Rate | sync_market_historical.py | Jan 2020 onwards, ~75 points | Monthly line |
| 10Y Bond Yield | sync_market_historical.py | Jan 2020 onwards, ~75 points | Monthly line |
| Yield Curve | sync_market_historical.py | Jan 2020 onwards, ~75 points | Monthly line (zeroLine:true) |

**Important:** `refetch_historical.py` is no longer the source of truth for Inflation, Unemployment, Policy Rate, Stock Market, FX, Bond Yield, or Yield Curve. Do not run it for those metrics. It still owns the commodity _frozen_historical arrays.

**Macro metric charts - annual series (GDP Growth, Budget Deficit, Current Account):**

All three have 27-point arrays covering 2000-2026F from Macro-stats (IMF WEO). Written exclusively by `sync_sheet.py`. When forecasts change, run `sync_sheet.py --apply`.

**Macro metric charts - monthly series (Inflation, Unemployment, Policy Rate):**

Now sourced from MACRO-MONTHLY sheet via `sync_monthly_historical.py`. Data from Jan 2020 onwards (~63-75 points per country). Written daily at step 4e of the ritual.

**Market metric charts (Stock Market, FX, Bond Yield, Yield Curve):**

Now sourced from MARKET-STATS sheet via `sync_market_historical.py`. Daily rows resampled to monthly end-of-month. Data from Jan 2020 onwards (75 points). Written daily at step 4f. sync_market_historical.py --apply completed March 14, 2026 (Session 6). FX Rate historical also populated in this run (was missing). NOTE: 75 months of history vs the previous 120-month refetch_historical.py arrays. To extend to 10 years, change START_DATE in sync_market_historical.py from 2020-01-01 to 2016-01-01 (sheet data exists from 2000-01-01).

**Tooltip chart range buttons (country metrics):**

Changed from 1Y/2Y/5Y/10Y to 1Y/2Y/5Y/All. All is active by default (data-r="999"). Commodity tooltip unchanged (1Y/2Y/5Y/All with All at 114 points).

**Per-country chart population (`_frozen_historical`):**

| Country | Charts populated | Notes |
|---|---|---|
| USA | 12/12 | All metrics covered |
| CAN | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill |
| GBR | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill |
| JPN | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill. Inflation: only 18 points (FRED series dead after Jun 2021) - fix in Session 7 |
| DEU | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill |
| FRA | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill |
| ITA | 12/12 | Yield Curve: covered after Bond_Yield_3M backfill |
| CHN | 9/12 | Unemployment: no source. 10Y Bond Yield: no FRED source. Yield Curve: no 3M source on FRED |
| IND | 9/12 | Unemployment: no source. 10Y Bond Yield: no FRED source. Yield Curve: no 3M source on FRED |
| ZAF | 11/12 | Unemployment: no monthly source. Yield Curve: covered after Bond_Yield_3M backfill |
| BRA | 10/12 | Unemployment: PME dead, no replacement. Yield Curve: no 3M source on FRED |
| RUS | 8/12 | Unemployment: no post-sanctions FRED source. Stock Market: truncates Jun 2024. Yield Curve: blank (no post-2022 data). FX: available |

**Known data quality flags:**
- JPN Inflation: only 18 points (Jan 2020 to Jun 2021). CPALTT01JPM657N dead after Jun 2021. Fix planned for Session 7: switch to JPNCPIALLMINMEI (OECD index level) with .pct_change(12)*100 YoY transform.
- RUS Yield Curve: blank. No post-2022 short rate data anywhere.
- Budget Deficit arrays are empty for 9 countries (CAN, GBR, DEU, FRA, CHN, IND, ZAF, BRA, RUS). A single forecast point with no history is meaningless as a chart, left empty intentionally.

---

### The 12 metrics per country

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate.

**Market (4):** Stock Market YTD, 10Y Bond Yield, Yield Curve, [FX pair - varies by country].

Note: Equity Vol, FX Vol, Corp Spread, and Sov CDS were all removed from the product in March 2026. Equity Vol and FX Vol had data quality issues. Corp Spread and Sov CDS had no reliable free source across all 12 countries. All four may return post-launch if a proper data solution is found. None exist in data.json, the shell, or any pipeline script.

---

### How metric stories work

Stories live in `data.json` inside each metric entry as a `story` object with `beginner`, `moderate`, and `expert` keys.

At load time the shell reads these into the `metricStories` object (line 5605 of shell).

When a user clicks a metric, `renderMTT()` (line 6542) builds the tooltip. The story appears inline between the value and the chart, with no header label. CSS class is `tt-metric-story` (line 165 of shell).

The tooltip order is: metric name, country + value, story, chart, explanation/bluf, FX regime (if applicable), compare button.

**Stories are written and maintained by AI.** `update_stories.py` (built March 11, 2026) diffs data.json against the last git commit, identifies metrics that changed past a configurable threshold, calls the Claude API, and rewrites the affected stories at all three levels in one pass. Do not write or edit stories by hand outside a dedicated stories session.

---

### Architecture decisions and why

**Google Sheet for macro metrics.** The sheet holds the 6 macro metrics per country. `sync_sheet.py` pulls from the sheet and writes `data.json`. The sheet is updated manually but infrequently, when year-end consensus forecasts change.

**fetch_market_data.py for live market metrics.** Pulls all 4 market metrics (Stock Market YTD, 10Y Bond Yield, Yield Curve, FX pair) from Yahoo Finance and FRED daily. Built and verified March 11, 2026. Equity Vol and FX Vol removed March 13, 2026. Corp Spread and Sov CDS removed March 14, 2026.

**update_stories.py for story maintenance.** Diffs data.json against the last git commit to detect meaningful value changes, then calls the Claude API to rewrite stories for affected metrics. Runs after both sync_sheet.py and fetch_market_data.py so it catches all changes in one pass. Built and verified March 11, 2026. Requires ANTHROPIC_API_KEY in .env.

**update_commodity_stories.py for commodity story maintenance.** Runs daily after `fetch_market_data.py`. Compares each commodity's current `price` field against `storyWrittenAtPrice` stored in `data.json`. Rewrites stories at all three levels for any commodity that has moved past its threshold (10% for Natural Gas, 5% for all others). Applies directly to `data.json` with no draft or review step. Built and verified March 12, 2026.

**No CMS.** Pre-launch solo workflow. JSON plus build script is faster to iterate with than any external system.

**GitHub Pages for hosting.** Repo is public at https://github.com/ralphlazar/macrosnaps. Deploy from master branch, root folder. The built HTML file is self-contained (data inlined) so no build step is needed on the server side.

**Git for version history.** Commit after every feature or meaningful change. `update_stories.py` uses git diff to detect what has changed since the last commit, so committing consistently is essential for correct story rewrite targeting.

---

### Google Sheet country data build (complete and integrated, March 13, 2026)

This was a standalone research session that built clean, IMF WEO-sourced data tables for all 12 countries covering the 6 macro metrics from 2000 to 2026F. The tables were pasted into the Macro-stats Google Sheet and are now the live data source for all annual macro metrics via `sync_sheet.py`.

**Status: complete and integrated for all 12 countries.**

| Country | Completed | Notes |
|---|---|---|
| USA | March 13 | BLS, BEA, OMB sources; Q4-over-Q4 GDP |
| CAN | March 13 | IMF WEO throughout; BoC overnight rate |
| GBR | March 13 | IMF WEO; BoE base rate; ONS sources noted |
| JPN | March 13 | IMF WEO; BoJ uncollateralised call rate; VAT flag 2014 |
| DEU | March 13 | IMF WEO; ECB MRO; Hartz IV and Schwarze Null flags |
| FRA | March 13 | IMF WEO; ECB MRO; bouclier tarifaire flag |
| ITA | March 13 | IMF WEO; ECB MRO; Superbonus 110% flag |
| CHN | March 13 | IMF WEO; PBoC LPR splice at 2019; major data quality flags |
| IND | March 13 | IMF WEO; RBI repo rate; PLFS/WPI-CPI/CSO methodology breaks |
| ZAF | March 13 | IMF WEO; SARB repo rate; rand crisis and narrow vs expanded unemployment flags |
| BRA | March 13 | IMF WEO; BCB Selic rate (confirmed 15.00% at Dec 2025 COPOM); PME/PNADC unemployment break |
| RUS | March 13 | IMF WEO; CBR key rate (confirmed 16.00% at Dec 19, 2025; cut to 15.50% Feb 13, 2026); refinancing/key rate splice at 2013; post-2022 data reliability flag |

**Source methodology (standard for all countries unless noted above):**
- GDP Growth: Annual real % change, calendar year average (IMF WEO)
- Inflation: Annual average CPI, all-items (IMF WEO)
- Unemployment: Annual average, ILO harmonized rate (IMF WEO)
- Budget Deficit: General government net lending/borrowing % GDP; positive = surplus (IMF WEO)
- Current Account: Current account balance % GDP (IMF WEO)
- Policy Rate: Respective central bank official rate at year-end

---

### Vulnerabilities and mitigations

| Vulnerability | Status | Mitigation |
|---|---|---|
| No version history | Fixed | Git initialized. Commit after every build. |
| JSON corruption from manual edits | Fixed | Run `python3 build.py --validate-only` before editing. Build script also validates on every run. |
| Forgetting to rebuild | Habit-dependent | Never call a task done until build has run and output copied. |
| No preview step | Fixed | `sync_sheet.py` preview mode shows all changes before anything is written. |
| Headline stories applied without review | Fixed | `update_headlines.py` writes a draft file only. `headline_review.html` is a browser tool for reviewing, editing, and approving before applying. |
| Spurious git diffs from build timestamps | Fixed | Build script stamps `_meta` in memory only. `data.json` on disk is never written by the build. |
| Daily backup only | Covered | Git provides full history. Build script saves daily backup to `backups/` and prunes after 30 days. |
| Historical chart data incomplete | Largely resolved | `refetch_historical.py` restored all charts except genuine data voids. |
| Stale or missing market data | Resolved | `fetch_market_data.py` built and verified March 11, 2026. Corp Spread and Sov CDS removed March 14, 2026. Commodity prices automated March 12, 2026. |
| Manual story maintenance burden | Resolved | `update_stories.py` built March 11, 2026. Rewrites stories for any metric that moves past threshold. |
| Weather Map showing stale forecast values | Fixed | Shell reads the 2026F column from live metrics at runtime. Historical years stay frozen. |
| Value/story drift between daily market updates and story rewrites | Resolved | `update_stories.py` built March 11, 2026. Run after each data fetch to keep stories current. |
| Current Account displayed in absolute dollars | Fixed 2026-03-10 | All CA historical arrays converted to % of GDP using IMF WEO denominators. 2026F appended as final point. |
| Macro chart 2026F point missing | Fixed 2026-03-10 | 2026F forecast appended as final point to all macro historical arrays with existing data. |
| Country card weather icon was static (read from data.json `weather` field) | Fixed 2026-03-13 | Shell now computes weather at runtime from each country's live GDP Growth value. Thresholds match the GDP Weather Map: >=3% sunny, 0-3% cloudy, <0% stormy. Falls back to `data.json` field only if GDP is missing. The `weather` field in data.json is now a fallback only and does not need to be maintained. |
| Chart tooltip title showed "True" on stock market charts | Fixed 2026-03-13 | `histEntry.indexLabel` is a boolean flag used for number formatting. It was being used as the chart title via a short-circuit `||`, so `true` rendered as "True". Removed `histEntry.indexLabel` from the title expression entirely. |
| Chart tooltip title showed "5-Year History" despite 10-year data | Fixed 2026-03-13 | Fallback label in `renderMTT()` updated from "5-Year History" to "10-Year History" to match the actual data window. |
| 10Y country chart range button appeared broken | Fixed 2026-03-12 | monthlyLabels in shell-frozen had 180 entries (Jan 2011–Dec 2025) but globe.html had been built when it was only 60 entries, so slice(-120) and slice(-60) returned identical arrays. Fixed by extending monthlyLabels to 192 entries (Jan 2011–Dec 2026). Whenever historical data is refetched into future months, extend monthlyLabels to match. |
| Commodity tooltips showed only annual price bars | Fixed 2026-03-13 | showCommodityMTT was wired to item.annual (16 annual points) and ignored item._frozen_historical.v (114 monthly points). Fixed by adding renderCommodityMonthlyChart and wiring the tooltip to use _frozen_historical with 1Y/2Y/5Y/All range buttons. Annual chart retained as fallback. |
| No .env file | Fixed 2026-03-11 | .env created at ~/Downloads/macrosnaps/.env with FRED_API_KEY. |
| market-stats-key.json committed to repo | Resolved 2026-03-14 | Key deleted and regenerated. File scrubbed from git history via filter-repo and force pushed. Added to .gitignore. Never commit this file. |
| .env.save committed to repo | Resolved 2026-03-14 | Anthropic API key regenerated. .env.save scrubbed from git history. Added to .gitignore. |

---

### Key shell locations

| Thing | Location |
|---|---|
| `.tt-metric-story` CSS | Line 165 |
| `metricDisplayLabels` in `_frozen` | Line ~5229 |
| `metricStories` object declaration | Line 5605 |
| `parseLiveVal()` helper | Line 5613 |
| Country card weather computed from GDP | Line 5496 (inline IIFE inside countries map) |
| `metricStories` populated from data | Line 5637 |
| `renderMTT()` function | Line 6542 |
| Metric story HTML built | Line 6581-6582 |
| Full tooltip render string | Line 6589 |
| `historicalData` populated from `_frozen_historical` | Line 5638 |
| Weather grid population (live override) | Line 5646 |
| `window.__MACROSNAPS_DATA__` injected by build | Before `</head>` in built output |

---

### update_commodity_stories.py

The script lives in `~/Downloads/macrosnaps/`. It runs as part of the daily ritual after `fetch_market_data.py`. It checks each commodity's current `price` against `storyWrittenAtPrice` in `data.json` and rewrites stories for any that have moved past threshold.

**Thresholds:**

| Commodity | Threshold |
|---|---|
| Natural Gas | 10% |
| All others | 5% |

**Fields written to each commodity in `data.json`:**
- `story.beginner.text`, `story.moderate.text`, `story.expert.text` - rewritten story
- `storyWrittenAtPrice` - price at time of last write, used for future drift checks
- `storyUpdatedDate` - datestamp of last rewrite

**First-run behaviour:** Any commodity missing `storyWrittenAtPrice` is treated as needing a rewrite, bootstrapping the state. All 9 commodities bootstrapped March 12, 2026.

**Requirements:**
```
pip3 install anthropic python-dotenv
```

**ANTHROPIC_API_KEY** must be set in `.env`.

**To run:**
```bash
cd ~/Downloads/macrosnaps
python3 update_commodity_stories.py
```

---

### sync_monthly_historical.py

The script lives in `~/Downloads/macrosnaps/`. Reads the MACRO-MONTHLY Google Sheet from Jan 2020 onwards and writes `_frozen_historical` arrays into `data.json` for Inflation (CPI), Unemployment, and Policy Rate across all 12 countries. Replaces `refetch_historical.py` as the source of truth for these three metrics.

**Auth:** same `market-stats-key.json` service account as `sync_market_sheet.py`. `MACRO_MONTHLY_SHEET_ID` must be in `.env`.

**Data window:** Jan 2020 to latest available. Typically 63-75 points per country per metric.

**Known gaps written as empty arrays:**
- CHN Unemployment, IND Unemployment, BRA Unemployment: no reliable source
- JPN Inflation: only 18 points (Jan 2020 to Jun 2021). All FRED and IMF monthly series for JPN CPI are dead after Jun 2021. Known gap, post-launch fix needed.

**To run:**
```bash
python3 sync_monthly_historical.py          # preview
python3 sync_monthly_historical.py --apply  # write to data.json
```

---

### sync_market_historical.py

The script lives in `~/Downloads/macrosnaps/`. Reads the MARKET-STATS Google Sheet from Jan 2020 onwards, resamples daily rows to monthly end-of-month, and writes `_frozen_historical` arrays into `data.json` for Stock Market YTD (raw index, `indexLabel:true`), FX Rate, 10Y Bond Yield, and Yield Curve across all 12 countries. Replaces `refetch_historical.py` as the source of truth for these four metrics.

**Auth:** same `market-stats-key.json` service account. `MARKET_STATS_SHEET_ID` must be in `.env`.

**Data window:** Jan 2020 to latest available. Typically 75 points per country per metric.

**Known gaps written as empty arrays:**
- CHN/IND/BRA 10Y Bond Yield and Yield Curve: no FRED source
- RUS Yield Curve: blank (no post-2022 short rate data)
- RUS Stock Market: truncates at June 2024 (MOEX delisted on Yahoo post-sanctions)

**NOTE:** First applied March 14, 2026 (Session 6) after Bond_Yield_3M fix. 75 months of history written for all market metrics. To extend to 10 years, change START_DATE from 2020-01-01 to 2016-01-01.

**To run:**
```bash
python3 sync_market_historical.py          # preview
python3 sync_market_historical.py --apply  # write to data.json
```

---

The script lives in `~/Downloads/macrosnaps/`. It pulls data from FRED and Yahoo Finance and writes `_frozen_historical` into `data.json` in place. It never touches any other field.

**Data windows (as of March 12, 2026):**
- Monthly metrics (Inflation, Unemployment, Policy Rate, 10Y Bond Yield, Yield Curve, Stock Market, FX): 120 points (10 years)
- Annual metrics (GDP Growth, Budget Deficit): 10 years
- Current Account: up to 10 years, expressed as % of GDP (converted natively using World Bank nominal GDP series)
- Commodities: 114-120 monthly closes per commodity via Yahoo Finance continuous futures

**Current Account % GDP conversion:**
Uses World Bank nominal GDP series `MKTGDP[ISO2]A646NWDB` via FRED. Annual CA sum (millions USD) is divided by GDP (converted to millions USD) for each matched year. Years where World Bank data is not yet published (typically the most recent year) are skipped gracefully. No manual re-conversion is needed after running this script.

**Commodity historical (as of March 12, 2026):**
All 9 commodities get `_frozen_historical` written to each item in `data.commodities.items`. Tickers: WTI=CL=F, Brent=BZ=F, NatGas=NG=F, Gold=GC=F, Silver=SI=F, Copper=HG=F, Wheat=ZW=F, Corn=ZC=F, Soybeans=ZS=F.

**Unfetchable series (as of March 2026)**

The table below is the definitive record of what `refetch_historical.py` cannot populate. All series marked "blanked" have `{"v": []}` written explicitly so the chart shows nothing rather than stale or misleading data.

| Metric | Country | Status | Reason |
|---|---|---|---|
| Yield Curve | RUS | Blanked | Post-sanctions FRED gaps leave only 42 points; chart date labels shift by view length, producing a misleading display |
| Stock Market | RUS | Truncated at Jun 2023 | Yahoo Finance stopped publishing MOEX data post-sanctions. 88 real months retained, truncation visually obvious |
| Unemployment | CHN, IND | No data | Not available on FRED or OECD |
| 10Y Bond Yield | CHN, IND | No data | Not available on FRED |
| Yield Curve | CHN, IND | No data | Derived from 10Y - missing |
| Policy Rate | CHN | Blanked | PBOC rate not on FRED (non-OECD member); IRSTCI01CNM156N returns no data |
| GDP Growth | RUS | No data | FRED series unavailable post-sanctions |
| Unemployment | RUS | No data | FRED series unavailable post-sanctions |
| USD/RUB | RUS | Blanked | DEXRUUS discontinued on FRED post-sanctions; explicitly blanked via COUNTRY_VOID_METRICS |

**Requirements (one-time setup):**
```
pip3 install requests yfinance python-dotenv
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
- `FORCE_OVERWRITE = True` - re-fetches everything on every run (set to False to skip already-populated series)
- `MIN_POINTS = 5` - existing point count that qualifies as already populated

---

### Pending work (priority order)

1. ~~**Build tooltip historical charts from Google Sheets (Jan 2020 onwards).**~~ Done March 14, 2026 (Session 5). Two scripts built: `sync_monthly_historical.py` reads MACRO-MONTHLY and writes _frozen_historical for Inflation, Unemployment, Policy Rate. `sync_market_historical.py` reads MARKET-STATS, resamples daily to monthly, and writes _frozen_historical for Stock Market, FX Rate, 10Y Bond Yield, Yield Curve. Shell tooltip range buttons updated from 1Y/2Y/5Y/10Y to 1Y/2Y/5Y/All (All default, data-r="999"). sync_monthly_historical.py --apply completed. sync_market_historical.py blocked pending Bond_Yield_3M fix (see next item).

1. ~~**Replace Bond_Yield_2Y with Bond_Yield_3M in MARKET-STATS pipeline.**~~ Done March 14, 2026 (Session 6). All four scripts updated. Re-backfill ran clean: 6835 rows per tab, Yield Curve live for 8 countries (USA/CAN/GBR/JPN/DEU/FRA/ITA/ZAF), CHN/IND/BRA/RUS remain gaps. FX Rate historical also filled (was 0 points before this run). sync_market_historical.py --apply completed, build successful, committed and pushed.

1. **Fix JPN inflation gap (Session 7).** `CPALTT01JPM657N` stops June 2021. Replace with `JPNCPIALLMINMEI` (OECD index level, not pre-computed YoY) in `populate_monthly_actuals.py` and `update_monthly_actuals.py`. Add `.pct_change(12) * 100` transform before writing. Re-run JPN inflation backfill only. Upload LIVING_BRIEF.md + both monthly actuals scripts.

1. ~~**Remove Corp Spread and Sov CDS from the dashboard.**~~ Done March 14, 2026. Removed from `data.json` (48 deletions across all 12 countries), `macrosnaps-shell.html` (2 full glossary entries + 2 metricSources lines, 17,066 chars), `fetch_market_data.py` (CORP_SPREAD_SERIES dict, SOV_CDS constants, both fetch functions, pre-fetch block, call site), `update_stories.py` (dead DATA_VOID_METRICS constant), and `build.py` (MARKET_METRICS_BASE trimmed from 6 to 4). Build confirmed clean. Market metrics now 4: Stock Market YTD, 10Y Bond Yield, Yield Curve, FX pair.

1. ~~**Build Google Sheet for daily market data (4 series, 2020 onwards).**~~ Done March 14, 2026. MARKET-STATS sheet built with daily data from 2000-01-01 for all 12 countries. Three scripts built and verified: `populate_market_sheet.py` (one-time backfill), `update_market_sheet.py` (daily appender), `sync_market_sheet.py` (reads sheet, writes to data.json). Stock Market YTD computed at read time from index levels. 2Y yields blank for all non-US countries (no reliable FRED source). RUS equity truncates cleanly at June 2024 with no forward-fill. `fetch_market_data.py` retired. 32 market values updated, stories rewritten, build successful. Two secrets (market-stats-key.json, .env.save) scrubbed from git history and keys regenerated. **Pending:** delete `fetch_market_data.py` once new pipeline has a few more successful runs.

1. ~~**Build Google Sheet for monthly macro actuals (3 series, 2020 onwards).**~~ Done March 14, 2026. Separate sheet MACRO-MONTHLY (ID: 1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI) with 3 tabs: Inflation, Unemployment, Policy_Rate. 315 rows from Jan 2000. Three scripts built: `populate_monthly_actuals.py` (one-time backfill, run and verified), `update_monthly_actuals.py` (daily appender), `sync_monthly_actuals.py` (reads last 6 non-null months per country per series, writes `monthly_actuals` field into data.json). Auth via same market-stats-key.json service account as MARKET-STATS. MACRO_MONTHLY_SHEET_ID added to .env. Re-backfilled March 14, 2026 (Session 4) after fixing stale FRED series: BIS WS_CBPOL for 7 policy rate countries, JPN CPI pre-computed YoY series, BRA unemployment blanked. monthly_actuals written into all 12 countries. update_stories.py and update_headlines.py updated to pass monthly actuals as story context.

1. ~~**Remove Equity Vol and FX Vol from `data.json`.**~~ Done March 13, 2026. Removed `"Equity Vol"` and `"FX Vol"` from `metrics.market` and `_frozen_historical` for all 12 countries (48 deletions total). No blanked stubs remain.

1. ~~**Remove Equity Vol and FX Vol from `macrosnaps-shell.html`.**~~ Done March 13, 2026. Removed both full glossary entries (beginner/moderate/expert bluf + full content, aliases, relatedTerms, metricLinks) and both `metricSources` lines. `metricDisplayLabels` had no entries for either metric. No hardcoded metric counts found. 17,016 characters removed.

1. ~~**Automate monthlyLabels generation in the shell.**~~ Done March 13, 2026. Static `monthlyLabels` array removed from `_frozen.chartConfig`. `histMonthlyLabels` is now a `let` variable populated at runtime by a small IIFE inside the `data.json` fetch `.then()` block, anchored to `data._meta.generated` and counting back 240 months (20 years). No manual shell edit needed when `refetch_historical.py` advances the data window.

1. ~~**Fix chart tooltip title bugs.**~~ Done March 13, 2026. Two bugs in `renderMTT()`: (1) `histEntry.indexLabel` (a boolean) was being used as the chart title via `||`, rendering as "True" on stock market charts. Removed from title expression. (2) Fallback label was "5-Year History" despite data now spanning 10 years. Updated to "10-Year History".

1. ~~**Automate country card weather icon from GDP Growth.**~~ Done March 13, 2026. Country card weather icon is now computed live at load time from each country's GDP Growth value, using the same thresholds as the GDP Weather Map (>=3% sunny, 0-3% cloudy, <0% stormy). The `weather` field in `data.json` is now a fallback only and does not need to be maintained. Implemented as an inline IIFE in the `countries` map (line 5496 of shell).

1. ~~**Restyle welcome banner.**~~ Done March 13, 2026. "Find out what MacroSnaps is and how it works" link converted to a solid cyan pill button with dark text and a glow effect. Banner background strengthened with cyan tint and top/bottom border lines. Font bumped from 12px to 14px with taller padding.

1. ~~**Commodity story rewrite session.**~~ Done March 12, 2026. `update_commodity_stories.py` built and added to daily ritual. Bootstrapped all 9 stories on first run. Prices have moved significantly since March 10 (Gold +74% YoY, Silver +157% YoY, WTI at $93.61, Natural Gas down 22% YoY) - all now rewritten automatically.

2. **Apply USA sheet changes.** `sync_sheet.py` preview on March 11 showed USA CPI 3.1% -> 2.3% and Unemployment 4.4% -> 4.2%. These were never applied. Run: `python3 sync_sheet.py --apply && python3 update_stories.py && python3 build.py`

2. **Manual stories session.** Use the Stories Session Prompt in Part 1B to rewrite all stale metric stories listed in "Known value/story drift" above. This is a content session - upload `LIVING_BRIEF.md` + `data.json`. Do this before building `update_stories.py` so there is a clean baseline.

2. ~~**Grey out 4 data-void metrics in the UI.**~~ Resolved March 12, 2026. On inspection, `fetch_market_data.py` is supplying real values for these metrics for most countries. No greying-out needed. The brief note was stale.

2. ~~**Build Google Sheet country data tables (all 12 countries).**~~ Done March 13, 2026 as a separate exercise. Tab-separated tables covering GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account, Policy Rate from 2000-2026F. All sourced from IMF WEO + central bank policy rates. Full methodology notes and data quality flags documented per country. See "Google Sheet country data build" section above.

2. ~~**Paste country tables into Google Sheet and integrate Macro-stats as data source.**~~ Done March 13, 2026. All 12 country tabs populated in Macro-stats sheet. `sync_sheet.py` fully rewritten to read from Macro-stats, writing 27-point annual historical arrays (2000-2026F) and per-country 2026F card values. Old `MacroSnaps_Forecasts_2026` sheet retired. `MACRO_STATS_SHEET_ID` added to `.env`.

2. **GDP Growth stories audit.** CAN, FRA, ITA, BRA confirmed mismatches between story text and current values. Run a targeted stories session for these four countries (upload LIVING_BRIEF.md + data.json, use Part 1B prompt).

3. ~~**Build `update_stories.py`.**~~ Done March 11, 2026. Script diffs data.json against last git commit, applies per-metric thresholds, calls Claude API (claude-sonnet-4-20250514), and writes all three story levels back into data.json. Also rewrites stories for data-void metrics if their values are ever populated.

4. ~~**Update `refetch_historical.py` to output Current Account as % of GDP natively.**~~ Done March 12, 2026. Uses World Bank nominal GDP series via FRED. No manual re-conversion needed after any future refetch run.

5. ~~**Extend historical data to 10 years.**~~ Done March 12, 2026. All monthly series now return 120 points, annual series return 10 years. Commodity `_frozen_historical` added for all 9 commodities (114 points each via Yahoo Finance continuous futures). BRA 10Y/Yield Curve now resolved. Updated March 13, 2026: USA USD/DXY now fetched (DTWEXBGS). All Equity Vol, Corp Spread, Sov CDS, FX Vol data blanked or removed. RUS Yield Curve explicitly blanked (42-point artefact caused misleading date-shift by view length). Corp Spread and Sov CDS subsequently removed from the product entirely on March 14, 2026.

5. ~~**Investigate IND and ZAF GDP Growth historical anomalies.**~~ Resolved March 13, 2026. IND and ZAF GDP Growth arrays now sourced from Macro-stats (IMF WEO real % growth), replacing the anomalous FRED nominal USD series. Clean data confirmed in preview output.

6. **Build `print_snapshot.py`.** Uses Playwright to open the built HTML file, loops through each country, expands it, and captures a full-height PDF. Output is a dated file in `snapshots/` (e.g. `macrosnaps-2026-03-09.pdf`). Audience level hardcoded to expert. For personal use only, not a public feature. Requires `pip3 install playwright` and `playwright install chromium`.

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

Implication for tooling: implemented March 12, 2026. See `update_headlines.py` architecture: Sonnet+search harvest call feeds recent data into Haiku writing batches as lead context.

---

7. ~~**Add country-level and global stories to the daily bash ritual.**~~ Done and verified March 11, 2026. `update_headlines.py` calls the Claude API, drafts 12 country story blocks (3 bullets x 3 levels) in 3 batches of 4 via Haiku (8000 tokens each) and global stories (3 items x 3 levels) via Sonnet with web search (5000 tokens). Saves to `stories_draft_YYYY-MM-DD.json`. `headline_review.html` is a browser-based review tool: tabs show Bullet 1/2/3, each tab shows all three levels stacked for easy comparison. Export `stories_approved_YYYY-MM-DD.json`, apply with `python3 update_headlines.py --apply`. First live run completed 13/13 March 11, 2026.

8. ~~**Enable web search for country stories in `update_headlines.py`.**~~ Done March 12, 2026. Two-phase architecture: a single Sonnet+search harvest call pulls recent data for all 12 countries (capped at 2 search turns, 1500 max_tokens), then 3 Haiku batches write stories with recent data leading and forecast values passed as background context only. Global runs first to avoid Sonnet rate limit exhaustion from the harvest call. Haiku prompt strengthened with explicit bullet count enforcement and one automatic retry per batch.

9. **Post-launch:** revisit architecture if a second person joins to update data daily.

10. **Post-launch:** replace fake contact form in "Ping Me" footer with a real form service (Formspree or similar). Currently the form shows a success message without sending anything.

11. **Post-launch:** consider user alert emails (daily or weekly digest for chosen countries/metrics/commodities). Requires server-side infrastructure. A simple early version could use Buttondown or Mailchimp for a subscriber list before building anything custom.
