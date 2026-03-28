# MacroSnaps - Living Brief
Last updated: March 28, 2026 (Session 59: metric story pipeline fixed and parallelised; JSON file renames; review UI fixes.)

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

(2) **macedu GitHub repo created.** `https://github.com/ralphlazar/macedu` -- separate from macrosnaps. All six chart components now read from `edu-data.json` (not hardcoded). Design pass complete (fonts, colours, section compartmentalisation). Deployment to Cloudflare Pages is the next step.

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

### Local preview rule
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
python3 sync_edu.py
cd /Users/lisaswerling/RALPH/AI/macedu && git add -A && git commit -m "Daily data sync YYYY-MM-DD" && git push origin main
cd /Users/lisaswerling/RALPH/AI/macrosnaps
python3 audit_ritual.py
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

---

## Full session history

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
