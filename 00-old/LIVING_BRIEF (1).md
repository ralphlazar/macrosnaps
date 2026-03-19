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

I want to add metric stories to canada

### ...to here

---

## PART 2 - PROJECT REFERENCE

---

### What the project is

MacroSnaps is a daily global macro and markets dashboard. It shows key economic metrics, market data, stories, and historical charts for 12 countries and 9 commodities. It is designed for three audience levels: beginner, moderate, and expert. The user toggles between levels and everything in the UI adapts - stories, terminology, glossary definitions.

The product is pre-launch. The architecture is intentionally simple. The goal right now is to get the product right before making it scalable.

---

### The 4 files

| File | What it is | Touch it when |
|---|---|---|
| `data.json` | All content and data | Updating metrics, writing stories, changing values |
| `macrosnaps-shell.html` | The entire app shell (no data) | Changing UI, layout, CSS, JS logic |
| `build.py` | The assembly line script | Changing build logic or validation rules |
| `macrosnaps-globe.html` | The built output | Never - this is generated, not edited |

**To build:** run `python build.py` then copy output: `cp macrosnaps-globe.html /mnt/user-data/outputs/macrosnaps-globe.html`

**To validate only (no files written):** run `python build.py --validate-only`. Use this before editing `data.json`.

**After every build:** run the `git commit` command the script prints at the end.

**Never modify** `_frozen_historical` or `_frozen_weatherGrid` inside any country in `data.json`. These are locked historical arrays.

---

### Current content state (March 8, 2026)

**Per-metric stories (beginner / moderate / expert)**
- USA: 14/14 complete
- CAN: 0/14 - not started
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

---

### The 14 metrics per country

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate.

**Market (8):** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, [FX pair - varies by country], FX Vol.

---

### How metric stories work

Stories live in `data.json` inside each metric entry as a `story` object with `beginner`, `moderate`, and `expert` keys.

At load time the shell reads these into the `metricStories` object (line 5605 of shell).

When a user clicks a metric, `renderMTT()` (line 6542) builds the tooltip. The story appears inline between the value and the chart, with no title label. CSS class is `tt-metric-story` (line 165 of shell).

The tooltip order is: metric name, country + value, story, chart, explanation/bluf, FX regime (if applicable), compare button.

---

### Architecture decisions and why

**No Google Sheets.** Claude writes all stories, so a human-friendly editing interface adds no value. The data structure is deeply nested and does not map cleanly to a flat sheet. `data.json` is the single source of truth. Revisit post-launch if a second person joins to update data.

**No CMS.** Pre-launch solo workflow. JSON plus build script is faster to iterate with than any external system.

**Git for version history.** Git is initialized. Commit after every feature or meaningful change using the command the build script prints at the end of each successful build.

---

### Vulnerabilities and mitigations

| Vulnerability | Status | Mitigation |
|---|---|---|
| No version history | Fixed (March 9) | Git initialized. Build script prints a ready-to-run commit command after every successful build. |
| JSON corruption from manual edits | Fixed (March 9) | Run `python build.py --validate-only` before editing. Build script also validates on every run. |
| Forgetting to rebuild | Habit-dependent | Never call a task done until build has run and output copied. |
| No preview step | Fixed (March 9) | Build script now confirms the data payload is present in the output HTML after every build. |
| Spurious git diffs from build timestamps | Fixed (March 9) | Build script stamps `_meta` in memory only. `data.json` on disk is never written by the build. |
| Daily backup only | Covered | Git provides full history. Build script saves daily backup to `backups/` and prunes after 30 days. |

---

### Key shell locations

| Thing | Location |
|---|---|
| `.tt-metric-story` CSS | Line 165 |
| `metricStories` object declaration | Line 5605 |
| `metricStories` populated from data | Line 5637 |
| `renderMTT()` function | Line 6542 |
| Metric story HTML built | Line 6581-6583 |
| Full tooltip render string | Line 6590 |

---

### Pending work (priority order)

1. Add per-metric stories (beginner, moderate, expert) to all 11 remaining countries. 11 countries x 14 metrics x 3 levels = 462 story fields. Biggest content task. Do one country per session.
2. Get the app hosted on GitHub Pages so sharing is a URL rather than a file download.
3. Post-launch: revisit architecture if a second person joins to update data daily.
