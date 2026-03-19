# MacroSnaps Handover Brief
## Session 4 - February 9, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard prototype. Single-page HTML app with a 3D globe (Three.js), 9 country cards with macro/market data, 3 expertise levels, inline glossary, historical charts, weather icon system, and comparison views. Built for investor demo and eventual production as a consumer fintech product.

**File:** `macrosnaps-globe.html` (~7,766 lines including pretty-printed JSON data, fully self-contained)

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
- BLUF explanation (level-sensitive) with "Read more" expand for structured deep-dive (ge-section format)
- Glossary terms link to bubbles EXCEPT the metric's own name (self-glossary suppression)
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

### Glossary System
- 155+ terms at 3 expertise levels
- BLUF + expandable full definition with sections (Why it matters, Intuition, Example, etc.)
- Inline: underlined terms throughout stories/explanations are clickable -> glossary bubble appears
- Footer glossary panel REMOVED (this session) - inline bubbles are the only glossary UX now

### 3 Global Stories (newsData)
- 🔥 Today's Story / ⚡ Biggest Movers / 💡 The Connection
- Written at all 3 expertise levels
- Currently static (BOJ carry trade, China property, dollar strength narratives)
- Source attribution on each story
- In production: will be generated daily by Claude API with real data feed

### Footer
- What? | How? | Who? | Legalese | Ping Me
- "Glossary" link removed this session
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

### Daily Story Generation
- Claude API generates 3 stories x 3 levels x 9 countries = 81 variants daily
- Architecture: real data in -> Claude narrative out (NEVER let Claude guess numbers)
- Data feed: market data API (FRED + Yahoo Finance + central bank APIs) runs daily
- News feed: Reuters/AP wire filtered to macro/markets
- Batch API call at 6am, cache results, serve all day
- Cost: few cents per batch run

### Story Style (tested this session with live Feb 2026 data)
- ~3 sentences per story per level
- Punchy, every word earns its place
- Beginner: explainer podcast tone
- Moderate: morning research email
- Expert: macro hedge fund CIO internal note

---

## WHAT WAS DONE THIS SESSION (Session 4)

1. Established Design Rule #0: THE UX MANDATE - clarity, smoothness, freshness, simplicity, no popover spawning
2. Unified metric popover UX - BLUF explanation now renders directly in the metric tooltip with inline "Read more" expand, eliminating the previous two-popover flow
3. Converted 7 metricExpl entries to {bluf, full} objects across all 3 expertise levels: Inflation (CPI), Yield Curve, Corp Spread, Sov CDS, Equity Vol, FX Vol
4. Enriched Inflation (CPI) "full" content with structured ge-section HTML (Why it matters, Intuition, Example, What to watch) at all 3 levels - matching glossary quality
5. Added self-glossary suppression - applyGlossary() now accepts a skipTerm parameter so a metric popover does not create a clickable glossary link for its own name
6. Refocused Inflation policyExpl at all 3 levels: renamed from "Inflation & Price Stability" to "How Central Banks Respond", content now covers central bank mechanism (rate transmission, lags, reaction function) instead of re-explaining what inflation is
7. Added CSS spacing between BLUF text and "Read more" link (margin-top:12px, display:block)
8. Killed policyExpl entirely (data, rendering, CSS) - 93 lines removed. Content was redundant with BLUF-enriched metricExpl. Any unique policy mechanism content to be folded into metricExpl full sections during BLUF conversion of remaining metrics
9. MAJOR REFACTOR: Data layer separation (Steps 1-3 of architecture plan)
   - All data extracted from inline JS into 3 typed JSON blocks: `<script type="application/json" id="countries-data|glossary-data|app-config">`
   - Bootstrap script parses JSON and reconstructs all variables the renderer expects
   - Rendering code unchanged (818 lines pure logic, zero content)
   - Step 1: countries-data (57KB), glossary-data (149KB), app-config (25KB)
   - Step 2: Per-country consolidation - each country is now one JSON object containing: code, name, flag, lat, lon, weather, metrics, stories (3 levels), fxRegime, historical data, weatherGrid (GDP + CPI)
   - Step 3: Glossary enriched schema - each entry now has: complexity, category (auto-detected: macro/fx/credit/equity/trade/general), levels (beginner/moderate/expert each with bluf/full), plus empty scaffolding for aliases, relatedTerms, metricLinks
   - metricSources extracted from inline showMTT function to app-config JSON
   - Adding a new country now means adding one JSON object (not editing 7 separate data structures)
   - Editing glossary/content is now safe JSON editing (no JS string escaping landmines)

## WHAT WAS DONE IN PREVIOUS SESSIONS

### Session 3

1. Fixed country label clickability in Chrome (event delegation fix)
2. Updated X/Y investor metrics: 29 views, 640+ data points per country
3. Added GDP Weather Grid (all 9 countries, 2020-2026F, 3-state icons)
4. Added Inflation Weather Grid (same format, inverted logic - sunny = on target)
5. Redesigned weather icons: emoji -> CSS icons -> back to emoji with CSS filters (3 iterations)
6. Settled on final 3-state icon spec (sunny/cloudy/stormy)
7. Aligned ALL weather icons across the app (card icons + grid icons + button icons)
8. Fixed country data: removed old 5-state emoji (🌤️🌧️), all 9 countries now use only ☀️/☁️/⛈️
9. Replaced all 189 em dashes with regular hyphens
10. Added data source attribution to all metric popovers
11. Removed "Economic data has 2-3 month delay" note from popovers
12. Synced Inflation (CPI) BLUF across glossary and metric popovers (all 3 levels)
13. "Over Time" button moved to top of compare view, label changed to [3 icons] Over Time
14. Killed footer glossary panel (CSS + JS + HTML, ~165 lines removed)
15. Removed "Glossary" link from footer
16. Generated sample real-time stories using Feb 9 2026 data (Warsh nomination, gold crash, dollar whipsaw)
17. Discussed and decided monetisation model

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

---

## OUTSTANDING / FUTURE IDEAS

### Content (next priority)
- Enrich remaining 6 BLUF metrics (Yield Curve, Corp Spread, Sov CDS, Equity Vol, FX Vol) with structured ge-section HTML like Inflation. Fold any unique policy mechanism content from the killed policyExpl into these sections.
- BLUF-convert all 160 glossary entries (currently most are plain strings, not {bluf, full} objects)
- Populate glossary aliases, relatedTerms, metricLinks fields (scaffolding in place, all empty)
- Refine glossary category auto-detection (107 of 160 entries defaulted to "general")
- Charts for remaining 6 countries (CAN, GBR, DEU, FRA, CHN, IND) - only Magic 3 have historical data

### UX
- Weather grids for more metrics beyond GDP and Inflation
- Mobile responsiveness improvements
- Searchable glossary overlay (small bookmark button) as lightweight replacement for killed footer glossary
- "See also" links between related glossary terms (schema ready)

### Production
- Daily story generation pipeline (Claude API + data feed)
- Paywall/trial UI implementation
- Backend: JSON blocks become standalone .json files served via API
- Build step: concatenate JSON + app code into single deployable HTML

---

## TECHNICAL NOTES

### Architecture (post-Session 4 refactor)
- Single HTML file, no build step, no dependencies except CDN-loaded Three.js r128 and Chart.js 4.4.0
- **Data layer**: 3 JSON blocks (`<script type="application/json">`) at bottom of file
  - `countries-data`: 9 consolidated country objects (metrics, stories, fxRegime, historical, weatherGrid)
  - `glossary-data`: 160 enriched entries (complexity, category, levels with bluf/full, aliases, relatedTerms, metricLinks)
  - `app-config`: globalStories, metricExpl, metricSources, chartConfig, footer
- **Bootstrap script**: Parses JSON blocks and reconstructs all variables the renderer expects
- **Rendering code**: ~818 lines of pure logic, references no content directly
- `DATA` global object exposes the consolidated structure for future features

### Key Functions
- `applyGlossary(html, skipTerm)` wraps glossary terms in clickable spans; skipTerm suppresses self-linking
- `attachGlossary()` binds click handlers after DOM insertion
- `renderMetricChart()` handles all chart rendering with type/data detection
- `showCompare()` builds ranked bar chart with animated bars
- `showWeatherGDP()` / `showWeatherCPI()` build the weather grids
- `getBluf()` / `getFull()` extract BLUF and full content from {bluf, full} objects or plain strings
- Charts destroyed via `activeChart.destroy()` before recreation
- Country labels recreated every animation frame (60fps) with data-code attributes for delegation
- `currentLevel` global variable drives all content switching

### Adding a New Country
1. Add one object to `countries-data` JSON block with all fields (metrics, stories at 3 levels, fxRegime, weatherGrid)
2. Optionally add historical data in the same object
3. No rendering code changes needed
