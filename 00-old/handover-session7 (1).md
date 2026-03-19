# MacroSnaps Handover Brief
## Session 7 - February 10, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard prototype. Single-page HTML app with a 3D globe (Three.js), 9 country cards with macro/market data, 3 expertise levels, inline glossary, historical charts, weather icon system, and comparison views. Built for investor demo and eventual production as a consumer fintech product.

**File:** `macrosnaps-globe.html` (~8,175 lines including pretty-printed JSON data, fully self-contained)

**Creator:** Ralph Lazar - MSc Economics (LSE), ex-Goldman Sachs Global Equity Strategy, ex-CSFB Fixed-Income Prop Trading.

---

## CURRENT FEATURE SET

### Globe & Navigation
- 3D wireframe globe with cyan dots for 9 countries
- Country labels (flag + code) float near dots, clickable via event delegation on container
- Blue dots clickable via raycasting on invisible hit-target spheres
- Drag to rotate, click to open country card
- Labels use `data-code` attribute, delegated click handler (fixes Chrome issue where per-frame recreation killed direct handlers)

### 9 Countries
USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND

### Country Cards
- Weather icon (3-state system - see DESIGN RULES below)
- 3 country-specific story bullets (change with expertise level)
- 6 macro metrics: GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate
- 8 market metrics: Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, Exchange Rate, FX Vol
- Each metric is clickable -> opens deep-dive popover

### 3 Expertise Levels
- Beginner / Moderate / Expert toggle in top bar AND inside popovers
- Changes: stories, metric explanations, policy explainers, glossary definitions
- Everything rewrites itself per level

### Metric Popovers (14 per country)
- Current value display
- Historical chart (Chart.js)
- BLUF explanation (level-sensitive) with "Read more" expand for structured deep-dive
- Glossary terms link to bubbles EXCEPT the metric's own name (self-glossary suppression via exact-match Set)
- Data source attribution (metric-specific, e.g. "BEA (US) - Cabinet Office (JPN)")
- Navigation arrows (up/down) to cycle through all 14 metrics
- "Compare All Countries" button -> ranked bar chart across 9 countries

### Historical Charts (Magic 3 countries: USA, JPN, ITA)
- Annual data (6 points, 2020-2025): GDP Growth, Budget Deficit, Current Account, Policy Rate - rendered as BAR charts
- Monthly data (60 points, Jan 2021-Dec 2025): All other 10 metrics - rendered as LINE charts
- Policy Rate uses STEPPED line
- Yield Curve: green segments above zero, red below zero, prominent zero line
- Stock Market shows index name (S&P 500 / Nikkei 225 / FTSE MIB) not "Stock Market YTD"
- Range toggles: 1Y/2Y/5Y for monthly data, hidden for annual
- Bar chart coloring: positive = cyan, negative = red
- Cyan gradient fill on line charts

### Weather Grid ("Over Time" view)
- Accessible via: Any country -> GDP Growth -> Compare All Countries -> "Over Time" button
- Also: Any country -> Inflation (CPI) -> Compare All Countries -> "Over Time" button
- Shows 9 countries x 7 years (2020-2026F) grid with weather icons per cell
- GDP thresholds: sunny >=3%, cloudy 0-3%, stormy <0%
- Inflation thresholds: sunny 1-3% (on target), cloudy 0-1%/3-5%, stormy <0%/>5%
- 2026F column marked as forecast
- Legend at bottom
- Button appears at TOP of compare view, reads: [sun][cloud][storm] Over Time

### Compare Views
- Horizontal bar chart ranking all 9 countries for any metric
- Highlight bar for the country you came from
- FX regime tags (clickable) for exchange rate comparisons
- FX regime labels include country names (e.g. "United States - Free Float") and beginner explanations rewritten for all 9 countries

### Glossary System
- 170 terms at 3 expertise levels across 6 categories
- BLUF + expandable full definition with sections (Why it matters, Intuition, Example, What to watch)
- Inline: underlined terms throughout stories/explanations are clickable -> glossary bubble appears
- Footer glossary panel REMOVED - inline bubbles are the only glossary UX now
- Self-glossary suppression: exact match via Set, not substring

### 3 Global Stories (newsData)
- 🔥 Today's Story / ⚡ Biggest Movers / 💡 The Connection
- Written at all 3 expertise levels
- Currently static (BOJ carry trade, China property, dollar strength narratives)
- Source attribution on each story
- In production: will be generated daily by Claude API with real data feed

### Footer
- What? | How? | Who? | Legalese | Ping Me
- "Glossary" link removed
- Contact form in "Ping Me"

---

## DESIGN RULES (MUST OBEY)

### 0. THE UX MANDATE
**Clarity, smoothness, freshness and simplicity.** This is the vibe of the entire site. For this to go viral the UX must stay minimalist, obvious and simple. Every interaction should feel like one clean layer - not a stack of nested dialogs. **No popover spawning.** A popover should never open another popover. If content belongs together, it lives in one panel with progressive disclosure (BLUF + "Read more" expand). If a user has to mentally track which layer they're on, the UX has failed.

### 1. Weather Icon System - 3 States Only
**NEVER add intermediate states. NEVER change these without asking the user.**

| State | Emoji | CSS Class | CSS Filter |
|-------|-------|-----------|------------|
| Sunny | ☀️ | `wi-sun` / `w-icon sunny` | `filter: none` |
| Cloudy | ☁️ | `wi-cloud` / `w-icon cloudy` | `filter: brightness(.65) contrast(1.05) saturate(.3)` |
| Stormy | ☁️ | `wi-storm` / `w-icon stormy` | `filter: brightness(.15) contrast(1.2) saturate(0) drop-shadow(0 0 4px rgba(255,255,255,.35)) drop-shadow(0 0 8px rgba(255,255,255,.15))` |

**Prompt for any AI tool to reproduce these icons:**
> Use three weather-state icons built from emoji with CSS filters. Sunny = ☀️ emoji unfiltered. Cloudy = ☁️ emoji with brightness 0.65, contrast 1.05, saturation 0.3 - producing a muted grey. Stormy = ☁️ emoji with brightness 0.15, contrast 1.2, saturation 0, plus two white drop-shadows (4px and 8px blur at 35% and 15% opacity) to create a fog halo so the near-black cloud is visible on dark backgrounds. All icons are displayed inline in a flex container at the same size. No image assets - CSS filters only. This is a strict 3-state system: sunny, cloudy, stormy. No intermediate states.

Current country assignments: USA ☀️, CAN ☁️, GBR ☁️, JPN ☁️, DEU ⛈️, FRA ☁️, ITA ☁️, CHN ⛈️, IND ☀️

### 2. No Em Dashes
Use regular hyphens (-) everywhere. No em dashes, no en dashes. Applied globally across all text content.

### 3. Minimalist Presentation
Keep pages clean. Be very disciplined about what goes on screen. Every element must earn its place. This was the reason the footer glossary was killed.

### 4. No Emoji in UI
Claude should not use emoji in responses or UI unless specifically part of the weather icon system or the story labels (🔥⚡💡).

---

## MONETISATION DECISIONS

### Model: Freemium + Trial
- **Beginner level: FREE FOREVER** - top of funnel, viral loop, word-of-mouth
- **3-day full access trial** for Moderate + Expert (no credit card required)
- After trial: subscription for Moderate + Expert access
- Pricing TBD (discussed $9-20/month range, to be A/B tested with real users)
- Key conversion metric: "did user toggle to Expert at least once"

### B2B Opportunity
- Enterprise/seat licensing for banks, asset managers, universities
- The 3-level system doubles as a training tool
- Price per seat, annual contracts

### API/White-label
- Daily stories at 3 levels are a standalone licensable product
- Target: fintechs, neobanks, robo-advisors wanting macro context

### What to Avoid
- No ads (kills premium feel)
- No trading signals (regulatory nightmare)
- No one-time purchase (need recurring revenue for data pipeline)

### Pitch Line
"We monetise the complexity gap. Bloomberg charges $24k/year and assumes you understand macro. We charge $79/year and make sure you do."

---

## PRODUCTION ARCHITECTURE (DISCUSSED, NOT YET BUILT)

### Forecast Data Source
- Annual forecasts for 9 countries (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND) maintained manually in a Google Sheets worksheet
- Sheet ID: `1t0DKsZcCDj3GojF1TzszZQGLR4oqgppuBbmsldsHj8E` (public, exported as CSV)
- Metrics in sheet currently: GDP_Growth_2026, Inflation_2026, Budget_Deficit_2026, Current_Account_2026
- Unemployment_2026 is also forecast by the creator (may need adding to the sheet)
- These are proprietary estimates by the creator
- Future plan: once revenue supports it, switch to Consensus Economics as the forecast data source
- Loaded at Flask API startup via `forecast_loader.py`, cached in memory
- These forecasts feed the 2026F column in weather grids and forward-looking country data

### Backend Data Pipeline
The backend is a Flask/PostgreSQL/SQLAlchemy application that fetches, stores, and serves economic data for all 9 countries.

**Stack:** Python 3.13, Flask, SQLAlchemy, PostgreSQL, Anthropic SDK

**Database schema (4 tables):**
- `countries` - 9 M9 countries (code, name, flag, display_order)
- `metrics` - 8 economic metrics (code, name, unit, tooltips at 3 levels)
- `daily_data` - time series (country_id x metric_id x date x value) with unique constraint
- `cards` - AI-generated daily cards (headlines + stories at 3 levels, weather icon)

**Data sources and fetcher architecture:**
Each country has a `{country}_fetcher.py` and `{country}_loader.py` pair:

| Country | Fetcher | FRED Series | Stock (Yahoo) | Notes |
|---------|---------|-------------|---------------|-------|
| USA | `usa_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, DXY, current account | ^GSPC (S&P 500) | Budget from IMF WEO |
| CAN | `canada_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, CAD | ^GSPTSE (TSX) | Budget from WEO |
| GBR | `uk_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, GBP | ^FTSE | Budget from WEO |
| JPN | `japan_fetcher.py` | GDP, unemployment, policy rate, 10Y, JPY | ^N225 | Inflation not in FRED |
| DEU | `germany_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, EUR | ^GDAXI (DAX) | Budget from WEO |
| FRA | `france_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, EUR | ^FCHI (CAC 40) | Budget from WEO |
| ITA | `italy_fetcher.py` | GDP, CPI, unemployment, policy rate, 10Y, EUR | FTSEMIB.MI | Budget from WEO |
| CHN | `china_fetcher.py` | CPI, policy rate, CNY | 000001.SS (SSE) | GDP, unemployment, bond yield not in FRED |
| IND | `india_fetcher.py` | GDP, CPI, policy rate, 10Y, INR | ^BSESN (Sensex) | Unemployment, bond yield not in FRED |

**Shared fetchers:**
- `fred_fetcher.py` - FRED API wrapper (requires FRED_API_KEY env var)
- `yahoo_fetcher.py` - yfinance wrapper for stock indices and FX
- `weo_fetcher.py` - IMF World Economic Outlook (budget deficit/surplus data)
- `forecast_loader.py` - Google Sheets reader for proprietary 2026 forecasts

**Story generation (Claude API):**
- `multilevel_claude_service.py` (600 lines) - the Claude API integration
  - `MultiLevelClaudeGenerator` class with editorial context per country
  - Country "personality" strings (e.g. USA: "the anchor of global macro - everything here ripples outward")
  - Country theme anchors (e.g. JPN: "BoJ normalization, Shunto wages, yen weakness, corporate governance reform")
  - Generates 3 story bullets x 3 expertise levels per country
- `multilevel_card_generator.py` (405 lines) - orchestrates card generation for all countries
- `card_generator.py` (981 lines) - older single-level version (backup)

**API endpoints (api.py, 484 lines):**
- `GET /` - serves viewer HTML
- `GET /api/cards?level=beginner|moderate|expert` - all country cards with metric data, stories, weather, trends
- Forecasts loaded from Google Sheets at startup
- Custom forecast getter per country/metric

**Utility files:**
- `utils/database.py` - SQLAlchemy engine + context manager (`get_db()`)
- `utils/calculations.py` - YoY inflation calculation, historical transformations
- `models/schema.py` - current DB schema (Country, Metric, DailyData, Card)
- `models/multilevel_schema.py` - updated schema with expertise-level columns
- `init_database.py` - seeds 9 countries + 8 metrics
- `migrations/add_current_account_metric.py` - schema migration

**Environment variables required:**
- `FRED_API_KEY` - Federal Reserve Economic Data API
- `ANTHROPIC_API_KEY` - Claude API for story generation
- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://localhost/macrosnaps`)

**Data gaps (documented in fetcher files):**
- China: GDP, unemployment, bond yield not available in FRED
- India: unemployment, bond yield not available in FRED
- Japan: inflation not available in FRED

### Daily Story Generation
- Claude API generates 3 stories x 3 levels x 9 countries = 81 variants daily
- Architecture: real data in -> Claude narrative out (NEVER let Claude guess numbers)
- Data feed: market data API (FRED + Yahoo Finance + central bank APIs) runs daily
- News feed: Reuters/AP wire filtered to macro/markets
- Batch API call at 6am, cache results, serve all day
- Cost: few cents per batch run

### Story Style (tested with live Feb 2026 data)
- ~3 sentences per story per level
- Punchy, every word earns its place
- Beginner: explainer podcast tone
- Moderate: morning research email
- Expert: macro hedge fund CIO internal note

---

## GLOSSARY BACKEND ARCHITECTURE (NEW - Session 5/6)

### Overview
Glossary has been separated from the HTML into standalone category JSON files for production deployment. The HTML keeps thin entries for design testing only. The JSON files are the source of truth.

### Structured Data Format (no HTML)
All enriched entries use this clean format - no markup anywhere:

```json
{
  "GDP Growth": {
    "complexity": 1,
    "category": "macro",
    "levels": {
      "beginner": {
        "bluf": "Summary text here (230-280 chars)",
        "sections": [
          {"head": "Why it matters", "body": "Paragraph text"},
          {"head": "What to watch", "body": [
            "**Bold label:** bullet point text",
            "**Another:** more text"
          ]}
        ],
        "formal": "Technical definition."
      },
      "moderate": { "bluf": "...", "sections": [...], "formal": "..." },
      "expert": { "bluf": "...", "sections": [...], "formal": "..." }
    },
    "aliases": ["GDP growth rate"],
    "relatedTerms": ["real GDP", "recession"],
    "metricLinks": ["GDP Growth"]
  }
}
```

**Body** = string (paragraph) or array (bullet list). **Bold** = `**markdown**`. **No HTML anywhere.**

### 6 Category Files

| File | Total | Enriched | Thin |
|---|---|---|---|
| macro.json | 64 | 18 | 46 |
| credit.json | 28 | 2 | 26 |
| equity.json | 25 | 2 | 23 |
| fx.json | 26 | 2 | 24 |
| trade.json | 8 | 1 | 7 |
| institutions.json | 19 | 0 | 19 |
| **Total** | **170** | **25** | **145** |

### Enriched Entries (25)
**Metrics (14):** GDP Growth, Inflation (CPI), Unemployment, Budget Deficit, Current Account, Policy Rate, Stock Market YTD, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, Equity Vol, FX Vol, Exchange Rate
**General (1):** inflation
**Macro batch 1 (10):** interest rate, property crisis, real GDP, recession, automatic stabilisers, breakeven inflation, deflation, deposit rate, disinflation, dovish

### Recategorisation (Session 5/6)
Eliminated "general" category (was 107 entries) by redistributing:
- Monetary policy terms (QE, tapering, forward guidance, r-star, etc.) -> macro
- Sovereign bonds (bunds, gilts, BTPs, JGBs, OATs) -> credit
- Market indices (CAC 40, CSI 300, DAX, FTSE MIB) -> equity
- Currency mechanics (convertibility, sterilization, impossible trinity) -> fx
- Central banks and international orgs (BOE, BOJ, ECB, Fed, IMF, BIS) -> institutions

### Duplicate Consolidation (4 pairs merged)
- "zero lower bound" (kept) <- "ZLB" (alias)
- "Sov CDS" (kept) <- "sovereign CDS" (removed)
- "Yield Curve" (kept) <- "yield curve" (alias)
- "Unemployment" (kept) <- "unemployment rate" (removed)
- "Inflation (CPI)" and "inflation" both kept (metric vs general concept)

### Production Rendering
The structured JSON needs a renderer that converts sections/body/formal to HTML at runtime:
- `body` is string -> render as `<p>`
- `body` is array -> render as `<ul><li>` with `**bold**` -> `<strong>`
- `formal` -> render as `<div class="ge-formal">`

---

## TECHNICAL ARCHITECTURE

### HTML File (post-Session 4 refactor)
- Single HTML file, no build step, no dependencies except CDN-loaded Three.js r128 and Chart.js 4.4.0
- **Data layer**: 3 JSON blocks (`<script type="application/json">`) at bottom of file
  - `countries-data`: 9 consolidated country objects (metrics, stories, fxRegime, historical, weatherGrid)
  - `glossary-data`: 170 entries (thin for design, 15 enriched for metric popovers)
  - `app-config`: globalStories, metricExpl, metricSources, chartConfig, footer
- **Bootstrap script**: Parses JSON blocks and reconstructs all variables the renderer expects
- **Rendering code**: ~818 lines of pure logic, references no content directly
- `DATA` global object exposes the consolidated structure for future features

### Assemble/Render Separation (Session 4 - Step 4)
All 6 major renderers refactored into data assembly + pure rendering:
1. `showMTT` -> `assembleMTTData` + `renderMTT` (metric popovers)
2. `showCard` -> `assembleCardData` + `renderCard` (country cards)
3. `showCompare` -> `assembleCompareData` + `renderCompare` (bar chart rankings)
4. `showWeatherGDP` + `showWeatherCPI` -> unified `assembleWeatherGrid(metric)` + `renderWeatherGrid`
5. `showNewsTooltip` -> `assembleNewsData` + `renderNews`
6. `showBubble` -> `assembleGlossaryData` + `renderBubbleContent`

Original `show*` function signatures still exist as thin wrappers - all callers unchanged.

### Key Functions
- `applyGlossary(html, skipTerm)` wraps glossary terms in clickable spans; skipTerm suppresses self-linking (exact match via Set)
- `attachGlossary()` binds click handlers after DOM insertion
- `renderMetricChart()` handles all chart rendering with type/data detection
- `getBluf()` / `getFull()` extract BLUF and full content from {bluf, full} objects or plain strings
- Charts destroyed via `activeChart.destroy()` before recreation
- Country labels recreated every animation frame (60fps) with data-code attributes for delegation
- `currentLevel` global variable drives all content switching

### Adding a New Country
1. Add one object to `countries-data` JSON block with all fields (metrics, stories at 3 levels, fxRegime, weatherGrid)
2. Optionally add historical data in the same object
3. No rendering code changes needed

### Target Production Architecture
- `data/glossary/macro.json` etc. fetched at runtime from GitHub repo
- `data/countries/USA.json` etc. (one per country)
- `data/app-config.json` (stories, sources, chartConfig)
- `index.html` (shell + CSS + renderer)
- Lazy load glossary detail on click

---

## GLOSSARY VOICE/STYLE RULES
- **Beginner:** explainer podcast tone, no jargon without definition, concrete examples
- **Moderate:** research email to informed non-specialist, can use technical terms
- **Expert:** hedge fund CIO note, assumes full fluency, frameworks and models by name
- No em dashes (--) or en dashes (-), use hyphens (-) only
- British spelling (organisation, labour, favour)
- Bold in markdown: `**term:**` for bullet list labels
- BLUF: 230-320 chars depending on level
- Sections: Why it matters (always), Intuition/Example (beginner), What to watch (moderate/expert), formal definition (always)

---

## WHAT TO DO NEXT SESSION (in priority order)

### 1. Set up GitHub repo + Claude Code (START HERE)
- Create GitHub repo with the 6 glossary JSON files
- Install Claude Code on user's machine (Node.js + `npm install -g @anthropic-ai/claude-code`)
- Connect to GitHub (personal access token)
- Test: "add carry trade to glossary" -> Claude Code writes entry, commits to repo
- Once working, all future glossary work goes through Claude Code
- User is comfortable with terminal/command line

### 2. Continue enriching 145 thin entries
Do in batches of ~10, category by category:
- **Macro:** 46 remaining
- **Credit:** 26 remaining
- **FX:** 24 remaining
- **Equity:** 23 remaining
- **Institutions:** 19 remaining
- **Trade:** 7 remaining

### 3. Outstanding UX/Content Work
- Weather grids for more metrics beyond GDP and Inflation
- Mobile responsiveness improvements
- Searchable glossary overlay (small bookmark button)
- "See also" links between related glossary terms (schema ready)
- Charts for remaining 6 countries (CAN, GBR, DEU, FRA, CHN, IND) - only Magic 3 have historical data

### 4. Production Pipeline
- Daily story generation pipeline (Claude API + data feed)
- Paywall/trial UI implementation
- Backend: JSON blocks become standalone .json files served via API

---

## ARCHITECTURE DECISIONS MADE

1. **Single source of truth:** Glossary JSON files (not HTML). HTML keeps thin entries for design only.
2. **Structured data, not markup:** Sections/body/formal pattern. No HTML in JSON.
3. **6 categories:** macro, credit, equity, fx, trade, institutions. No "general".
4. **3 expertise levels:** beginner (explainer podcast), moderate (research email), expert (CIO note)
5. **BLUF + deep dive:** Every entry has bluf (always shown) + sections (shown on expand)
6. **GitHub as persistence:** Repo is the canonical store. Claude Code reads/writes directly.
7. **metricExpl deleted:** All metric explanations merged into glossary. assembleMTTData reads from glossary.
8. **policyExpl deleted:** Content was redundant. Unique policy mechanism content folded into metric sections.
9. **Assemble/render separation:** All renderers split into data assembly + pure rendering functions.
10. **Defensive rendering:** Missing data = skip section, never crash.

---

## SESSION HISTORY

### Session 1
- Built entire prototype from scratch: globe, 9 countries, cards, metrics, 3 expertise levels
- 155+ glossary terms at 3 levels with BLUF system
- Inline glossary click-to-define UX
- Global stories (🔥⚡💡) at 3 levels
- Footer with What/How/Who/Legalese/Ping Me
- FX regime tags on exchange rate comparisons

### Session 2
- Reordered market metrics
- Expanded charts from 2 to all 14 metrics with 5-year history
- Implemented bar/line/stepped chart types
- Yield Curve green/red coloring
- 60-month realistic time series for USA, JPN, ITA
- Metric navigation arrows (up/down) in popovers
- Config-driven chart metadata system

### Session 3
- Fixed country label clickability in Chrome (event delegation fix)
- Updated X/Y investor metrics: 29 views, 640+ data points per country
- Added GDP and Inflation Weather Grids (9 countries x 7 years)
- Settled on 3-state weather icon spec with CSS filters
- Replaced all 189 em dashes with regular hyphens
- Added data source attribution to all metric popovers
- Killed footer glossary panel
- Generated sample real-time stories using Feb 9 2026 data
- Discussed and decided monetisation model

### Session 4
- Established Design Rule #0: THE UX MANDATE
- Unified metric popover UX (BLUF + Read more, no double popovers)
- Enriched Inflation (CPI) with structured ge-section HTML at all 3 levels
- Added self-glossary suppression
- Killed policyExpl entirely (93 lines removed)
- MAJOR REFACTOR: Data layer separation into 3 JSON blocks
- Per-country consolidation (one JSON object per country)
- Glossary enriched schema (complexity, category, levels, aliases, relatedTerms, metricLinks)
- Fixed chart click bug

### Session 5
- Completed Step 4 refactor: all 6 renderers split into assemble + render pairs
- Completed Step 5: defensive rendering everywhere
- Unified metricExpl into glossary (metricExpl deleted from app-config)
- assembleMTTData now reads from glossary directly
- Enriched 14 metric entries with full BLUF + ge-section content at 3 levels
- Fixed self-glossary suppression to use exact-match Set (was substring)
- FX regime beginner explanations rewritten for all 9 countries
- FX regime labels now include country names

### Session 6
- Recategorised all 170 glossary entries: eliminated "general" (107 entries redistributed)
- Consolidated 4 duplicate pairs
- Enriched 10 macro batch 1 entries (interest rate, property crisis, real GDP, recession, automatic stabilisers, breakeven inflation, deflation, deposit rate, disinflation, dovish)
- Separated glossary backend from HTML into 6 category JSON files
- Converted all enriched entries from ge-section HTML to structured data (no HTML in JSON)
- Decided GitHub + Claude Code architecture for future glossary management
- User comfortable with terminal - Claude Code setup planned for next session

---

## FILES TO UPLOAD NEXT SESSION
1. `macrosnaps-globe.html` (the HTML file)
2. `glossary/macro.json`
3. `glossary/credit.json`
4. `glossary/equity.json`
5. `glossary/fx.json`
6. `glossary/trade.json`
7. `glossary/institutions.json`
8. `backend.zip` (the full Python backend)
9. This handover brief
