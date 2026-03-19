# MacroSnaps Handover Brief
## Session 8 - February 10, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard prototype. Single-page HTML app with a 3D globe (Three.js), 9 country cards with macro/market data, 3 expertise levels, inline glossary, historical charts, weather icon system, and comparison views. Built for investor demo and eventual production as a consumer fintech product.

**File:** `macrosnaps-globe.html` (~8,175 lines including pretty-printed JSON data, fully self-contained)

**Repo:** `github.com/ralphlazar/macrosnaps-01` (private)

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
- **ALL 170 ENTRIES FULLY ENRICHED** (completed Session 7 via Claude Code)
- BLUF + expandable full definition with sections (Why it matters, Intuition, Example, What to watch)
- Inline: underlined terms throughout stories/explanations are clickable -> glossary bubble appears
- Footer glossary panel REMOVED - inline bubbles are the only glossary UX now
- Self-glossary suppression: exact match via Set, not substring

### 3 Global Stories (newsData)
- Fire Today's Story / Lightning Biggest Movers / Lightbulb The Connection
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
| Sunny | sun | `wi-sun` / `w-icon sunny` | `filter: none` |
| Cloudy | cloud | `wi-cloud` / `w-icon cloudy` | `filter: brightness(.65) contrast(1.05) saturate(.3)` |
| Stormy | cloud | `wi-storm` / `w-icon stormy` | `filter: brightness(.15) contrast(1.2) saturate(0) drop-shadow(0 0 4px rgba(255,255,255,.35)) drop-shadow(0 0 8px rgba(255,255,255,.15))` |

Current country assignments: USA sun, CAN cloud, GBR cloud, JPN cloud, DEU storm, FRA cloud, ITA cloud, CHN storm, IND sun

### 2. No Em Dashes
Use regular hyphens (-) everywhere. No em dashes, no en dashes. Applied globally across all text content.

### 3. Minimalist Presentation
Keep pages clean. Be very disciplined about what goes on screen. Every element must earn its place. This was the reason the footer glossary was killed.

### 4. No Emoji in UI
Claude should not use emoji in responses or UI unless specifically part of the weather icon system or the story labels.

### 5. Mobile-Compatible by Default
Mobile is the launch priority (expect 60-70% mobile users). While the current prototype is desktop-first, **do not build desktop features that are fundamentally incompatible with mobile.** Every new feature should be designed so it can translate to a phone screen - even if the responsive CSS comes later. The globe is the one known risk (may become a flat map or country list on phone). Sharing must be native to the mobile experience.

---

## MONETIZATION DECISIONS

### Model: Freemium + Trial
- **Beginner + Moderate levels: FREE for university students** - top of funnel, viral loop
- **Beginner level: FREE FOREVER for everyone** - viral growth engine
- **3-day full access trial** for Expert (no credit card required)
- After trial: subscription for Expert access
- Pricing TBD (discussed $9-20/month range, to be A/B tested with real users)
- Key conversion metric: "did user toggle to Expert at least once"

### B2B Opportunity
- Enterprise/seat licensing for banks, asset managers, universities
- The 3-level system doubles as a training tool
- Price per seat, annual contracts
- Expert-level access is the thing they're paying for - giving it free to students doesn't undermine B2B because students get beginner + moderate only

### API/White-label
- Daily stories at 3 levels are a standalone licensable product
- Target: fintechs, neobanks, robo-advisors wanting macro context

### What to Avoid
- No ads (kills premium feel)
- No trading signals (regulatory nightmare)
- No one-time purchase (need recurring revenue for data pipeline)

### Pitch Line
"We monetize the complexity gap. Bloomberg charges $24k/year and assumes you understand macro. We charge $79/year and make sure you do."

### Sharing & Virality Strategy
**Mobile is the priority for launch. Sharing is the growth engine.**

**3 shareable units:**
1. **Country snapshot:** Flag, weather icon, 3 key numbers, one-line story. Generates a branded image card optimized for iMessage/WhatsApp/Twitter. Link to MacroSnaps underneath. This is the primary viral unit.
2. **Comparison chart:** The ranked bar chart for any metric across 9 countries. Exports as branded image. "Look where Italy ranks on debt" is a conversation starter.
3. **Glossary explainer:** A clean card with the BLUF for any term. One tap to share. "This is the best explanation of the yield curve I've seen."

**UX rules for sharing:**
- One subtle share icon per view (card, compare, popover) - not on everything. Minimalist rule applies.
- Content does the selling, not the button.
- Shared content generates either a branded image (for chat) or a deep link (for web).
- Deep links open directly to the relevant country/metric/term - never dump the user on the globe.
- Shared links are always viewable at beginner level without login or signup.
- Upgrade prompt appears only when they try to toggle to Expert.

**The viral loop:** Free beginner content -> user shares -> recipient sees beautiful snapshot -> taps link -> lands on beginner view -> explores -> hits Expert paywall -> converts.

---

## UNIVERSITY GO-TO-MARKET STRATEGY (Session 7)

### The core idea
Give beginner + moderate access free to university students. Students are the perfect audience: they share aggressively, they're learning macro for the first time, and some will become paying expert-level users after graduation.

### How to start
1. **Pick 5 professors at LSE** (alma mater - warmest leads)
2. Look for anyone teaching intro macro, international economics, or financial markets
3. Send a short email: "I'm an LSE econ grad (ex-Goldman, ex-CSFB) and I've built an interactive macro dashboard that explains 170 economic concepts at three levels. I'd love to offer it free to your students. Would you be open to a 5-minute demo?"
4. No pitch deck needed. The product speaks for itself.

### Why professors say yes
- They're always looking for teaching tools
- Investopedia is too simplistic, Bloomberg is too expensive
- The 3-level system is literally a pedagogical tool: beginner for first-years, moderate for upper-level, expert for postgrads

### Scale it up
- Once 2-3 professors are using it, get a one-line testimonial
- Email the next 50 professors with "Professor X at LSE uses this in their macro course"
- Contact university finance societies and economics clubs directly
- Create a simple page: macrosnaps.com/universities - "Free for students. Email us for access."

### Other marketing channels (in priority order)
1. **X/Twitter** - post one glossary card a day as an image. Finance Twitter is massive and engaged.
2. **Reddit** - r/economics, r/investing, r/financialindependence. Share useful content, don't promote.
3. **Product Hunt** - launch day spike, free to post, early adopter audience
4. **CFA/FRM study communities** - hundreds of thousands studying for finance exams globally
5. **Finance newsletter sponsorships** - Morning Brew, Chartr, The Daily Upside, Finimize. $500-2,000 per send.
6. **YouTube/TikTok** - 60-second explainer videos using the 3-level concept
7. **Financial advisors** - they need to explain macro to clients in plain language. Beginner level is what they wish they could send clients.

---

## THE LAUNCH TIGHTROPE: GOLDMAN-GRADE CONTENT, STARTUP-GRADE INFRASTRUCTURE (Session 7)

### The principle
Build Goldman-grade content (glossary, explanations, 3-level system - that's the moat and it's nearly done). Ship startup-grade infrastructure (the backend just needs to not break - that's a very different bar from "perfect"). The content is what makes people share it. The infrastructure is invisible to users unless it fails.

**The most dangerous risk is never launching.** Not a messy backend. Not imperfect data. Not missing sov CDS. Never launching.

### What MUST be real for launch (non-negotiable)
- **6 macro metrics** (GDP, inflation, unemployment, budget deficit, current account, policy rate) - real data, all 9 countries, from FRED + IMF WEO. Users will fact-check these. If US inflation is wrong, credibility is dead.
- **Stock markets and exchange rates** - real and current, from Yahoo Finance. People notice if the S&P 500 is stale.
- **Historical data from 2010** for all 9 countries - 15 years covers post-GFC recovery, low-rate era, COVID, inflation cycle, tightening cycle. Rich story.

### What can be APPROXIMATE at launch
- **Equity vol** - compute 30-day realized vol from stock index returns. VIX/VSTOXX data where available, realized vol fallback elsewhere.
- **FX vol** - 30-day realized vol from daily FX returns.
- **Corp spread** - FRED's ICE BofA BBB index (BAMLC0A4CBBB) for US, Euro equivalent for Europe. Proxies for Japan/China/India.
- **Sov CDS** - free reliable CDS data doesn't exist. Use sovereign spread over UST/Bunds as proxy. Label it honestly. Add real CDS when revenue supports Bloomberg ($24k/year).
- **Yield curve** - derived (10Y minus 2Y). FRED 2Y series where available, 10Y minus 3M as fallback.

### What does NOT need to exist at launch
- The full `UnifiedFetcher` architecture (build in month 3)
- The `data_sources` configuration table (build in month 3)
- Fetch logging and staleness alerts (build in month 3)
- Health monitoring endpoint (build in month 3)
- These are engineering comfort blankets that delay launch by weeks

### The 3-phase plan

**Phase 1: LAUNCH (4-6 weeks from now)**
- Extend current backend to fetch all 14 metrics from FRED + Yahoo for all 9 countries
- Backfill historical data to 2010
- Compute derived metrics (yield curve, vol) with simple Python
- Keep current 18-file fetcher architecture - messy but it works
- Ship: real data, complete glossary, stories, mobile layout, basic paywall
- Email 5 LSE professors. Post on X. Launch on Product Hunt.

**Phase 2: RELIABILITY (month 2-3, once users exist)**
- Refactor: replace 18 fetcher files with unified fetcher + data_sources table
- Add data quality checks and validation rules
- Set up daily pipeline (cron or Celery)
- Add staleness detection and alerting

**Phase 3: SCALE (month 4+, once revenue exists)**
- Polygon.io ($99/month) for reliable market data (replaces Yahoo Finance scraper)
- CEIC ($5-10k/year) for China/India data gaps if B2B justifies
- Bloomberg/Refinitiv ($22-24k/year) for real CDS data if B2B revenue justifies
- Consensus Economics forecasts (replaces Google Sheets)

### Data cost trajectory

| Stage | Sources | Cost |
|-------|---------|------|
| Launch | FRED + Yahoo Finance + IMF WEO + Google Sheets | Free |
| Month 3 | Add Polygon.io | $99/month |
| Month 6+ | Add CEIC (if B2B) | $5-10k/year |
| Year 1+ | Add Bloomberg/Refinitiv (if B2B revenue justifies) | $22-24k/year |

---

## COMPLETE FRED SERIES MATRIX (for backend backfill to 2010)

Full series IDs for all 14 metrics x 9 countries documented in `docs/data-backend-spec.md`. Key highlights:

**GDP Growth:** FRED has quarterly data for 8/9 countries. China requires IMF WEO (annual only).

**Inflation:** FRED has monthly CPI indices for all 9. Compute YoY from index.

**Unemployment:** FRED has 7/9. China (NBS quarterly) and India (CMIE or WEO) require alternative sources.

**Budget Deficit:** IMF WEO for all 9 (annual, GGXCNL_NGDP). Extend from 2010.

**Current Account:** FRED has quarterly data for all 9 (B6BLTT02STSAQ pattern).

**Policy Rate:** FRED has all 9. DEU/FRA/ITA share ECB rate (IRSTCI01EZM156N).

**10Y Bond Yield:** FRED has 8/9. China not reliably available.

**Exchange Rates:** FRED + Yahoo cover all 9.

**Derived metrics:** Yield curve (10Y - 2Y), equity vol (realized or VIX), FX vol (realized) - compute in Python.

---

## COMMODITIES CARD SPEC (Session 7 - designed, not yet built)

### Overview
10th globe dot ("CMDTY") at lat 0, lon -30 (mid-Atlantic). Opens a commodities card with 8 commodities in a grid. Click any commodity for a popover with 8 metrics, charts, and compare views.

### 8 Commodities
Brent Crude (BZ=F), WTI (CL=F), Gold (GC=F), Copper (HG=F), Natural Gas (NG=F), Iron Ore (TIO=F), Wheat (ZW=F), Silver (SI=F)

### Card layout
- Weather icon (overall commodity outlook, 3-state)
- 3 stories at 3 levels (same as country cards)
- Grid: 8 rows showing commodity name + price + YTD change
- Click any row -> popover

### 8 Metrics per commodity (uniform)
1. Current Price
2. YTD Change (%)
3. 52-Week Range
4. 30-Day Volatility
5. 200-Day Moving Average
6. Futures Curve (contango/backwardation)
7. Open Interest
8. Real Price vs Historical Average

### Compare view
Ranked bar chart across all 8 commodities for any metric.

### New glossary terms (add to glossary after implementation)
contango, backwardation, commodity supercycle, Dutch disease, resource curse, terms of trade, Brent-WTI spread, OPEC+, strategic petroleum reserve, open interest, futures curve

### Implementation files ready
- `data/commodities.json` - complete data for all 8 commodities
- `docs/commodities-spec.md` - full spec with functions, CSS, click handlers

---

## GLOSSARY BACKEND ARCHITECTURE

### Structured Data Format (no HTML)
```json
{
  "Term": {
    "complexity": 1,
    "category": "macro",
    "levels": {
      "beginner": {
        "bluf": "230-280 chars",
        "sections": [
          {"head": "Why it matters", "body": "Paragraph"},
          {"head": "What to watch", "body": ["**Label:** bullet", "**Label:** bullet"]}
        ],
        "formal": "Technical definition."
      },
      "moderate": { "bluf": "...", "sections": [...], "formal": "..." },
      "expert": { "bluf": "...", "sections": [...], "formal": "..." }
    },
    "aliases": [],
    "relatedTerms": [],
    "metricLinks": []
  }
}
```

**Body** = string (paragraph) or array (bullet list). **Bold** = `**markdown**`. **No HTML anywhere.**

### 6 Category Files - ALL ENRICHED (Session 7)

| File | Total | Enriched | Status |
|---|---|---|---|
| macro.json | 64 | 64 | COMPLETE |
| credit.json | 28 | 28 | COMPLETE |
| equity.json | 25 | 25 | COMPLETE |
| fx.json | 26 | 26 | COMPLETE |
| trade.json | 8 | 8 | COMPLETE |
| institutions.json | 19 | 19 | COMPLETE |
| **Total** | **170** | **170** | **ALL ENRICHED** |

Note: verify all commits landed on GitHub by checking commit history. fx.json and macro.json enrichment was running overnight via Claude Code parallel agents.

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

### Assemble/Render Separation (Session 4)
All 6 major renderers refactored into data assembly + pure rendering:
1. `showMTT` -> `assembleMTTData` + `renderMTT` (metric popovers)
2. `showCard` -> `assembleCardData` + `renderCard` (country cards)
3. `showCompare` -> `assembleCompareData` + `renderCompare` (bar chart rankings)
4. `showWeatherGDP` + `showWeatherCPI` -> unified `assembleWeatherGrid(metric)` + `renderWeatherGrid`
5. `showNewsTooltip` -> `assembleNewsData` + `renderNews`
6. `showBubble` -> `assembleGlossaryData` + `renderBubbleContent`

### Key Functions
- `applyGlossary(html, skipTerm)` wraps glossary terms in clickable spans; skipTerm suppresses self-linking
- `attachGlossary()` binds click handlers after DOM insertion
- `renderMetricChart()` handles all chart rendering with type/data detection
- `getBluf()` / `getFull()` extract BLUF and full content from {bluf, full} objects or plain strings
- `currentLevel` global variable drives all content switching

---

## GITHUB & CLAUDE CODE SETUP (Session 7)

### Repository
- **URL:** `github.com/ralphlazar/macrosnaps-01` (private)
- **Auth:** Personal access token (classic) with `repo` scope

### Claude Code
- Installed via Homebrew: `brew install --cask claude-code`
- Version: v2.1.38, Model: Opus 4.6 via Claude Max
- Permissions pre-approved for: file edits, git commands, python3 commands
- `CLAUDE.md` at project root gives Claude Code full project context

### How to resume
```bash
cd ~/Downloads/macrosnaps-repo
claude
```

---

## GLOSSARY VOICE/STYLE RULES
- **Beginner:** explainer podcast tone, no jargon without definition, concrete examples
- **Moderate:** research email to informed non-specialist, can use technical terms
- **Expert:** hedge fund CIO note, assumes full fluency, frameworks and models by name
- No em dashes (--) or en dashes (-), use hyphens (-) only
- US spelling (organization, labor, favor, stabilizers, defense)
- Bold in markdown: `**term:**` for bullet list labels
- BLUF: 230-320 chars depending on level
- Sections: Why it matters (always), Intuition/Example (beginner), What to watch (moderate/expert), formal definition (always)

---

## WHAT TO DO NEXT SESSION (in priority order)

### 1. Verify glossary enrichment completed
- Check GitHub commit history at `ralphlazar/macrosnaps-01`
- Confirm all 6 JSON files show 170/170 enriched
- If any failed overnight, re-run in Claude Code

### 2. US spelling pass
- In Claude Code: "Find and fix all British spellings across all 6 glossary JSON files, commit and push"
- Also check stories and UI text in the HTML file

### 3. Build commodities card
- Add `data/commodities.json` and `docs/commodities-spec.md` to repo
- In Claude Code: "Read docs/commodities-spec.md and data/commodities.json, then implement the commodities card feature in frontend/macrosnaps-globe.html following the spec exactly"

### 4. Extend backend data to 2010 (Phase 1 launch prep)
- Change `start_date` in all fetchers to 2010-01-01
- Extend WEO fetcher from `>= 2020` to `>= 2010`
- Add missing FRED series for 6 untracked metrics
- Add derived metric computations (yield curve, realized vol)
- Backfill all 14 metrics x 9 countries from 2010

### 5. Mobile design pass
### 6. Paywall/trial UI

---

## ARCHITECTURE DECISIONS MADE

1. **Single source of truth:** Glossary JSON files (not HTML).
2. **Structured data, not markup:** Sections/body/formal pattern. No HTML in JSON.
3. **6 categories:** macro, credit, equity, fx, trade, institutions. No "general".
4. **3 expertise levels:** beginner (explainer podcast), moderate (research email), expert (CIO note).
5. **BLUF + deep dive:** Every entry has bluf (always shown) + sections (shown on expand).
6. **GitHub as persistence:** Repo is the canonical store. Claude Code reads/writes directly.
7. **metricExpl deleted:** All metric explanations merged into glossary.
8. **policyExpl deleted:** Content was redundant.
9. **Assemble/render separation:** All renderers split into data assembly + pure rendering functions.
10. **Defensive rendering:** Missing data = skip section, never crash.
11. **Uniform country cards:** All 9 countries have identical metric structure (same 14 metrics).
12. **US spelling throughout.**
13. **Mobile: NOT YET ADDRESSED.** Launch priority (60-70% of users).
14. **Sharing as growth engine.** 3 shareable units, deep links, beginner always free.
15. **Goldman-grade content, startup-grade infrastructure.** (Session 7) Content is the moat. Infrastructure just needs to not break. Extend for launch, refactor in month 2-3, scale with paid sources when revenue justifies. Never let perfect infra delay launch.
16. **University-first go-to-market.** (Session 7) Beginner + moderate free for students. Expert behind paywall. Start with 5 LSE professors.
17. **Historical data from 2010.** (Session 7) 15 years of charts. Range toggles: 1Y / 3Y / 5Y / MAX.
18. **Commodities card: 8 commodities, 8 metrics, grid + popover UX.** (Session 7)

---

## SESSION HISTORY

### Session 1
- Built entire prototype from scratch: globe, 9 countries, cards, metrics, 3 expertise levels
- 155+ glossary terms at 3 levels with BLUF system
- Inline glossary click-to-define UX
- Global stories at 3 levels
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
- Discussed and decided monetization model

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
- Recategorized all 170 glossary entries: eliminated "general" (107 entries redistributed)
- Consolidated 4 duplicate pairs
- Enriched 10 macro batch 1 entries
- Separated glossary backend from HTML into 6 category JSON files
- Converted all enriched entries from ge-section HTML to structured data (no HTML in JSON)
- Decided GitHub + Claude Code architecture for future glossary management

### Session 7
- **GitHub repo created** at `ralphlazar/macrosnaps-01` (private), all files pushed
- **Claude Code installed** via Homebrew, authenticated with Claude Max (Opus 4.6)
- **CLAUDE.md** created at project root for Claude Code context
- **Glossary enrichment completed/in progress via Claude Code:**
  - trade.json: 8/8 enriched, committed, pushed
  - equity.json: 25/25 enriched, committed, pushed
  - credit.json: 28/28 enriched, committed, pushed
  - institutions.json: 19/19 enriched, committed, pushed
  - fx.json: 26/26 enrichment running overnight
  - macro.json: 64 entries enrichment running overnight (4 parallel agents)
  - British spelling fixes applied during enrichment
- **Commodities card designed:** 8 commodities, 8 metrics, grid + popover UX. Full spec and data file created.
- **Data backend architecture** audited. Complete FRED series matrix for 14 metrics x 9 countries documented. Honest assessment of current gaps.
- **Launch strategy decided:** Goldman-grade content, startup-grade infrastructure. 3-phase roadmap (launch free sources -> reliability refactor -> paid scale). Most dangerous risk is never launching.
- **University go-to-market strategy** defined. Beginner + moderate free for students. Expert behind paywall. Start with 5 LSE professors.
- **Marketing channels** prioritized: universities first, X/Twitter second, Reddit/Product Hunt third, newsletter sponsorships later.

---

## FILES IN REPO
```
macrosnaps-01/
  .gitignore
  .env.example
  CLAUDE.md
  README.md
  glossary/
    macro.json, credit.json, equity.json, fx.json, trade.json, institutions.json
  backend/
    api.py, init_database.py, __init__.py
    migrations/add_current_account_metric.py
    models/schema.py, multilevel_schema.py, __init__.py
    services/
      [9 country fetcher/loader pairs]
      card_generator.py, multilevel_card_generator.py, multilevel_claude_service.py
      data_loader.py, forecast_loader.py, fred_fetcher.py, yahoo_fetcher.py, weo_fetcher.py
    utils/database.py, calculations.py, __init__.py
  frontend/macrosnaps-globe.html
  docs/handover-session7.md, setup-guide.md
  [To add: data/commodities.json, docs/commodities-spec.md, docs/data-backend-spec.md]
```
