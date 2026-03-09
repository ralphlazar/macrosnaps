# MacroSnaps - Living Brief
Last updated: March 8, 2026 (end of session)

---

## What the project is

MacroSnaps is a daily global macro and markets dashboard. It shows key economic metrics, market data, stories, and historical charts for 12 countries and 9 commodities. It is designed for three audience levels: beginner, moderate, and expert. The user toggles between levels and everything in the UI adapts - stories, terminology, glossary definitions.

The product is pre-launch. The architecture is intentionally simple. The goal right now is to get the product right before making it scalable.

---

## The 4 files

| File | What it is | Touch it when |
|---|---|---|
| `data.json` | All content and data | Updating metrics, writing stories, changing values |
| `macrosnaps-shell.html` | The entire app shell (no data) | Changing UI, layout, CSS, JS logic |
| `build.py` | The assembly line script | Changing build logic or validation rules |
| `macrosnaps-globe.html` | The built output | Never - this is generated, not edited |

**To build:** run `python build.py` then copy output to outputs folder.

**Never modify** `_frozen_historical` or `_frozen_weatherGrid` inside any country in `data.json`. These are locked historical arrays.

---

## Current content state (March 8, 2026)

### Per-metric stories (beginner / moderate / expert)
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

### Other content (all 12 countries)
- Country-level stories (3 bullets per level): complete for all 12
- metricBriefs (short summaries per metric): complete for all 12
- fxRegime descriptions (3 levels): complete for all 12

---

## The 14 metrics per country

**Macro (6):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate.

**Market (8):** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, [FX pair - varies by country], FX Vol.

---

## How metric stories work

Stories live in `data.json` inside each metric entry as a `story` object with `beginner`, `moderate`, and `expert` keys.

At load time the shell reads these into the `metricStories` object (line 5605 of shell).

When a user clicks a metric, `renderMTT()` (line 6542) builds the tooltip. The story appears inline between the value and the chart, with no title label. CSS class is `tt-metric-story` (line 165 of shell).

The tooltip order is: metric name, country + value, story, chart, explanation/bluf, FX regime (if applicable), compare button.

---

## Architecture decisions made and why

**No Google Sheets.** The data structure is deeply nested (not flat/tabular). Sheets would require a sync script, adds two sources of truth, and adds failure points. Revisit post-launch if a second person needs to update data.

**No CMS.** Pre-launch solo workflow. JSON plus build script is faster to iterate with than any external system.

**JSON as single source of truth.** One file, one place. Simple and appropriate for this stage.

**Git for version history.** Run `git init` if not already done. Commit after every feature or meaningful change. This is the most important stability improvement.

---

## Vulnerabilities and mitigations in place

| Vulnerability | Mitigation |
|---|---|
| No version history | Use Git. Commit after every chunk of work. |
| JSON corruption from manual edits | Validate before editing: `python -c "import json; json.load(open('data.json')); print('valid')"` |
| Forgetting to rebuild | Never call a task done until build has run and output copied |
| No preview step | After build, grep the output to confirm the change landed correctly |
| Daily backup only | Git provides full history. Build script saves daily backup to `backups/` folder. |

---

## Key shell locations

| Thing | Location |
|---|---|
| `.tt-metric-story` CSS | Line 165 |
| `metricStories` object declaration | Line 5605 |
| `metricStories` populated from data | Line 5637 |
| `renderMTT()` function | Line 6542 |
| Metric story HTML built | Line 6581-6583 |
| Full tooltip render string | Line 6590 |

---

## Working preferences

- Think before building. Share approach and flag concerns before writing code. Wait for "go."
- Surgical edits only. Change the minimum needed. Do not rewrite surrounding code.
- Brief explanation after each edit of what changed and why.
- Flag architectural concerns before acting on them.
- Never present a task as done until the build has run successfully.

---

## Writing style rule

No em dashes, no en dashes. Standard hyphen (-) only if a dash is genuinely needed. Prefer commas, periods, or parentheses. Scan every response before outputting. This applies to responses, code comments, and story content written into data.json.

---

## Session rhythm

At the end of each natural unit of work, update this file before starting the next thing. Do not wait until the context window is full. Upload this file at the start of every new session alongside the three source files.

---

## Pending work (priority order)

1. Add per-metric stories (beginner, moderate, expert) to all 11 remaining countries. 11 countries x 14 metrics x 3 levels = 462 story fields. This is the biggest content task.
2. Consider a local story editor (simple HTML form) to make writing stories easier without touching raw JSON.
3. Get the app hosted on GitHub Pages so sharing is a URL rather than a file download.
4. Post-launch: revisit Google Sheets for flat metric data if a second person joins to update numbers daily.

---

## Files to upload at the start of every session

1. `LIVING_BRIEF.md` (this file)
2. `macrosnaps-shell.html`
3. `data.json`
4. `build.py`
