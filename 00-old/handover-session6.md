# MacroSnaps Handover Brief - Session 6
**Date:** 9 Feb 2026
**Resume from:** Glossary backend architecture + Claude Code setup

---

## WHAT EXISTS NOW

### HTML file: macrosnaps-globe.html
- Interactive macro dashboard with globe, country panels, metric popovers
- 170 glossary entries in `<script id="glossary-data">` (thin entries for design, 15 enriched for metric popovers)
- All entries recategorised: 0 "general" remaining
- 4 duplicates consolidated (ZLB->zero lower bound, sovereign CDS->Sov CDS, yield curve->Yield Curve, unemployment rate->Unemployment)
- Self-glossary suppression fix (exact match via Set, not substring)
- FX regime improvements (country names in labels, beginner explanations rewritten for all 9 countries)
- Expertise levels: beginner/moderate/expert with level switcher

### JSON files: glossary/ (6 category files)
These are the PRODUCTION backend files. Same 170 entries, but enriched entries use **structured format** (no HTML):

```json
{
  "GDP Growth": {
    "complexity": 1,
    "category": "macro",
    "levels": {
      "beginner": {
        "bluf": "Summary text here",
        "sections": [
          {"head": "Why it matters", "body": "Paragraph text"},
          {"head": "What to watch", "body": [
            "**Bold label:** bullet point text",
            "**Another:** more text"
          ]}
        ],
        "formal": "Technical definition."
      },
      "moderate": { ... },
      "expert": { ... }
    },
    "aliases": ["GDP growth rate"],
    "relatedTerms": ["real GDP", "recession"],
    "metricLinks": ["GDP Growth"]
  }
}
```

**Body** = string (paragraph) or array (bullet list). **Bold** = `**markdown**`. **No HTML anywhere.**

### Category file status:

| File | Total | Enriched | Thin |
|---|---|---|---|
| macro.json | 64 | 18 | 46 |
| credit.json | 28 | 2 | 26 |
| equity.json | 25 | 2 | 23 |
| fx.json | 26 | 2 | 24 |
| trade.json | 8 | 1 | 7 |
| institutions.json | 19 | 0 | 19 |
| **Total** | **170** | **25** | **145** |

### Enriched entries (25):
**Metrics (14):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate, Stock Market YTD, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, Equity Vol, FX Vol, Exchange Rate
**General (1):** inflation
**Macro batch 1 (10):** interest rate, property crisis, real GDP, recession, automatic stabilisers, breakeven inflation, deflation, deposit rate, disinflation, dovish

---

## WHAT TO DO NEXT (in priority order)

### 1. Set up GitHub repo + Claude Code (NEW - start here)
- Create GitHub repo with the 6 glossary JSON files
- Install Claude Code on user's machine (Node.js + `npm install -g @anthropic-ai/claude-code`)
- Connect to GitHub (personal access token)
- Test: "add carry trade to glossary" -> Claude Code writes entry, commits to repo
- Once working, all future glossary work goes through Claude Code

### 2. Continue enriching 145 thin entries
Do in batches of ~10, category by category:
- **Macro:** 46 remaining (next batch: financial conditions, forward guidance, inflation targeting, interbank rate, labour force participation, monetary easing, monetary tightening, output gap, PCE, PMI)
- **Credit:** 26 remaining
- **FX:** 24 remaining
- **Equity:** 23 remaining
- **Institutions:** 19 remaining
- **Trade:** 7 remaining

### 3. Production app rendering
The structured JSON needs a renderer that converts sections/body/formal back to HTML at runtime. This replaces the inline `ge-section` divs. Simple function:
- `body` is string -> render as `<p>`
- `body` is array -> render as `<ul><li>` with `**bold**` -> `<strong>`
- `formal` -> render as `<div class="ge-formal">`

### 4. App architecture (future)
- `data/glossary/macro.json` etc. fetched at runtime
- `data/countries/USA.json` etc. (one per country)
- `data/app-config.json` (stories, sources, chartConfig)
- `index.html` (shell + CSS + renderer)
- Lazy load glossary detail on click

---

## ARCHITECTURE DECISIONS MADE

1. **Single source of truth:** Glossary JSON files (not HTML). HTML keeps thin entries for design only.
2. **Structured data, not markup:** Sections/body/formal pattern. No HTML in JSON.
3. **6 categories:** macro, credit, equity, fx, trade, institutions. No "general".
4. **3 expertise levels:** beginner (explainer podcast), moderate (research email), expert (CIO note)
5. **BLUF + deep dive:** Every entry has bluf (always shown) + sections (shown on expand)
6. **GitHub as persistence:** Repo is the canonical store. Claude Code reads/writes directly.
7. **metricExpl deleted:** All metric explanations merged into glossary. assembleMTTData reads from glossary.

---

## FILES TO UPLOAD NEXT SESSION
1. `macrosnaps-globe.html` (the HTML file)
2. `glossary/macro.json`
3. `glossary/credit.json`
4. `glossary/equity.json`
5. `glossary/fx.json`
6. `glossary/trade.json`
7. `glossary/institutions.json`
8. This handover brief

---

## VOICE/STYLE RULES (for glossary writing)
- Beginner: explainer podcast tone, no jargon without definition, concrete examples
- Moderate: research email to informed non-specialist, can use technical terms
- Expert: hedge fund CIO note, assumes full fluency, frameworks and models by name
- No em dashes (--) or en dashes (-), use hyphens (-) only
- British spelling (organisation, labour, favour)
- Bold in markdown: `**term:**` for bullet list labels
