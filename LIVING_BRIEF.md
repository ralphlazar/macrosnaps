# MacroSnaps - Living Brief
Last updated: March 23, 2026 (Session 46: Twitter/OG meta tags added; educators.html created; Subscribe free + Educators buttons moved into fixed footer; #ping hash handler added.)

Session 46 changes in detail:

(1) **Twitter/OG meta tags added to `macrosnaps-shell.html`.** Full set of tags added to `<head>`: `twitter:card`, `twitter:site` (@macrosnapsapp), `twitter:title`, `twitter:description`, `twitter:image`, `twitter:image:alt`, plus `og:image`, `og:title`, `og:description`. Image URL points to `https://raw.githubusercontent.com/ralphlazar/macrosnaps/master/macrosnaps-logo.png` (raw GitHub URL used because the custom domain was returning 400 on the direct path). Logo file (`macrosnaps-logo.png`) uploaded to the root of the GitHub repo. Validated via cards-dev.twitter.com/validator.

(2) **`educators.html` created.** Standalone page at `macrosnaps.app/educators.html`. Matches site design (Space Mono + DM Sans, dark navy, cyan accents). Sections: title block with three weather icons (☀️ ☁️ ⛈️) in a row at 52px using the same CSS filters as the weather grid; intro paragraph; three level cards (Beginner/Moderate/Expert) colour-coded green/gold/cyan; four teaching ideas using weather icons as idea bullets; Share with your department section with Copy link, Share by email, and Suggest a feature buttons. "Suggest a feature" links to `macrosnaps.app/#ping` (not a mailto) to avoid email harvesting. Footer reads: `macrosnaps.app · Macro · Markets · World`. Key terms bold cyan: "three levels", "country card", "weather icons", "story bullets". No em dashes throughout. Human-written tone per style guide.

(3) **Subscribe free + Educators buttons moved into fixed footer.** Standalone subscribe box between weather table and footer removed. Footer is now two rows: row 1 = Subscribe free + Educators buttons; row 2 = Commodities | What? | How? | Who? | Icons? | Legalese | Ping Me | X icon. Footer changed from `display:flex` (single row) to `flex-direction:column`. `footer-comm-row` and `footer-main-row` changed from `display:contents` to `display:flex` with `justify-content:center`. New `.footer-btn-row` class added. `#rankings-view` bottom padding bumped from 80px to 110px to account for taller footer.

(4) **`#ping` hash handler added to `macrosnaps-shell.html`.** A JS snippet at the end of the main script block checks `window.location.hash` on load. If the hash matches a key in `footerContent` (e.g. `#ping`, `#what`), it opens that tooltip automatically. This allows `macrosnaps.app/#ping` to be linked from external pages (e.g. educators.html) and open the Ping Me form directly.

(5) **Educator outreach strategy added to brief.** Target audience: university macroeconomics lecturers globally. Rationale: the three expertise levels map naturally to intro/intermediate/advanced students. Outreach channels: cold email to economics departments, X engagement on #econtwitter, educators page as landing destination. Cold email template drafted: short, collaborative tone, soft-launch framing, invites feedback.

---



Session 45 changes in detail:

(1) **`build.py`: structural date fix.** Root cause of site showing yesterday's date three days running: build.py was injecting data into `window.__MACROSNAPS_DATA__` while the site JS reads from `window.__MACRO_DATA__` — two different variable names, so injected data was never used. Fix: build.py now uses a regex to directly replace the `window.__MACRO_DATA__ = {...};` block in the shell with today's fresh data on every build. The old fetch-block replacement logic and misnamed variable injection have been removed. Additionally, the date stamp is now applied to `data` before serialisation, so both `index.html` and `data.json` always carry the same date.

(2) **`macrosnaps-shell.html`: US→Commodities tooltip nav flash fixed.** The previous session's nav fix (skip animation on country→country navigation) was applied to `showCard` only. `showCommoditiesCard` still used a create-new/remove-old cycle, causing a blank flash specifically on the US→Commodities transition (US is the last country before Commodities in nav order). Fix: `showCommoditiesCard` now uses the same update-in-place strategy as `showCard` — if a `.card-overlay` already exists, it reuses it and swaps innerHTML rather than creating a new overlay. No flash on any nav transition.

(3) **Ping Me form wired to Formspree.** The fake contact form (which just swapped in a success message on submit without sending anything) has been replaced with a real Formspree POST. Endpoint: `https://formspree.io/f/xqeyvnov`. Fields: `name`, `email`, `message`. Button shows "Sending…" during request, success message on delivery, "Error — try again" on failure. Submissions arrive at `lastlemon@gmail.com` with subject line "MacroSnaps" (set in Formspree dashboard under Settings → Email Notifications).

(4) **`forecast_cms.html`: explainer banner added.** A slim dark banner sits between the header and the grid with four labelled items: what the CMS is, how to run it (start `forecast_server.py`, open in browser), what the context column shows, and the save feedback colour codes (gold/green/red).

---

Session 44 changes in detail:

(1) **`macrosnaps-shell.html`: X/Twitter icon added to footer.** Small inline SVG X logo added after `| Ping Me |` in the footer link bar. Links to `https://x.com/macrosnapsapp` in a new tab. Uses `aria-label="MacroSnaps on X"`. New CSS class `.footer-x-link`: colour `#555`, hover-to-`var(--cyan)` matching all other footer links, `display:inline-flex;align-items:center`. No external dependencies -- inline SVG only.

(2) **`update_stories.py`: prompt tightened to reduce stale, forecast-anchored stories.** Three new rules added to `STYLE_GUIDE`:
- "Lead with the most recent data point or trend. Do not open with the annual forecast value."
- "The annual forecast is background context only. Mention it solely if there is a meaningful gap between recent data and the year-end target."
- "Convey direction. Is this metric rising, falling, or holding? A story with no directional signal is a dead story."

`monthly_context` instruction hardened from "Lead with the most recent print where relevant" to "The most recent monthly print is your anchor. Open with it. The annual value is the year-end forecast -- treat it as background, not the lead."

Metric prompt anchor changed from "Write three story variants for this metric at the value shown above" to "Write three story variants for this metric. Anchor each story in the most recent data and direction of travel, not the annual forecast."

Commodity prompt updated to "Lead with the price level and its direction -- is it rising, falling, or range-bound? Give the reader a sense of momentum, not just a number."

`--force-all` run completed: 140/141 OK. ITA/Current Account failed on first run (JSON truncation mid-response). Re-ran with new `--country`/`--metric` flags; second attempt succeeded.

(3) **`update_stories.py`: `--country` and `--metric` filter flags added.** Two new optional arguments:
- `--country CODE` -- filters queue to a single country code (e.g. `--country ITA`). Case-insensitive.
- `--metric NAME` -- filters queue to a single metric name (e.g. `--metric "Current Account"`). Case-insensitive.

Both flags apply as a post-queue filter -- they work with any mode (`--force-all`, `--stale-only`, default diff). Usage for single-metric retry:
```bash
python3 update_stories.py --force-all --country ITA --metric "Current Account"
```

---


Session 43 changes in detail:

(1) **`build.py`: `data["_meta"]["generated"] = TODAY` assignment was missing.** The `ok()` log line claimed the stamp had been written, but there was no actual assignment before the `json.dump()` call. Result: `data.json` always retained yesterday's date, and `audit_ritual.py` Check 1 always failed. Fixed by inserting `data["_meta"]["generated"] = TODAY` immediately before the `json.dump()` call. Note: Session 41 fixed the same bug for the `index.html` inlining path (`json.dumps()`), but the separate `json.dump()` write to `data.json` at the end of the build was never patched. Both paths are now correct.

(2) **`digest_server.py`: invalid model string fixed; tweet and LinkedIn prompts tightened.**
- Model string `claude-opus-4-5` changed to `claude-haiku-4-5-20251001` in both `generate_tweets()` and `generate_linkedin()`. The invalid string was causing the API call to fail silently, returning an empty list, and the UI was falling back to rendering the raw digest markdown as the tweet.
- Tweet prompt: character budget clarified as 256 chars of text + 1 space + bare URL (Twitter wraps all URLs to 23 chars, so total = 280). Explicit rule added: no markdown links, no [text](url) formatting, bare URL only. CTA URL included in the output format spec.
- LinkedIn prompt: added explicit rule "No markdown links. LinkedIn does not render them. Bare URLs only."

(3) **`generate_digest.py`: first-occurrence jargon hyperlinks enabled for Substack; model string fixed.**
- Model string `claude-opus-4-5` changed to `claude-haiku-4-5-20251001`.
- Added rule to STRICT WRITING RULES: "Hyperlink the first occurrence of jargon terms (e.g. stagflation, yield curve, CPI) using markdown links to macrosnaps.app -- first occurrence only, not every instance." Markdown links are correct for Substack (renders them as hyperlinks) and for the digest server's HTML preview. They must not appear in tweet or LinkedIn output -- those are handled by separate rules in `digest_server.py`.

---


Session 42 changes in detail:

(1) **Digest pipeline built.** Two new scripts added to the macrosnaps folder:
- `generate_digest.py` -- reads `data.json`, diffs against a saved snapshot to detect changes, builds an analytical brief, calls Claude API, writes output to `digests/YYYY-MM-DD-[mode].md`. Supports `--mode daily|weekly|notes`. Run at end of daily ritual.
- `digest_server.py` + `digest_ui.html` -- local web server on `http://localhost:8080`. Run `python3 digest_server.py` once per session. Browser UI with Daily Post, Weekly Digest, and Substack Notes buttons. Generates digest, tweets, and (on weekly) LinkedIn post in one click. Each section has its own Copy button.

(2) **Digest format.** Ultra-short bullet format. Daily: 4 bullets max, under 80 words. Weekly: "What moved" + "What to watch" sections, under 150 words. Notes: 3 standalone one-sentence takes. Voice: moderate expertise level, assumes basic financial literacy, no jargon wall. First-occurrence jargon hyperlinked to macrosnaps.app.

(3) **Digest writing rules (enforced in prompt).** Em-dashes banned entirely. No filler words (notably, importantly, it is worth noting, interestingly). No hedging. Specific numbers over vague descriptions. Every word earns its place. Sound human, not AI-generated.

(4) **Snapshot delta system.** `generate_digest.py` saves a lean snapshot of all metric values to `digests/snapshots/YYYY-MM-DD.json` after each run. Next run diffs against previous snapshot, surfaces changed metrics, stormy flags, and commodity moves >= 1.5% to Claude as structured input.

(5) **Subscribe box added to `macrosnaps-shell.html`.** Sits between the GDP rankings table and the footer. Centred, dark navy with cyan border glow, matching site aesthetic. Links to `macrosnaps.substack.com` in a new tab. Text: "MacroSnaps Newsletter / Daily and weekly macro mini-briefings, straight to your inbox." Button: "Subscribe free".

(6) **Substack account set up.** URL: `macrosnaps.substack.com`. Description: "Daily macro briefings across 12 economies, at the depth you choose." Cadence: daily posts weekdays only, weekly digest every Thursday. Expertise level: moderate throughout.

(7) **Twitter/X account set up.** Professional account, Financial services category. Profile photo: `macrosnaps-logo.png` (512x512). Banner: `macrosnaps-banner.png` (1500x500). Handle: `@macrosnapsapp`. URL: `https://x.com/macrosnapsapp`. Posting cadence: daily including weekends. Content: one tweet per day from Notes output or a single data observation.

(8) **LinkedIn.** Posting cadence: once per week, Thursdays, condensed version of weekly digest. LinkedIn post generated automatically by `digest_server.py` when weekly mode is run.

(9) **Posting cadence summary.**
- Substack daily post: weekdays only (Mon-Wed, Fri). Generated via digest server, daily mode.
- Substack weekly digest: Thursdays. Generated via digest server, weekly mode.
- Twitter/X: daily including weekends.
- LinkedIn: Thursdays only, from weekly digest run.

(10) **Build rule.** Always ask before building, coding, or creating any files. No exceptions.

---

Session 41 changes in detail:

(1) **Three.js removed from `macrosnaps-shell.html`.** The Three.js script (`cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`) was loading on every page load despite the globe no longer being part of the site. This was crashing Chrome 146 on macOS instantly, both regular and incognito mode. Safari and mobile were unaffected. Confirmed by disabling GPU in Chrome (`--disable-gpu` flag), which prevented the crash, isolating it to Chrome's GPU process. Removed by deleting the `<script>` tag from `macrosnaps-shell.html`. Globe feature is gone, Three.js is dead code and must not be re-added.

(2) **Cloudflare Web Analytics beacon removed from `macrosnaps-shell.html`.** The beacon script (`static.cloudflareinsights.com/beacon.min.js`) was also contributing to Chrome crashes. Removed by deleting the line from `macrosnaps-shell.html`. Google Analytics to be added as a replacement at a later date. To add GA4: insert snippet just before `</body>` in `macrosnaps-shell.html` and run `build.py --apply`.

(3) **`build.py`: date stamp order fixed.** `data["_meta"]["generated"]` and `data["_meta"]["built_at"]` were being stamped after `json.dumps(data)` was called to inline into `index.html`, meaning the published site always showed yesterday's date under the logo. Fixed by moving both assignments to immediately before the `json.dumps()` call. The `json.dump()` write to `data.json` at the end of the build is unchanged.

(4) **Google service account key regenerated.** `market-stats-key.json` had an invalid JWT signature, causing all gspread calls to fail (`invalid_grant: Invalid JWT Signature`). This affected both the sheet append in `fetch_market_data.py` and all of `sync_market_historical.py`. Regenerated via Google Cloud Console (project: `macrosnaps`, service account: `macrosnaps-sheets@macrosnaps.iam.gserviceaccount.com`) under IAM & Admin, Service Accounts, Keys, Add Key, Create new key, JSON. Downloaded and replaced `~/Downloads/macrosnaps/market-stats-key.json`. If this recurs, regenerate the key via the same path.

(5) **Anthropic API key updated in `.env`.** `update_headlines.py` was failing with `401 invalid x-api-key`. Fixed by updating `ANTHROPIC_API_KEY` in `~/Downloads/macrosnaps/.env` with the correct key.

---

Session 40 changes in detail:

(1) **`update_headlines.py`: harvest `max_tokens` raised from 2000 to 4000 (line 284).** The Anthropic API now returns web search results as `server_tool_use` + `web_search_tool_result` blocks in the same turn as the final text response, consuming tokens from the same `max_tokens` budget. This left insufficient room for the 12-country JSON output, causing truncation mid-object and a consistent `No JSON object found in response` parse failure. Bumping to 4000 resolved it cleanly. Root cause confirmed by inspecting raw block types: previously the search results were lighter or handled differently; now they count against the output budget.

---

Session 39 changes in detail:

(1) **`sync_commodity_data.py`: `SPARK_MONTHS` cap removed.** `SPARK_MONTHS = 120` changed to `SPARK_MONTHS = None` (unused). `derive_spark()` previously returned `last_closes[-SPARK_MONTHS:]`, hard-truncating to 10 years. Now returns `last_closes` in full. All 9 commodities now write ~307-309 monthly points to `data.json` (Brent Crude 225 pts due to shorter sheet history). Root cause of charts starting at Oct 2016 rather than Jan 2000.

(2) **`audit_ritual.py`: `EXPECTED_SPARK_PTS` made dynamic.** Was hardcoded to `120`. Now computed at runtime via `_months_since_jan_2000()` which returns `(year - 2000) * 12 + month` (currently 314). Check 4 allows 3 months of lag tolerance (`len(spark) < EXPECTED_SPARK_PTS - 3`) to handle commodities with slightly shorter sheet history.

---

Session 38 changes in detail:

(1) **Commodity story malformed structure fixed in `data.json`.** Five commodities (Natural Gas, Gold, Copper, Wheat, Corn) had story tiers stored as `{"text": "..."}` objects instead of plain strings. This caused tooltips to render blank for those commodities. Fixed by flattening all 15 affected tiers (5 commodities x 3 levels) to plain strings. WTI Crude, Brent, Silver, and Soybeans were unaffected.

(2) **`write_commodity_story()` fixed in `update_stories.py`.** Root cause of (1): the function was wrapping each tier in `{"text": "..."}` instead of writing a plain string. The docstring even stated "Commodity stories use `{text: ...}` dicts per level" -- that was wrong. Fixed to write plain strings identical to `write_metric_story()`. Also added `storyWrittenAtPrice` and `storyUpdatedDate` writes to the commodity path, which were previously missing (those fields existed on WTI from manual edits but were never being written by the pipeline for any commodity).

(3) **Icons/values toggle added to weather matrix in `macrosnaps-shell.html`.** A toggle button appears in the matrix title bar next to the metric picker. Clicking it switches all matrix cells between weather icons and the underlying forecast numbers. Numbers are coloured by weather class (sunny=cyan, cloudy=grey, stormy=hot). State persists via `localStorage` key `whNumericMode`. Toggle only applies to grid metrics (`hasGrid:true`): GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account. For non-grid metrics (Policy Rate, Stock Market YTD, 10Y Bond Yield, Yield Curve) the toggle button is always rendered but `visibility:hidden` to prevent layout shift when switching metrics. New CSS classes: `.wh-num-val` (number display), `.wh-num-toggle` (button), `.wh-num-toggle-hidden` (invisible placeholder).

(4) **Password changed** from `Crocodile` to `croc` in `macrosnaps-shell.html`.

---

Session 37 changes in detail:

(1) **Site launched at macrosnaps.app.** Domain registered on Cloudflare. DNS configured with four A records (185.199.108-111.153) and a CNAME (www -> ralphlazar.github.io), all grey cloud (DNS only, not proxied). Custom domain set in GitHub Pages settings. HTTPS enforced via Let's Encrypt (auto-provisioned by GitHub).

(2) **`build.py` OUTPUT_FILE changed from `macrosnaps-globe.html` to `index.html`.** Single-line change on line 27. Required because GitHub Pages serves `index.html` at the root. `macrosnaps-shell.html` remains the source template (input). `macrosnaps-globe.html` deleted from repo -- still recoverable from git history if ever needed.

(3) **git pull strategy set to merge.** `git config --global pull.rebase false` run on the machine to prevent the divergent-branches prompt on future pulls. The initial push conflict was caused by GitHub auto-creating a `CNAME` file when the custom domain was set.

(4) **Password gate added to `macrosnaps-shell.html`.** Temporary, for soft-launch period. An IIFE immediately after `<body>` prompts for password. Currently set to `croc` (changed from `Crocodile` in Session 38). Wrong password blanks the page and redirects to `about:blank`. To remove at public launch: delete the 9-line `<script>` block after `<body>` and run `build.py`.

(5) **Cloudflare Web Analytics added.** RUM enabled with JS snippet installation (auto-inject not available since DNS is grey cloud). Snippet added just before `</body>` in `macrosnaps-shell.html`:
```html
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "30ef321a2bad44e5aa9b4ddcf4f6ac65"}'></script><!-- End Cloudflare Web Analytics -->
```

(6) **Welcome modal redesigned in `macrosnaps-shell.html`.** Replaced the thin top-of-page banner strip with a full-screen overlay modal. Features: blurred dark backdrop, centred dark navy card with cyan glow border, three weather icons (☀️ ☁️ ⛈️) using the canonical `.wh-icon` filter pattern, bold headline, short description, cyan gradient CTA button ("Show me how it works" -- opens the What tooltip as before), "I'll explore on my own" dismiss link, x close button, and click-outside-to-dismiss. Slides up on entry. Shown once per browser via `localStorage` key `ms_welcomed`. To re-trigger for testing: delete `ms_welcomed` from DevTools -> Application -> Local Storage.

---

Session 36 changes in detail:

(1) **Pre-launch checklist closed.** All blocking items resolved:
- `clean_cite_tags()` regex (`r'</?cite[^>]*>'`) confirmed fixed prior to this session.
- `audit_macro_monthly.py` marked redundant -- superseded by `audit_sheets.py` (Session 28), which covers the same gap audit. Never needs to be run.
- Corp Spread and Sov CDS confirmed removed from `data.json`.
- `audit_ritual.py` corrected and verified with a clean green run (see below).

(2) **`audit_ritual.py` corrected (three fixes).** The script was written against a stale assumption of the data.json schema and had three bugs:

- **Check 3 (spark arrays): wrong skip set.** `check_spark_arrays()` was using `KNOWN_BLANK_MARKET` to skip permanent gaps in `_frozen_historical`, but that dict only covers market metric display values. Added a dedicated `KNOWN_BLANK_HISTORICAL` dict:
```python
KNOWN_BLANK_HISTORICAL = {
    "CHN": {"Policy Rate", "Unemployment", "10Y Bond Yield", "Yield Curve"},
    "IND": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "BRA": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "RUS": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "ZAF": {"Unemployment"},
}
```
These match the confirmed permanent data gaps in the known gaps table.

- **Check 6 (story freshness): wrong field path.** `country.last_updated` does not exist in data.json. The `last_updated` field lives on individual metrics (`metrics.macro[x].last_updated`, `metrics.market[x].last_updated`). Rewritten to use `metrics.market['Stock Market YTD'].last_updated` as the daily-updated proxy, with fallback to any market metric that has the field.

- **Check 8 (global stories): wrong key and wrong structure.** Script used `data.get("global_stories", [])` but the actual key is `globalStories` and it is a dict keyed by tier (`beginner`, `moderate`, `expert`), each containing a list of 3 cards. Rewritten accordingly.

- **`KNOWN_BLANK_MARKET` for RUS also corrected.** `"Stock Market YTD"` was in the skip list for RUS, leftover from before Session 33 fixed the MOEX fetch. Removed -- RUS Stock Market YTD is now live data and should be audited.

(3) **`audit_ritual.py` verified clean.** All 8 checks passed against today's `data.json` (2026-03-17 build).

---

Session 35 changes in detail:

(1) **Metric dropdown flash-to-top-left fixed in `macrosnaps-shell.html`.** The `.wh-metric-dropdown` was using the shared `ttIn` keyframe animation, which applies `transform: translate(-50%, -50%)`. This is correct for centred tooltips but wrong for the dropdown, which uses fixed `left`/`top` positioning, causing a one-frame jump to the wrong position on every open. Fixed by replacing `animation: ttIn .15s ease-out` with a dedicated `dropIn` keyframe (`@keyframes dropIn{from{opacity:0}to{opacity:1}}`), a simple fade with no transform. Fix applies on both desktop and mobile.

---

Session 34 changes in detail:

(1) **`print_snapshot.py` built.** Standalone script generating a dated, print-friendly PDF snapshot of the full MacroSnaps dashboard. Reads `data.json` directly; does not open the live site. Output: `00-snapshots/macrosnaps-YYYY-MM-DD.pdf` (directory created automatically).

PDF structure: one page per country in GDP_NOMINAL_ORDER, each with a metrics table (6 macro + visible market metrics) and one Chart.js chart per metric with historical data. Charts annotate the last non-null data point with a filled circle and a label (e.g. "Mar 2026: 2.4%") - the key pipeline audit feature. Monthly actuals insets (3 most recent rows) appear below the Inflation, Unemployment, and Policy Rate charts. A commodities section follows all 12 countries with a 120-pt sparkline per commodity.

Chart.js 4.4.1 and chartjs-plugin-datalabels 2.2.0 are fetched from cdnjs at runtime and inlined into the HTML (not loaded via `<script src>` - headless Chromium cannot fetch external scripts when the page has no origin). Playwright uses `wait_for_function("window.allChartsRendered === true")` before exporting.

Usage:
```bash
python3 print_snapshot.py
python3 print_snapshot.py --date 2026-03-15   # override date label only
```

One-time setup (already done on this machine):
```bash
pip3 install playwright --break-system-packages
python3 -m playwright install chromium
```

---

Session 33 changes in detail:

(1) **RUS Stock Market YTD fixed in `fetch_market_data.py`.** `fetch_moex_index()` function added. Uses the public MOEX ISS REST API (`iss.moex.com/iss/history/engines/stock/markets/index/boards/SNDX/securities/IMOEX.json`) to fetch all IMOEX daily closes from Jan 1 to today and compute YTD %. `fetch_stock_ytd()` now returns early for RUS via `if code == "RUS": return fetch_moex_index()`, bypassing yfinance entirely.

(2) **USA Stock Market YTD NaN fixed in `fetch_market_data.py`.** `yf_ytd_return()` now calls `.dropna()` on the Close series before slicing with `iloc[0]` / `iloc[-1]`, preventing NaN rows from producing `nan%`.

(3) **USD/DXY FX fetch fixed in `fetch_market_data.py`.** `yf_latest_close()` rewritten to use `yf.download()` with `progress=False, auto_adjust=True` and `.squeeze().dropna()` to handle MultiIndex columns in newer yfinance. Falls back to `Ticker.fast_info["lastPrice"]` for tickers that fail `yf.download()` (e.g. DX-Y.NYB).

(4) **Rolling spark update removed from `fetch_market_data.py`.** Lines that did `spark = spark[1:] + [round(current, 2)]` on commodity items were deleted. Superseded by `sync_commodity_data.py` which rebuilds sparks from the sheet.

(5) **JPN headlines skip fixed in `update_headlines.py`.** `draft_countries_batch()` validation now checks for countries missing entirely from the parsed batch response (not just short bullet counts). A missing country triggers a retry with message `(missing: JPN, retrying...)`. `apply_draft()` now prints `[WARN] JPN not in approved file` at apply time if any country is absent from the approved JSON.

(6) **gspread deprecation warning fixed in `populate_monthly_actuals.py`.** `ws.update('A1', values)` changed to `ws.update(values, 'A1')` in `write_tab()`.

(7) **Redundant scripts deleted.** Removed from repo: `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`. (`headline_review.html` retained.)

---

Session 32 changes in detail:

(1) **Mobile header second separator dot added.** On mobile, the header collapses to one line. A dot already existed between "Macro & Market Snapshots" and the date. A matching dot was added before "Macro & Market Snapshots" so the line reads: `MACROSNAPS · MACRO & MARKET SNAPSHOTS · UPDATED 17 MAR 2026`. Fix: added `.logo .sub1::before{content:' · '}` inside the mobile `@media` block in `macrosnaps-shell.html`, directly above the existing `::after` rule. Desktop layout unaffected.

(2) **`update_stories.py --stale-only` mode added.** New flag scans all macro metrics in `data.json` for entries where `value_at_generation` is present and does not match `value`. Rewrites only those metrics via the Claude API. Scoped to macro only, matching the `build.py` mismatch guard. Exits cleanly with a "nothing to rewrite" message if no mismatches found. Use between `sync_sheet.py --apply` and `build.py` whenever forecasts are updated:
```bash
python3 sync_sheet.py --apply
python3 update_stories.py --stale-only
python3 build.py --apply
```

(3) **GDP Growth stories audit closed as false alarm.** CAN, FRA, ITA, BRA stories were audited against current values. All four stories are consistent with their current values. The earlier suspicion of mismatches was not borne out. All four have `value_at_generation: MISSING` (field predates Session 29) -- this is harmless; `build.py` only blocks when the field is present and mismatches. These will self-heal the next time `update_stories.py` rewrites them.

---

Session 31 changes in detail:

(1) **Daily ritual run successfully.** Build 2026-03-17 committed and pushed to ralphlazar.github.io/macrosnaps. Three known issues surfaced:
- **RUS Stock Market YTD failed** -- `fetch_moex_index()` not being called correctly in `fetch_market_data.py`. yfinance hit instead and returned no data (`$IMOEX.ME possibly delisted`). Russia carried yesterday's value. Fixed in Session 33.
- **JPN missing from `update_headlines.py --apply` output** -- 11/12 countries applied, JPN absent. Japan carried yesterday's stories. Fixed in Session 33.
- **USA/JPN/DEU/FRA/ITA 10Y Bond Yield and Yield Curve failed** -- FRED HTTP 500s, transient outage. Values stale by one day. Self-corrected when FRED recovered.

(2) **`audit_ritual.py` built.** Final step of the daily ritual. Reads `data.json` from the project directory and produces a terminal health report. Eight checks:
- Build date matches today (`_meta.generated`)
- Market values non-blank (skips known permanent gaps per `KNOWN_BLANK_MARKET`)
- Spark arrays non-empty (skips known permanent gaps per `KNOWN_BLANK_HISTORICAL`)
- All 9 commodities have price, change, and sufficient spark pts (dynamic, ~months since Jan 2000)
- All 12 countries have stories at all 3 tiers
- All countries have market data updated today (checks `metrics.market['Stock Market YTD'].last_updated`)
- No `value_at_generation` mismatches on macro metrics
- All 3 global story cards present at all 3 tiers (reads `data.globalStories[tier]` list of 3)

Writes dated plain-text log to `logs/audit_YYYY-MM-DD.txt`. Creates `logs/` directory if needed. Exits with code 1 if any issues found. Run as final step of the daily ritual: `python3 audit_ritual.py`.

(3) **Daily ritual expanded to 9 steps.** See updated Daily ritual section below.

---

Session 30 changes in detail:

(1) **Header "Updated Daily" replaced with dynamic date.** `<span class="sub2" id="headerUpdated">` now reads `_meta.generated` on data load and renders as "Updated 17 Mar 2026". Falls back to "Updated Daily" if data not yet loaded. Colour changed from `#aaa` to `#4db8cc` (muted cyan) to signal freshness.

(2) **Global stories news icon fading removed.** `setActiveNewsIcon()` and `clearActiveNewsIcon()` are now empty stubs. Icons sit fully static at all times. Inconsistent dimming behaviour was the root cause.

(3) **"Updated" date below rankings and commodity tables removed.** `asofHTML` variable and its two injection points deleted from `renderGridTable()` and `renderRankedTable()`. Date is in the header; no need to repeat it.

(4) **"Icons?" footer tooltip added.** New entry in the footer links bar and footer data object. Covers all three icon contexts: country headline icon, metric weather strip, and commodity card icon. All three icons rendered with `.wh-icon` filter spans. Short hyphens throughout (no em-dashes).

(5) **Weather strip added to macro metric tooltips.** When a macro metric tooltip opens, the 7-icon weather strip from the card now appears to the right of the country name and value. Strip is injected via `insertAdjacentHTML` after `applyGlossary` runs (to avoid attribute mangling). Market metric tooltips unaffected. Strip size matches card (18px). Rollover tip for all icons anchored above icon 4 (the middle) using nth-child CSS offsets to prevent clipping.

(6) **2dp formatting in ranked tables.** `fmtNum()` helper added -- pads values with fewer than 2 decimal places to exactly 2dp (e.g. 6% -> 6.00%, 2.5% -> 2.50%). Applies to all ranked and grid table values via `fmtPct()` and the `disp` line. Exception: Yield Curve (unit ` bps`) bypasses `fmtNum` and renders as plain integers.

(7) **Canonical weather icon set locked (style guide).** ☀️ ☁️ ⛈️ are the only permitted weather icons anywhere in the product. All other variants (⛅ 🌩 🌧 🌤 etc.) are banned. Every icon must use a `.wh-icon sunny/cloudy/stormy` span for CSS filter rendering. Raw emoji forbidden.

(8) **Em-dash ban hardened (style guide).** Rule extended from story text and copy to everywhere without exception: code, comments, prompts, tooltips, the living brief itself. No edge cases.

(9) **`update_headlines.py` word count ceilings added.** Global story body caps: beginner 55 words, moderate 80 words, expert 110 words. Added directly to the JSON format spec in `build_global_system()`.

---

Session 29 changes in detail:

(1) **`hasChartData(metricName, countryCode)` helper added to `macrosnaps-shell.html`.** When a metric has no historical data at all (missing `_frozen_historical`, empty `v` array, or all-null values after padding), the entire chart section is now hidden from the tooltip -- including the title, range buttons, and canvas. Previously a "No historical data" placeholder rendered, which looked like a broken state. The helper uses the same three-layer guard as `renderMetricChart()` and correctly handles both bar (annual) and line (monthly) chart types by selecting the appropriate label array. Both the `chartHTML` build block and the render block are gated on `d.chart && hasChartData(d.metricName, d.chart.code)`.

(2) **Global stories nav arrows removed from `renderNews()`.** The arrows in the global stories tooltip were redundant -- story icons in the background menu already serve as navigation. Removed: `navHTML` construction, nav btn click listeners, `measureNewsTTHeight()` function, `newsTTHeight` module-level variable, and `newsTTHeight = null` from `clearActiveNewsIcon()`. Kept: `activeNewsIdx`, `setActiveNewsIcon()`, `clearActiveNewsIcon()`, and all icon opacity fade behaviour. The `.tt-nav` / `.tt-nav-btn` CSS is retained -- still used by metric and commodity tooltips.

(3) **Commodity chart x-axis fixed to Jan 2000 -> current month.** `renderCommodityMonthlyChart()` previously used a broken slice pattern: on "All" view it took the first 120 labels from `histMonthlyLabels`, mapping commodity data to Jan 2000-Dec 2009 regardless of actual dates. Fixed by replacing with the same right-align + null-pad pattern used in `renderMetricChart()`: the spark array is right-aligned into the full `histMonthlyLabels` window (~303 months), left-padded with nulls. The render function was correct after this fix; Session 39 fixed the separate issue of the wrong data source being read.

(4) **`value_at_generation` field added to `update_stories.py`.** `write_metric_story()` now saves `entry["value_at_generation"] = item["new_value"]` alongside `last_updated` every time a metric story is written. This records the value the story was written for.

(5) **Story mismatch guard added to `build.py`.** In the macro metrics validation loop (Section 2), after the existing tier/value checks, `build.py` now checks: if `value_at_generation` is present and does not match the current `value`, the build fails with a clear error:
```
x [BRA] macro['GDP Growth'] story mismatch -- written for '2.8%', current value is '2.1%'. Re-run update_stories.py for this metric.
```
Guard scoped to macro metrics only (forecast values drift; market values update in the same daily ritual). The guard only fires when `value_at_generation` is present -- existing metrics without the field pass silently. The field populates organically as stories are regenerated.

---

Session 28 changes in detail:

(1) **`audit_sheets.py` built.** Read-only diagnostic script that connects to both MARKET-STATS and MACRO-MONTHLY and prints a gap report. For each MARKET-STATS country tab, reports last populated date per column (`Stock_Market_Index`, `FX_Rate`, `Bond_Yield_10Y`, `Yield_Curve`, `Stock_Market_YTD_USD`) and flags anything >90 days stale or blank. For each MACRO-MONTHLY tab, reports last non-null date per country column. Known permanent gaps are labelled rather than flagged. Auth via `market-stats-key.json`. Run:
```bash
MACRO_MONTHLY_SHEET_ID=<id> python3 audit_sheets.py
```
MACRO-MONTHLY sheet ID: `1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI`

(2) **Root cause of USA unemployment gap identified and fixed.** `update_monthly_actuals.py` checked only the last *row date* in the Date column (which ran to 2026-03-01) and concluded "nothing to do" -- it never checked whether individual country cells within those rows were blank. USA unemployment had been blank since Jan 2025 (15 months). Fixed by switching USA from IMF LS (which genuinely stopped publishing USA data after Feb 2012) to FRED `UNRATE`. 13 cells backfilled (Jan 2025 -> Feb 2026).

(3) **`--backfill` mode added to `update_monthly_actuals.py`.** Scans all three tabs for blank cells in existing rows, fetches data for the date range of those gaps, and writes values back using targeted `ws.batch_update()` calls. Dry run by default; `--apply` to write.
```bash
MACRO_MONTHLY_SHEET_ID=<id> python3 update_monthly_actuals.py --backfill          # preview
MACRO_MONTHLY_SHEET_ID=<id> python3 update_monthly_actuals.py --backfill --apply  # write
```

(4) **`update_monthly_actuals.py` source changes (v4).** Unemployment and Policy Rate sources updated:
- **USA unemployment**: switched from IMF LS (stops 2012 for USA) -> FRED `UNRATE`
- **GBR unemployment**: FRED `LRHUTTTTGBM156S` (unchanged)
- **BRA unemployment**: removed `BRAURAGSAM157S` (bad series ID); BRA added to `UNEMP_BLANK` -- no viable monthly source exists (see permanent gaps below)
- **IND policy rate**: removed from `BIS_RATE_COUNTRIES` and `RATE_SERIES_FRED`; BIS stops Aug 2016, FRED `INTDSRINM193N` also stops 2016 -- no current source (see permanent gaps below)

(5) **Two new permanent data gaps confirmed and documented** (see Known permanent data gaps table).

(6) **Session 28 audit results summary:**
- MARKET-STATS: all 12 country tabs current to 2026-03-15. CHN/IND/BRA/RUS Bond Yield and Yield Curve blank -- known permanent gaps.
- Commodities tab: all 9 commodities current to 2026-03-16.
- MACRO-MONTHLY Inflation: 11/12 countries current to Jan 2026. IND last=Dec 2025 (IMF lag -- expected).
- MACRO-MONTHLY Policy Rate: all countries current to Jan/Feb 2026.
- MACRO-MONTHLY Unemployment: USA now current to Feb 2026. GBR last=Nov 2025 (ONS lag). Others at expected IMF/BIS lag.

---

Session 27 changes in detail:

(1) **Global stories carousel navigation added then partially removed.** Session 27 added nav arrows to the global stories tooltip. Session 29 removed them as redundant (story icons in the background menu already serve as navigation). What remains from Session 27: `setActiveNewsIcon(idx)` / `clearActiveNewsIcon()` icon opacity fade behaviour, `activeNewsIdx` tracker. What was removed in Session 29: `navHTML`, nav btn listeners, `measureNewsTTHeight()`, `newsTTHeight`.

(2) **`Updated` date label made more visible.** `.wh-asof` CSS: `color:#333 -> #777`, `font-size:7px -> 9px`.

(3) **Copy tweaks in WHAT? footer.** "seasoned professionals" -> "finance professionals". "AI-generated story bullets" -> "story bullets".

---

Session 26 changes in detail:

(1) **Glossary extended with four new entries:** G7, BRICS, Goldman Sachs, CSFB. All three levels written for each. Footer tooltips (WHAT? and WHO?) now run `applyGlossary()` + `attachGlossary()` so these terms auto-link inside footer panels.

(2) **Floating commodities FAB removed.** `#btnCommFab` (the FAB button, fixed bottom-right) is gone entirely -- CSS block, HTML element, and JS event listener all deleted.

(3) **Commodity inline links added.** `applyCommLinks()` and `attachCommLinks()` added and wired into `applyGlossary()` / `attachGlossary()`. Every call site that already used those functions (global stories, country card bullets, metric tooltips, footer panels) now also gets commodity links automatically -- no new call sites needed.
- Colour: gold `#e8a838` with dotted underline -- visually distinct from glossary blue (`#8ec8f0`)
- Generic terms (oil, crude, commodity, commodities) -> opens full commodities card
- Specific terms (WTI, Brent, natural gas, gold, silver, copper, wheat, corn, soybeans, soybean) -> opens individual commodity tooltip by item name lookup; fallback to full card if name not found
- First occurrence only per term per text block, longest-match first to avoid partial matches
- CSS classes: `.comm-term` (link), hover brightens to `#f5c46a`

(4) **Style guide rule established: no em-dashes anywhere.** Em-dashes are a signal of AI-generated writing and are banned from all story text, glossary definitions, and any other copy in the product. Use commas, colons, parentheses, or restructure the sentence instead.

---

Session 25 changes in detail:

(1) **Pipeline architecture rule established (CRITICAL).** No sync script may contact an external API directly. The pipeline has two strictly separated layers:
- **Fetch layer** (`fetch_market_data.py`, `update_monthly_actuals.py`) -- contacts external APIs, writes to Google Sheets.
- **Sync layer** (`sync_market_historical.py`, `sync_commodity_data.py`, `sync_monthly_actuals.py`) -- reads exclusively from Google Sheets, writes to data.json. Never contacts any external API.
This ensures chart rendering is never broken by a transient external API failure. All three sync scripts confirmed compliant as of this session.

(2) **`sync_market_historical.py` rewritten (v2).** Previous version fetched directly from yfinance and FRED -- architecturally wrong and the root cause of the USA USD/DXY empty tooltip chart (yfinance `DX-Y.NYB` returned no data on March 16). New version reads exclusively from the MARKET-STATS Google Sheet (ID: `1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI`), one tab per country. Sheet columns used: `Stock_Market_Index`, `FX_Rate`, `Bond_Yield_10Y`, `Yield_Curve`. All four columns resampled to monthly last-close via pandas. No yfinance, no FRED, no requests -- gspread only. Auth via `market-stats-key.json`.

(3) **FX inversion removed from `sync_market_historical.py`.** FX values in MARKET-STATS are already stored in display format. No inversion logic needed. `FX_INVERT` dict removed entirely.

(4) **Yield Curve derivation removed from `sync_market_historical.py`.** `Yield_Curve` column is pre-computed in bps in the sheet. `SHORT_RATE_SERIES` dict and derivation logic removed entirely.

(5) **Staleness check fixed in `sync_market_historical.py`.** Previous check compared total array length against expected months-since-2000 -- produced false positives for series with shorter history (e.g. EUR/USD starts 2004, ZAF stocks start 2012). New check uses actual last data point date from the DataFrame vs today, flagging only if last point is more than `STALE_MONTHS` (3) months old.

(6) **`sync_monthly_actuals.py` confirmed already compliant.** Reads exclusively from MACRO-MONTHLY via Google Sheets API (`googleapiclient`). No external API calls. No changes needed.

(7) **MARKET-STATS sheet column reference** (confirmed this session):
`Date | Stock_Market_Index | FX_Rate | Bond_Yield_10Y | Bond_Yield_3M | Yield_Curve | Stock_Market_YTD_USD`

(8) **Preview and apply run clean.** 48 spark arrays written across 12 countries, all current to 2026-03. Build successful, committed, pushed.

---

Session 24 changes in detail:

(1) **Tooltip navigation arrows now respect `CARD_MARKET_EXCLUDE`.** `CARD_MARKET_EXCLUDE` was lifted from inside `assembleCardData()` to module scope. `getMetricList()` now applies the same filter, so the up/down arrows in a metric tooltip can only navigate to the same 10 metrics visible on the card. Navigable sequence: GDP Growth -> Inflation (CPI) -> Unemployment -> Budget Deficit -> Current Account -> Policy Rate -> Stock Market YTD -> 10Y Bond Yield -> Yield Curve -> FX cross.

(2) **Fixed-window chart rendering in `renderMetricChart()`.** All tooltip charts -- annual bar, monthly line, market line -- now always span **Jan 2000 (left) -> current month (right)**. The x-axis window is fixed; it never auto-fits to the extent of available data. Data is right-aligned into the full label array and left-padded with nulls where coverage is shorter than Jan 2000. Gaps are visible as blank regions rather than hidden by axis shrinkage.

(3) **Three-layer "no chart" guard in `renderMetricChart()`.** Guards fire in sequence: (a) `!d` -- no `_frozen_historical` object; (b) `!cfg || !cfg.v || !cfg.v.length` -- metric key missing or `v` array empty; (c) `!validVals.length` -- all values null after padding. Session 29 extended this concept with `hasChartData()` to hide the entire chart section rather than show a placeholder message.

---

Session 23 changes in detail:

(1) **Old IMF API permanently shut down.** `dataservices.imf.org` is not a temporary outage -- the IMF decommissioned this endpoint in 2025 and replaced it with a new SDMX API accessible via the `sdmx1` Python library (`sdmx.Client('IMF_DATA')`). All scripts that used the old endpoint now use the new one. `sdmx1` is now a required dependency (`pip3 install sdmx1 --break-system-packages`).

(2) **`populate_monthly_actuals.py` rewritten (v3).** New data sources:
- **Inflation**: IMF `CPI` dataset, key `COUNTRY.CPI._T.IX.M`. Single call covers all 12 countries. YoY % computed from monthly index levels (fetched from Jan 1999 for overlap). All 12 countries current to Jan 2026, IND to Dec 2025.
- **Unemployment**: IMF `LS` dataset, key `COUNTRY.U.PT.M`. Covers CAN/JPN/DEU/FRA/ITA/RUS. USA: FRED `UNRATE`. GBR: FRED `LRHUTTTTGBM156S`. CHN/IND/ZAF/BRA: permanent blanks (no monthly source).
- **Policy Rate**: BIS `WS_CBPOL` API for CAN/GBR/JPN/ZAF/BRA/RUS. FRED `FEDFUNDS` for USA. FRED `ECBMRRFR` for DEU/FRA/ITA. CHN/IND: permanent blanks (no current monthly source).

(3) **`update_monthly_actuals.py` rewritten (v3->v4).** Same source changes as populate. Incremental append logic unchanged. `--backfill` mode added in Session 28.

(4) **MACRO-MONTHLY backfill completed successfully.** `populate_monthly_actuals.py --apply` wrote 315 rows to all three tabs (Inflation, Unemployment, Policy_Rate). All 12 countries now have current monthly actuals in tooltip charts.

(6) **New IMF API country/dataset reference:**
- CPI: `sdmx.Client('IMF_DATA').data('CPI', key='COUNTRY.CPI._T.IX.M', params={'startPeriod': 'YYYY-MM'})`
- Unemployment: `sdmx.Client('IMF_DATA').data('LS', key='COUNTRY.U.PT.M', params={'startPeriod': 'YYYY-MM'})`
- Country codes: ISO3 (USA, GBR, DEU, JPN, FRA, ITA, CAN, CHN, IND, ZAF, BRA, RUS)

---

Session 22 changes in detail:

(1) **`forecast_cms.html` built.** Standalone browser-based CMS for editing 2026 annual forecast values (Column AB) across all 12 country tabs in the Macro-stats Google Sheet. Shows a 12-country grid, 6 metrics each. Inputs save on blur with flash feedback (gold = saving, green = saved, red = error). Context column shows latest external consensus value, source, date, and revision badge where available. Server connection status shown in header with auto-detect.

(2) **`forecast_server.py` built.** Local Flask proxy running on `localhost:5050`. Authenticates via `market-stats-key.json` service account. Endpoints: `GET /forecasts`, `POST /forecast`, `GET /external_forecasts`, `POST /run_fetch` + `GET /fetch_status`. Requires `flask flask-cors`. Service account must have Editor access to Macro-stats sheet.

(3) **`fetch_external_forecasts.py` built.** Haiku 4.5 + web search, one API call per country, fetches latest 2026 forecasts from IMF, OECD, Goldman Sachs, JPMorgan, and other credible institutions published in the last 30 days. Returns structured JSON per metric: value, source, date, prior (if revised), notes. Writes to `external_forecasts.json`. `max_uses: 3` web searches per call. Cost: ~$0.73/run. Recommended cadence: weekly.

(4) **Forecast CMS daily usage.** To use: (a) run `python3 forecast_server.py`; (b) open `forecast_cms.html` in browser; (c) edit any forecast value -- saves on blur; (d) hit Fetch External weekly for fresh context data.

(5) **`METRIC_ROWS` config in `forecast_server.py`.** Row mapping (1-indexed): GDP_Growth=2, Inflation=3, Unemployment=4, Budget_Deficit=5, Current_Account=6, Policy_Rate=7. Verify this matches Macro-stats tab layout if saves land in wrong rows.

---

Session 21 changes in detail:

(1) **Daily ritual completed successfully.**

(2) **Cite tag bug fixed in `update_headlines.py` (two parts).**
- **Prompt-level fix:** Added hard rule to `build_global_system()` prompt: "All story text must be plain prose only. Never include HTML tags, `<cite>` tags, citation markup, markdown, or any other formatting. No angle brackets of any kind in story text."
- **Scrubber fix:** `clean_cite_tags()` regex corrected to `r'</?cite[^>]*>'` (was `r'</?antml:cite[^>]*>'` which did not match actual escaped tags in JSON). Confirmed resolved prior to Session 36.

(3) **`update_headlines.py`: harvest prompt broadened to include geopolitical events.** `max_tokens` 1500 -> 2000, search turns 2 -> 3.

(4) **`headline_review.html`: global detail textarea font fixed.** `font-size: 12px` -> `13px`, `color: var(--text-dim)` -> `var(--text)`.

(5) **Editorial workflow clarified.** When re-editing mid-day: always load `stories_approved_YYYY-MM-DD.json` (not the draft). Re-export overwrites approved file. Re-run steps 3 and 4. Safe to do multiple times per day.

---

Session 20 changes in detail:

(1) **`macrosnaps-shell.html`: icon removed from global story tooltip title.**
(2) **`macrosnaps-shell.html`: "MSc Economics (LSE)," removed from WHO copy.**
(3) **`macrosnaps-shell.html`: HOW copy updated.**
(4) **`audit_market_data.py` written and run successfully.** Results clean.
(5) **`audit_macro_monthly.py` written but never run.** Superseded by `audit_sheets.py` (Session 28). Do not run.

---

Session 19 changes in detail:

(1) **`sync_monthly_actuals.py`: `MONTHS_TO_KEEP = 6` -> `36`.**

---

Session 18 changes in detail:

(1) **`populate_monthly_actuals.py` and `update_monthly_actuals.py` rewritten (v2).** Switched CPI and Unemployment from frozen FRED/OECD series to IMF IFS API.

(2) **`sync_market_historical.py` originally introduced.** Rewritten in Session 25 -- see above.

(3) **Bug fix: spark arrays were writing to wrong location.** Previous script wrote to `metrics.market[label]["spark"]` -- a field the shell never reads. Fixed. Shell reads exclusively from `_frozen_historical[label].v`.

(4) **`_frozen_historical` structure confirmed.** Shell populates `historicalData[code]` from `c._frozen_historical` (line 5595). Format per entry: `{"type": "bar"|"line", "v": [...]}`.

---

Session 17 changes in detail:

(1) **Security -- stale API key file deleted and scrubbed from git history.**
(2) **Sort order fix in macrosnaps-shell.html.** `_whSortCol = -1` on metric dropdown change.
(3) **Redundant files identified** (not yet deleted): `sync_market_sheet.py`, `sync_monthly_historical.py`, `update_market_sheet.py`, `populate_market_sheet.py`, `headline_review.html`.

---

Session 16 changes in detail (all in macrosnaps-shell.html only):
(1) Logo click from Globe view navigates back to homepage correctly.
(2) Nav simplified to logo-only. All button code intact -- do not delete.
(3) Commodities FAB introduced this session. **Removed in Session 26.**
(4) Yield Curve and 10Y Bond Yield rankings render `num + cfg.unit` correctly.
(5) Mobile rankings grid: columns 0-1 hidden at <=768px.
(6) Per-metric weather strip added to country cards (5 macro metrics, 7 icons).
(7) Icon rule (FIXED -- do not change): all weather icons use `.wh-icon` CSS filter pattern.
(8) `CARD_MARKET_EXCLUDE` set: `Stock Market YTD (USD)`, `Stock Market Index`, `FX Rate`.
(9) Navy palette applied everywhere.
(10) Default rankings sort: nominal GDP order via `GDP_NOMINAL_ORDER` constant, `_whSortCol = -1`.
(11) Compare All Countries and Over Time buttons removed from macro metric tooltips.

---

Session 15 changes in detail:
(1) New `Commodities` tab in MARKET-STATS sheet.
(2) `backfill_commodity_data.py` -- one-time only, already run. Do not re-run.
(3) `fetch_market_data.py` now appends today's commodity row to sheet.
(4) `sync_commodity_data.py` reads Commodities tab, derives price/change/spark (full monthly history from Jan 2000).
(5) spark upgraded from 12 -> ~307 points (full history).
(6) change is now day-over-day, not YTD.

Session 14-8: See previous brief versions.

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
- No em-dashes anywhere in story text, glossary definitions, or any other copy. They are a signal of AI-generated writing. Use commas, colons, parentheses, or restructure the sentence instead.
- When in doubt, ask. Do not assume.

### ...to here

---

## PART 2 - PROJECT REFERENCE

### Site

- Live URL: https://macrosnaps.app
- Repo: GitHub Pages, branch `master`, root directory
- Built file: `index.html` (standalone, self-contained, ~1110 KB)

---

### Architecture

Three source files assemble into one output:

| File | Role |
|------|------|
| `data.json` | All content: metrics, stories, commodities, historical arrays |
| `macrosnaps-shell.html` | All UI: HTML, CSS, JS. References `data.json` via a placeholder |
| `build.py` | Assembles output: inlines data.json into shell, validates schema, diffs changes, auto-commits |

`index.html` is build output. Never edit it directly.

---

### Countries

12 countries in this order: USA, CAN, GBR, DEU, FRA, ITA, JPN, CHN, IND, BRA, RUS, ZAF

---

### Metrics

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate

**Market (5):** Stock Market YTD, Stock Market YTD (USD), 10Y Bond Yield, Yield Curve, FX (country-specific key per country)

**Market metrics in data.json** live at `country.metrics.market[display_key]` where display_key is the exact string above (e.g. `"Stock Market YTD (USD)"`). These are written by `sync_sheet.py --market --apply`.

---

### Pipeline architecture rule (CRITICAL)

**No sync script may contact an external API directly.** The pipeline has two strictly separated layers:

| Layer | Scripts | Contacts external APIs? | Reads sheets? | Writes sheets? | Writes data.json? |
|-------|---------|------------------------|---------------|----------------|-------------------|
| Fetch | `fetch_market_data.py`, `update_monthly_actuals.py` | Yes | No | Yes | current values only |
| Sync | `sync_market_historical.py`, `sync_commodity_data.py`, `sync_monthly_actuals.py` | Never | Yes | No | Yes |

This ensures chart rendering is never broken by a transient external API failure.

---

### Data sources

**Annual forecasts (macro card values):**
- Source: Ralph's Google Sheet "Macro-stats" (ID: `1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo`)
- Script: `sync_sheet.py --apply`
- Writes: `metrics.macro[key].value` (2026F card value) and `_frozen_historical[key].v` (annual array, bar chart) for GDP Growth, Budget Deficit, Current Account only

**Daily market data (current values + sheet append):**
- Source: yfinance + FRED + MOEX REST API
- Script: `fetch_market_data.py` -- fetches current values, writes to `metrics.market[label].value`, and appends a daily row to each country tab in MARKET-STATS. Never touches spark arrays in data.json.
- RUS equity: MOEX REST API (not yfinance). `fetch_moex_index()` in `fetch_market_data.py`
- Permanent blanks: CHN/IND/BRA/RUS bond yields -- values hand-maintained in data.json. None-guard prevents overwriting.

**Market metric spark arrays (historical line charts):**
- Script: `sync_market_historical.py --apply`
- **Source: MARKET-STATS sheet only. Never contacts yfinance or FRED.**
- Sheet columns: `Stock_Market_Index`, `FX_Rate`, `Bond_Yield_10Y`, `Yield_Curve`
- FX values stored in display format in sheet -- no inversion needed.
- Yield curve stored in bps in sheet -- no derivation needed.
- Run: daily (after `fetch_market_data.py`)
- Writes: `_frozen_historical[label] = {"type": "line", "v": [...]}`

**Commodity daily prices:**
- Source: MARKET-STATS Google Sheet, `Commodities` tab
- Columns: `Date | WTI Crude | Brent Crude | Natural Gas | Gold | Silver | Copper | Wheat | Corn | Soybeans`
- ~6,400 daily rows covering full history from Jan 2000
- Script: `fetch_market_data.py` appends today's row; `sync_commodity_data.py --apply` reads full tab, derives price/change/spark (~307 monthly pts), writes to `data.json`
- Spark field: `data.commodities.items[n].spark` -- plain array of monthly last-close floats. Read directly by `renderCommodityMonthlyChart()` in the shell. NOT via `_frozen_historical` (that structure is for country macro/market metrics only).
- Backfill script: `backfill_commodity_data.py` -- one-time, already run. Do not re-run.

**Monthly actuals (tooltip line charts -- Inflation, Unemployment, Policy Rate):**
- Source: MACRO-MONTHLY Google Sheet (ID: `1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI`, also set via `MACRO_MONTHLY_SHEET_ID` env var)
- Tabs: `Inflation`, `Unemployment`, `Policy_Rate`
- Columns: `Date | USA | CAN | GBR | JPN | DEU | FRA | ITA | CHN | IND | ZAF | BRA | RUS`
- Backfill script: `populate_monthly_actuals.py` -- run to rewrite full history from Jan 2000.
- Incremental script: `update_monthly_actuals.py` -- appends new months and fills blank cells (`--backfill`). Run monthly.
- Sync script: `sync_monthly_actuals.py --apply` -- reads MACRO-MONTHLY sheet only, writes `monthly_actuals` to data.json. `MONTHS_TO_KEEP = 36`. Never contacts external APIs.
- **IMF SDMX API**: `sdmx.Client('IMF_DATA')` via `sdmx1` library. CPI dataset: `COUNTRY.CPI._T.IX.M`. LS (unemployment) dataset: `COUNTRY.U.PT.M`. Old `dataservices.imf.org` endpoint is permanently dead.
- **Unemployment sources per country**: USA -> FRED `UNRATE`; GBR -> FRED `LRHUTTTTGBM156S`; CAN/JPN/DEU/FRA/ITA/RUS -> IMF LS; CHN/IND/ZAF/BRA -> permanent blanks.
- **Policy Rate sources per country**: USA -> FRED `FEDFUNDS`; DEU/FRA/ITA -> FRED `ECBMRRFR`; CAN/GBR/JPN/ZAF/BRA/RUS -> BIS `WS_CBPOL`; CHN/IND -> permanent blanks.

---

### Spark array architecture rule

**Every spark array must cover Jan 2000 -> last available data point.** "Last available" must be within the last 3 months of today. If a source stops updating, the chart shows a visible trailing gap rather than hiding it. Gaps are diagnostic. Sparks are never rolled forward one point at a time -- they are always rebuilt from source on each run.

---

### Daily ritual

```bash
python3 fetch_market_data.py
python3 sync_market_historical.py --apply
python3 sync_commodity_data.py --apply
python3 update_commodity_stories.py
python3 update_headlines.py
# [manual review gate -- open headline_review.html, load draft, review/edit, export approved file]
python3 update_headlines.py --apply stories_approved_$(date +%Y-%m-%d).json
python3 build.py --apply
python3 audit_ritual.py
python3 digest_server.py
```

`update_headlines.py` has a manual review gate:
1. Run `python3 update_headlines.py` -- produces `stories_draft_YYYY-MM-DD.json`
2. Open `headline_review.html`, load draft, review/edit, export `stories_approved_YYYY-MM-DD.json`
3. Run `python3 update_headlines.py --apply stories_approved_YYYY-MM-DD.json`
4. Run `python3 build.py --apply`
5. Run `python3 audit_ritual.py`
6. Run `python3 digest_server.py` -- opens browser UI at `http://localhost:8080`, generate and post digest

**Mid-day re-edit workflow:** Load `stories_approved_YYYY-MM-DD.json` (not the draft) to preserve previous edits. Re-export overwrites the approved file. Re-run steps 3, 4, and 5. Safe to do multiple times per day.

---

### Key data.json paths

```
data.countries[code].metrics.macro[metric_name].value                <- card display value (string)
data.countries[code].metrics.macro[metric_name].story                <- per-metric story object
data.countries[code].metrics.macro[metric_name].value_at_generation  <- value story was written for
data.countries[code].metrics.macro[metric_name].last_updated         <- date story was written
data.countries[code].metrics.market[metric_name].value               <- current market value (string)
data.countries[code].metrics.market[metric_name].last_updated        <- date market value was fetched
data.countries[code]._frozen_historical[metric_name].type            <- "bar" or "line"
data.countries[code]._frozen_historical[metric_name].v               <- chart data array (macro/market tooltip charts only)
data.countries[code].monthly_actuals                                 <- {inflation, unemployment, policy_rate} arrays
data.commodities.items[n].price                                      <- commodity price
data.commodities.items[n].spark                                      <- commodity monthly chart data (~307 pts) -- NOT _frozen_historical
data._meta.generated                                                 <- build date stamp
data.globalStories[tier]                                             <- list of 3 cards, each {icon, label, body, source}
```

---

### Known permanent data gaps

| Country | Metric | Reason |
|---------|--------|--------|
| CHN, IND, ZAF | Unemployment (MACRO-MONTHLY) | No IMF LUR coverage -- permanent blank |
| BRA | Unemployment (MACRO-MONTHLY) | PNAD Continua is quarterly only -- no freely available monthly series exists. IMF LS stops 2012 for BRA. Permanent blank. |
| CHN, IND, BRA, RUS | 10Y Bond Yield | No source -- sheet column empty; values hand-maintained in data.json |
| CHN, IND, BRA, RUS | Yield Curve | No source -- sheet column empty, always blank in chart |
| CHN | Policy Rate (MACRO-MONTHLY) | No source -- permanent blank |
| IND | Policy Rate (MACRO-MONTHLY) | BIS WS_CBPOL stops Aug 2016; FRED INTDSRINM193N also stops 2016; RBI repo rate not available as a live monthly series. Permanent blank. |
| RUS | Policy Rate (MACRO-MONTHLY) | BIS stopped publishing after Feb 2022 (sanctions) -- blank from Mar 2022 |
| RUS | All equity | MOEX REST API used instead of yfinance |
| CAD/USD, GBP/USD, EUR/USD, USD/INR, USD/ZAR, USD/BRL | FX spark history | Sheet data starts ~2004, not 2000. Data is current, history is shorter. |
| ZAF | Stock Market spark history | Sheet data starts ~2012 |

---

### Scripts summary

| Script | Trigger | What it does |
|--------|---------|--------------|
| `fetch_market_data.py` | Daily | Fetches current equity/FX/yields via yfinance+FRED+MOEX, writes `metrics.market[label].value`; appends daily row to each country tab in MARKET-STATS; appends commodity row to Commodities tab |
| `sync_market_historical.py --apply` | Daily | Reads MARKET-STATS country tabs, resamples to monthly last-close, rebuilds all 4 market spark arrays in `_frozen_historical`. No external API calls. |
| `sync_commodity_data.py --apply` | Daily | Reads full Commodities tab (~6,400 rows), derives price/change/spark (~307 monthly pts), writes to data.json |
| `update_commodity_stories.py` | Daily | Rewrites commodity stories when price moves exceed threshold |
| `update_headlines.py` | Daily | Calls Claude API, writes country and global stories to draft JSON (manual review gate before --apply) |
| `sync_sheet.py --apply` | When forecasts change | Reads Macro-stats sheet, writes macro card values and `_frozen_historical` arrays |
| `populate_monthly_actuals.py` | Once (backfill) | Writes full history Jan 2000 -> present to MACRO-MONTHLY sheet. CPI via IMF SDMX; Unemployment via IMF LS + FRED; Policy Rate via BIS WS_CBPOL + FRED |
| `update_monthly_actuals.py` | Monthly | Appends new months to MACRO-MONTHLY sheet. `--backfill` mode fills blank cells in existing rows. Same sources as populate. |
| `sync_monthly_actuals.py --apply` | After update_monthly_actuals | Reads MACRO-MONTHLY sheet only, writes `monthly_actuals` to data.json (36 most recent non-null per series). No external API calls. |
| `audit_sheets.py` | Ad hoc | Read-only gap audit of MARKET-STATS and MACRO-MONTHLY. Flags stale or blank series. No writes. |
| `update_stories.py` | On metric change / after sync_sheet.py | Diff-driven per-metric story rewrites. `--force-all` rewrites everything. `--stale-only` rewrites macro metrics where `value_at_generation` mismatches `value`. `--country CODE` and `--metric NAME` filter to a single metric for targeted retries. Saves `value_at_generation` alongside each story. |
| `build.py --apply` | Daily | Assembles index.html, validates schema (incl. story mismatch guard), diffs, auto-commits, pushes |
| `audit_ritual.py` | Daily (final step) | Reads data.json, runs 8 health checks, prints terminal report, writes logs/audit_YYYY-MM-DD.txt. Exits 1 if issues found. Commodity spark check uses dynamic expected pts (months since Jan 2000, currently ~314). |

---

### Shell key facts (macrosnaps-shell.html)

- All macro/market tooltip charts read from `_frozen_historical[label].v` via `historicalData[code]` (line 5595: `historicalData[c.code] = c._frozen_historical`)
- **Commodity charts read from `item.spark` directly** -- NOT from `_frozen_historical`. `_frozen_historical` is a country-level structure and is never populated on commodity items.
- Market metric current values read from `co.metrics.market[display_key]` -- exact string match required
- `Stock Market YTD (USD)` read at rankings table only -- excluded from country cards via `CARD_MARKET_EXCLUDE`
- `Stock Market Index` and `FX Rate` also excluded from country cards via `CARD_MARKET_EXCLUDE`
- Local YTD: `co.metrics.market['Stock Market YTD']`
- `_flattenMetrics()` flattens `{value, story}` objects to bare values for the shell
- `DISPLAY_NAMES` map: `'United Kingdom' -> 'UK'`, `'United States' -> 'USA'`
- Weather icon computed live from GDP Growth thresholds: >=3% sunny, >=0% cloudy, <0% stormy
- `metricDisplayLabels`: `'Policy Rate' -> 'Policy Rate (year-end)'`
- Globe is lazy-init (WebGL only on first toggle click). Nav buttons hidden, globe accessible by restoring `.view-toggle{display:flex}` if needed.
- Default sort: `_whSortCol = -1` = nominal GDP order (GDP_NOMINAL_ORDER constant). Logo click resets to this. Metric dropdown change also resets to `-1` (Session 17 fix).
- `_whNumericMode` (bool, localStorage `whNumericMode`): when true, weather matrix cells show forecast numbers instead of icons. Grid metrics only (`hasGrid:true`). Toggle button always rendered for layout stability; `visibility:hidden` on non-grid metrics.
- `CARD_MARKET_EXCLUDE` set: `'Stock Market YTD (USD)'`, `'Stock Market Index'`, `'FX Rate'`
- `monthly_actuals` field is rendered in tooltip line charts for macro metrics -- the script header comment saying "story context only" is wrong.
- **Tooltip chart window rule:** All tooltip charts (annual bar, monthly line, market line, commodity monthly) always span Jan 2000 (left) -> current month (right). The axis is fixed -- never auto-fitted to data extent. Data is right-aligned into the full label array, left-padded with nulls. Missing data shows as visible gaps.
- **hasChartData guard:** `hasChartData(metricName, countryCode)` runs before building chart HTML. If it returns false, the entire `.metric-chart-wrap` section (title, range buttons, canvas) is omitted from the tooltip entirely. No "No historical data" message is shown -- the chart section simply does not exist. Applies to metric tooltips only; commodity charts are separate and use `renderCommodityMonthlyChart()` / `renderCommodityChart()`.
- **Commodity inline links:** `applyCommLinks()` runs at end of every `applyGlossary()` call. `attachCommLinks()` runs at end of every `attachGlossary()` call. Gold colour `#e8a838`, class `.comm-term`. Generic terms (oil, crude, commodity, commodities) -> `showCommoditiesCard()`. Specific terms (WTI, Brent, natural gas, gold, silver, copper, wheat, corn, soybeans) -> `showCommodityMTT(idx)` by name lookup. First occurrence only per term per block. Do not add separate call sites -- the wiring into `applyGlossary`/`attachGlossary` covers all surfaces automatically.
- **No floating commodities FAB.** The `#btnCommFab` button was removed in Session 26. Do not re-add it.
- **Global stories carousel.** `renderNews()` drives the three-story carousel. `activeNewsIdx` tracks current story (0/1/2). `setActiveNewsIcon(idx)` / `clearActiveNewsIcon()` are empty stubs -- icons are fully static. No nav arrows in the global stories tooltip -- story icons in the background menu are the navigation. `measureNewsTTHeight()` and `newsTTHeight` were removed in Session 29.
- **X/Twitter icon in footer.** Small inline SVG X logo sits after `| Ping Me |` in the footer link bar. Links to `https://x.com/macrosnapsapp`. CSS class `.footer-x-link`. Do not change the handle.

### Weather icon rule (FIXED -- do not change)

All weather icons across the entire site must use the `.wh-icon` CSS filter pattern:
- A single emoji wrapped in `<span class="wh-icon sunny/cloudy/stormy">`
- `.sunny`: no filter. `.cloudy`: `brightness(.6) contrast(1.05) saturate(.3)`. `.stormy`: `brightness(.15) contrast(1.2) saturate(0) drop-shadow(...)`
- Exception: per-metric strip uses the correct emoji per state with the same `.wh-icon cls` wrapper -- intentional, filter still applies correctly
- Never use differently-styled icons (raw emoji, SVG, different filter values) anywhere else on the site

**Canonical emoji set (LOCKED -- do not substitute):**
- ☀️ sunny state
- ☁️ cloudy state
- ⛈️ stormy state

These three and only these three may be used anywhere in the product -- in code, copy, tooltips, prompts, or documentation. ⛅, 🌩, 🌧, 🌤 and all other weather variants are banned. This applies to all future UI changes, story writing, and pipeline updates.

**Icon rendering rule (FIXED -- no exceptions):** Every weather icon displayed in the UI must be wrapped in a `.wh-icon sunny/cloudy/stormy` span so the CSS filter is applied. Raw emoji, bare text, or any other rendering method is forbidden. This includes footer tooltips, glossary entries, story text, and any future UI component.

---

### Em-dash rule (FIXED -- no exceptions)

Em-dashes are banned everywhere in the product without exception. This includes story text, glossary definitions, footer copy, UI labels, tooltips, code comments, prompts, and the living brief itself. Use commas, colons, parentheses, or restructure the sentence instead. There are no edge cases where an em-dash is acceptable.

---

### Pending work (priority order)

1. **`update_stories.py` pipeline session (next).** Two improvements agreed but not yet built: (a) monthly actuals as a story rewrite trigger -- rewrite when a new monthly actual lands, not just when the annual forecast changes; (b) time-based stale refresh via `--stale-only` with a 30-day age threshold as a safety net for metrics where monthly actuals rarely change.

1. **Post-launch:** revisit architecture if a second person joins to update data daily.

1. **Post-launch:** replace fake contact form in "Ping Me" footer with a real form service (Formspree or similar).

1. **Post-launch:** Substack chosen as the email/newsletter platform. See Substack strategy section for full plan. Buttondown and Mailchimp no longer under consideration.

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

**Stories** should be written off recent data and trends, not off the forecast values. Monthly CPI prints, quarterly GDP flash estimates, central bank decisions, weekly jobless claims -- this is the live texture that makes stories worth reading. A story that just restates the annual forecast number adds no value.

The correct approach: stories comment on what is actually happening right now. If recent data is tracking ahead of or behind the annual forecast, the story can note that tension briefly. But the forecast is not the anchor of the story -- recent data is.

**Architectural constraint: write path separation.** `sync_sheet.py --apply` writes only annual forecast fields. `sync_monthly_actuals.py` writes only the `monthly_actuals` field. These two scripts must never touch each other's fields. No other script writes to `monthly_actuals`.

**Story mismatch guard.** `update_stories.py` now saves `value_at_generation` alongside every metric story it writes. `build.py` checks this field at build time -- if `value_at_generation` differs from the current `value`, the build fails with a clear error naming the country and metric. This field populates organically as stories are regenerated; existing metrics without the field pass the check silently.

---

---

### Substack strategy

**Goal for first 3 months:** audience building only. No paywall, no monetisation pressure.

**Cadence: daily posts + weekly digest**

Run two things simultaneously, serving different subscriber relationships:

- **Daily post:** short, low-friction, almost verbatim from the pipeline's three-act global story output. Low extra effort. Its jobs are: proving the pipeline is alive and the product is serious (40 posts = credibility), creating a scrollable archive for new subscribers, and feeding Substack's algorithm (which surfaces active publications). Most subscribers will not read every one -- that is fine.
- **Weekly digest:** the actual product most subscribers will open. Longer and more considered: what mattered this week, which countries moved, what surprised, what to watch next week. Different enough from the daily to justify both. Built from material already generated during the week.

Keep daily posts genuinely short. If they are long, readers feel guilty skipping them, unsubscribe rates rise, and the weekly stops feeling like a reward.

**Funnel: glossary links + one CTA per post**

Every glossary term in every post should be hyperlinked to the live glossary on macrosnaps.app. Use the same rule as the site: first occurrence per post only, not every instance. This is a passive conversion path -- readers who click mid-sentence to understand a term land on a live interactive page and become site users.

Supplement with one explicit call to action (CTA) at the end of every post. Something like: "See how this plays out across all 12 countries on the live dashboard." This is active, gives a specific reason to visit, and positions the site as the thing the email cannot replace (interactivity, depth-toggle). Glossary links + one CTA is the right combination for the audience-building phase.

Note on deliverability: emails with many outbound links can score worse on spam filters. The first-occurrence rule keeps this clean.

**Depth levels and future monetisation**

The site's beginner / moderate / expert structure maps naturally to a free/paid Substack split. Suggested path: everything free for 3 months, then introduce paid with beginner free and moderate/expert behind a paywall. The content structure already justifies this -- no extra work required.

**Voice**

Substack readers follow people, not products. The pipeline writes the stories but a 2-3 sentence human intro each day (written by Ralph) is important. Without it the publication reads like a feed, not a newsletter. The most successful macro newsletters (Doomberg, Net Interest, Kyla's Newsletter) have a strong authorial voice.

**The name**

MacroSnaps works for a web app. Consider whether the Substack needs a subtitle or tagline that carries more weight on its own and tells a new reader immediately what they are getting.

**Before launching: have 4-6 posts in the bank.** New subscribers who arrive at a near-empty archive leave immediately.

**Substack Notes**

Substack's short-form feed (similar to Twitter). Macro content performs well there. A chart screenshot or one-line take on a data print is natural material given the daily pipeline. Low effort, decent discovery reach.

**Promotion (first 3 months)**

What actually works at the early stage, in priority order:

1. **Personal outreach first.** The first 50-100 subscribers should come from people already known personally or professionally. Pick 30-40 people in your network who would genuinely find it useful and message them individually. Direct messages convert far better than any public promotion.

2. **LinkedIn.** Macro content performs well there, especially anything with a clear data angle. A weekly post sharing one chart or insight from MacroSnaps, with a link to the Substack, is low effort and reaches a professional audience already predisposed to this content. Consistency matters more than virality.

3. **Cross-recommendations on Substack.** Recommend other macro/finance Substacks genuinely. Some will recommend back. It is a real growth driver on the platform. Do not be transactional about it.

4. **Twitter/X.** Worth maintaining for macro content specifically because that community is active there, but it is a slow burn unless something catches. Do not rely on it.

5. **Ask early subscribers to forward to one person.** Word of mouth from a trusted source converts better than anything you can do yourself. Most people do not think to do it unless asked.

**What not to bother with in the first 3 months:** paid promotion, SEO, press outreach, ProductHunt-style launches. All of that makes sense later. For sub-1000 subscribers it is noise.

---

**Do not position against Bloomberg or data terminals.** The audience is professionals and informed non-professionals who want a daily briefing at the depth they choose, not a research platform. The competition is a good morning read, not a data subscription.
