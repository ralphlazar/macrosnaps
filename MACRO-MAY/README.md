# MACRO-MAY

MacroSnaps v2 — prototype build. Lives as a subfolder inside the main `macrosnaps` repo so it can read `../data.json` directly.

Light mode, orange palette, coral-numbered bullets, modular boxes, multi-page architecture (homepage + 12 country pages). Reuses the chart code from the existing site, adapted for the light theme.

## Layout

```
macrosnaps/
├── data.json                  # main repo's canonical data (read by MACRO-MAY/build.py)
├── ... existing site files ...
└── MACRO-MAY/
    ├── build.py               # generates dist/ from ../data.json + styles + charts
    ├── styles.css             # shared CSS
    ├── charts.js              # Chart.js render logic (ported from existing site)
    ├── serve.sh               # local server on port 8765
    ├── README.md
    └── dist/                  # generated output (gitignored if desired)
        ├── index.html
        ├── usa.html ... rus.html
```

## Build and run

```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps/MACRO-MAY
python3 build.py        # generates dist/ (reads ../data.json)
bash serve.sh           # serves dist/ on http://localhost:8765/
```

`serve.sh` runs `build.py` first if `dist/` doesn't exist, then starts the server on **port 8765** (deliberately offset from the 8080 the headline review uses).

## Data sync

`build.py` reads `../data.json` (the main repo's file) by default. No duplication. Run the build any time after the daily ritual updates `data.json`.

## What's in v1

- Homepage: brand header, today's 3 headlines, 12-country snapshot table, 12 country cards (text-only, 3 bullets each, click-through), commodities panel
- Country pages: header with back link, today's 3 country-level stories, 10 metric boxes (GDP, CPI, Unemployment, Budget Deficit, Current Account, Policy Rate, Stock Market YTD, 10Y Bond Yield, Yield Curve, FX), each with value + 3 stories + chart panel + glossary
- Charts: Chart.js, line for time-series with 1Y/2Y/5Y/All toggles, bar for annual structural metrics, ported from the existing renderMetricChart

## What's stubbed

- FX YTD column in the snapshot table is blank (`—`). Existing `data.json` carries FX as a level, not a YTD change. Needs a derived field or a different snapshot column in v2.
- FX regime explanation block per country page is not yet wired (data isn't currently in `data.json`).
- Mod/Expert tiers are intentionally dropped from the rendering (per the spec). They remain in `data.json` for backwards compatibility but are not surfaced.
- No favicon / OG meta / analytics yet.
