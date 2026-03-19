# MacroSnaps Handover Brief
## Session 8 - February 10, 2026

---

## WHAT IS MACROSNAPS

An interactive economic dashboard prototype. 3D globe (Three.js) with weather-colored country dots, 9 country cards with macro/market data, 3 expertise levels, inline glossary, historical charts, weather icon system, and comparison views. Built for consumer fintech launch and eventual B2B licensing.

**Prototype:** `macrosnaps-globe.html` (~8,175 lines, fully self-contained)

**New prototype:** `macrosnaps-globe-weather.html` (Session 8 - redesigned globe with weather-shaded dots, floating card UI)

**Repo:** `github.com/ralphlazar/macrosnaps-01` (private)

**Creator:** Ralph Lazar - MSc Economics (LSE), ex-Goldman Sachs Global Equity Strategy, ex-CSFB Fixed-Income Prop Trading.

---

## SESSION 8 SUMMARY

### What happened this session

1. **Data backend audit and spec.** Reviewed all 18 fetcher/loader files. Documented the full FRED series matrix for 14 metrics x 9 countries. Identified gaps (China GDP/unemployment, sov CDS, corp spreads outside US). Created `docs/data-backend-spec.md` with the target production architecture.

2. **Launch tightrope decision.** Resolved the tension between Goldman-grade backend and shipping as a solo entrepreneur. Decision: Goldman-grade content (the moat), startup-grade infrastructure (just needs to not break). 3-phase roadmap defined. The most dangerous risk is never launching.

3. **App strategy discussion.** Covered: domain/handle lockdown, competitive advantage (3-level system is genuinely novel), daily habit (stories pipeline), solo founder tradeoffs, content treadmill, legal structure, personal brand as underused asset.

4. **Home screen redesign - weather map exploration.**
   - First attempt: flat 2D world map with countries shaded by weather. User verdict: "looks boring and I've seen that before." Every COVID tracker and election night dashboard since 2020.
   - Second attempt: 3D globe with weather-colored dots. Sunny countries glow warm amber with shimmer. Stormy countries pulse dark purple. Atmospheric blue rim glow. User verdict: "I like that."
   - Card iteration: started as bottom sheet (too big), then reduced bottom sheet (still a footer), then floating card centered over globe with X close button (approved).

5. **Final prototype delivered.** `macrosnaps-globe-weather.html` - working 3D globe with 9 weather-colored dots, floating card with 6 macro + 8 market metrics in 2-column grid, consistent weather icons per brief spec.

---

## NEW DESIGN DIRECTION (Session 8)

### The globe IS the weather map
The globe is not just navigation - it communicates the state of the world economy at a glance through color. Sunny economies glow warm amber. Stormy economies pulse dark bruised purple. Cloudy economies sit quiet in muted grey-blue. Without reading a single number, you can see where the strength and trouble are.

### Country dot colors

**Sunny (expanding):** warm amber core (#e8b84a), double glow halo, subtle shimmer animation. Immediately draws the eye. Used for: USA, IND.

**Cloudy (mixed):** muted grey-blue (#5a6a7a), smaller dot, no glow. Present but quiet. Used for: CAN, GBR, JPN, FRA, ITA.

**Stormy (contracting):** dark bruised purple (#6a3a5e / #4a2a4e), slow pulse animation cycling opacity. Feels unsettled. Used for: DEU, CHN.

### Globe design
- Dark sphere (#0a0f1a) with atmospheric blue rim glow (shader-based)
- Subtle latitude lines at 30-degree intervals (near-invisible)
- Slow auto-rotation, drag to spin, momentum on release
- Country labels float near dots: flag emoji + country code
- Labels fade when on back side of globe

### Card design (floating, not bottom sheet)
- Centered over globe, glassmorphism background (blur + transparency)
- X close button in top right corner
- Also closes on: Escape key, clicking globe background, clicking another country
- Flag + country name + weather icon in header
- Story text (one paragraph, level-sensitive)
- 6 macro metrics in 2-column grid
- 8 market metrics in 2-column grid
- Each metric tile: label, value, change indicator (green/red/grey)

### Top bar
- Brand: pulse dot + "MACROSNAPS" (uppercase, letter-spaced)
- Beginner / Moderate / Expert level toggle
- No nav tabs in current prototype (World/Commodities planned)

### Bottom ticker
- 3 global stories as scrollable ticker strip
- Fire / Lightning / Lightbulb labels

### Legend
- Bottom left: Expanding (gold) / Mixed (grey) / Contracting (purple)
- Hides when card is open

### Scaling to 20+ countries
This design scales naturally. Adding countries means adding dots to the globe - no grid redesign, no layout changes. At 40+ countries the globe gets richer and more interesting, not more cluttered. Dark unlit regions represent countries not yet covered - creates visual anticipation for expansion.

### Mobile
Globe can work on mobile with touch drag. Card stays as centered floating panel. At very small screens, card width adapts to near-full-width. Ticker hides on mobile. The globe + floating card pattern translates well to phone screens.

### What was rejected
- **Flat 2D colored world map.** Too conventional. Looks like every election/COVID dashboard. "Boring and I've seen that before."
- **Bottom sheet card.** Too dominant, obscures the globe. Footer pattern feels generic.
- **Sidebar feed.** Conventional fintech thinking. Bloomberg lite. Nobody looks at that and thinks "this is interesting."
- **Weather-themed language** ("clearing skies in Japan"). Too gimmicky. Writing stays as sharp economic analysis. Weather icons are visual shorthand only, not a writing style.

---

## CURRENT FEATURE SET

### Globe and Navigation
- 3D globe with weather-colored dots for 9 countries
- Country labels (flag + code) float near dots
- Blue atmospheric glow rim
- Drag to rotate, auto-rotation resumes after 3s idle
- Click dot to open floating country card
- Raycasting on invisible hit-target spheres for click detection

### 9 Countries (weather assignments)
USA (sunny), CAN (cloudy), GBR (cloudy), JPN (cloudy), DEU (stormy), FRA (cloudy), ITA (cloudy), CHN (stormy), IND (sunny)

### Country Cards (14 metrics)
**6 Macro:** GDP Growth, Inflation, Unemployment, Budget Deficit, Current Account, Policy Rate

**8 Market:** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, Exchange Rate, FX Vol

### 3 Expertise Levels
- Beginner / Moderate / Expert toggle in top bar
- Changes: stories, metric explanations, glossary definitions
- Everything rewrites itself per level

### Metric Popovers (in original prototype)
- Current value display
- Historical chart (Chart.js)
- BLUF explanation (level-sensitive) with "Read more" expand
- Glossary terms link to bubbles (self-glossary suppression via exact-match Set)
- Data source attribution
- Navigation arrows to cycle through all 14 metrics
- "Compare All Countries" button -> ranked bar chart

### Historical Charts (original prototype - Magic 3: USA, JPN, ITA)
- Annual data (6 points, 2020-2025): bar charts
- Monthly data (60 points): line charts
- To be extended to 2010 for all 9 countries (see backend section)

### Weather Grid ("Over Time" view - original prototype)
- 9 countries x 7 years grid with weather icons per cell
- GDP and Inflation thresholds defined
- Accessible via Compare All Countries -> Over Time button

### Glossary System
- 170 terms at 3 expertise levels across 6 categories
- **ALL 170 ENTRIES FULLY ENRICHED** (completed Session 7 via Claude Code)
- BLUF + expandable sections (Why it matters, Intuition, Example, What to watch)
- Inline clickable terms -> glossary bubble

### 3 Global Stories
- Fire / Lightning / Lightbulb
- Written at all 3 expertise levels
- Currently static; in production generated daily by Claude API

---

## DESIGN RULES (MUST OBEY)

### 0. THE UX MANDATE
**Clarity, smoothness, freshness and simplicity.** The site must look completely different from anything else. A user or investor must think "ok, this is interesting." No popover spawning. One clean layer at a time.

### 1. Weather Icon System - 3 States Only
**NEVER add intermediate states. NEVER change these without asking the user.**

| State | Icon | CSS Filter |
|-------|------|------------|
| Sunny | sun emoji | `filter: none` |
| Cloudy | cloud emoji | `filter: brightness(.65) contrast(1.05) saturate(.3)` |
| Stormy | cloud emoji | `filter: brightness(.15) contrast(1.2) saturate(0) drop-shadow(...)` |

All three states use the same base emoji approach. Stormy uses the CLOUD icon with the dark filter applied - NOT a storm/thunder emoji.

### 2. No Em Dashes
Use regular hyphens (-) everywhere.

### 3. Minimalist Presentation
Every element must earn its place.

### 4. No Emoji in UI
Except weather icons and story labels.

### 5. Mobile-Compatible by Default
60-70% of users expected on mobile. Globe works with touch. Card adapts to screen width.

---

## THE LAUNCH TIGHTROPE (Session 8)

### Principle
**Goldman-grade content, startup-grade infrastructure.** The content (glossary, 3-level explanations, editorial voice) is the moat. The infrastructure just needs to not break. The most dangerous risk is never launching.

### What MUST be real for launch
- 6 macro metrics: real data, all 9 countries, from FRED + IMF WEO
- Stock markets and exchange rates: real and current, from Yahoo Finance
- Historical data from 2010: 15 years of charts

### What can be approximate at launch
- Equity vol, FX vol: computed realized vol from returns
- Corp spread: FRED ICE BofA indices for US/Europe, proxies elsewhere
- Sov CDS: sovereign spread proxy (free CDS data doesn't exist)
- Yield curve: derived 10Y minus 2Y

### What doesn't need to exist at launch
- UnifiedFetcher architecture (month 3)
- data_sources configuration table (month 3)
- Fetch logging and staleness alerts (month 3)
- Health monitoring (month 3)

### 3-Phase Plan

**Phase 1 - LAUNCH (4-6 weeks):** Extend current fetchers to 2010. Add missing FRED series. Compute derived metrics. Keep 18-file architecture. Ship with real data, glossary, stories, mobile layout, basic paywall. Email 5 LSE professors. Post on X. Product Hunt.

**Phase 2 - RELIABILITY (month 2-3):** Refactor to unified fetcher. Data quality checks. Daily pipeline (cron/Celery). Staleness detection.

**Phase 3 - SCALE (month 4+):** Polygon.io ($99/month). CEIC ($5-10k/year if B2B). Bloomberg ($22-24k/year if B2B revenue justifies).

### Data cost trajectory
| Stage | Cost |
|-------|------|
| Launch | Free (FRED + Yahoo + IMF WEO) |
| Month 3 | $99/month (Polygon.io) |
| Month 6+ | $5-10k/year (CEIC, if B2B) |
| Year 1+ | $22-24k/year (Bloomberg, if B2B revenue justifies) |

---

## APP STRATEGY NOTES (Session 8)

### Things to lock down now
- **Domain:** macrosnaps.com (check availability, buy tonight)
- **X handle:** @macrosnaps or similar
- **App Store name:** MacroSnaps

### Competitive advantage
Not the data (Bloomberg has better data). The advantage is treating macro literacy as a product problem. The 3-level system is genuinely novel. Nobody else does it. The editorial voice at three levels of sophistication is the moat.

### Daily habit
The most valuable apps are daily habits. The story pipeline (Claude API) is the key. "What happened in macro yesterday, explained at my level" - that's a daily open. Consider email/push notifications for daily digest at launch, not as afterthought.

### Content treadmill
170 glossary terms are done. But users expect content to feel alive - new terms when news breaks, existing terms updated when policy changes. Budget for ongoing editorial maintenance.

### Legal structure
Need before launch: company entity, terms of service, privacy policy, GDPR compliance (European university audience).

### Personal brand
LSE economics + Goldman global equity strategy + CSFB fixed-income prop. That credibility stack should be front and center: X bio, Product Hunt launch, professor emails, about page. People trust macro commentary from someone who traded on it.

### The globe stays
The globe is a genuine differentiator. Most fintech looks like it was designed by a compliance department. The globe makes someone stop and think "this is different." The weather-colored dots communicate economic health at a glance. Keep it. At 20+ countries, the globe scales naturally - just add dots.

---

## MONETIZATION DECISIONS

### Model: Freemium + Trial
- **Beginner + Moderate: FREE for university students**
- **Beginner: FREE FOREVER for everyone**
- **3-day trial** for Expert (no credit card)
- Subscription for Expert after trial
- Pricing TBD ($9-20/month, A/B test)

### B2B
- Seat licensing for banks, asset managers, universities
- Expert-level access is the product
- Daily stories at 3 levels are independently licensable

### Pitch Line
"Bloomberg charges $24k/year and assumes you understand macro. We charge $79/year and make sure you do."

### Sharing and Virality
3 shareable units: country snapshot, comparison chart, glossary explainer. Deep links to specific content. Beginner level always free and viewable without login.

---

## UNIVERSITY GO-TO-MARKET

1. Start with 5 LSE professors (alma mater)
2. Short email: "I'm an LSE econ grad (ex-Goldman, ex-CSFB), built an interactive macro dashboard, 170 concepts at 3 levels, free for students"
3. Scale via testimonials and student org outreach
4. Other channels: X/Twitter, Reddit, Product Hunt, CFA/FRM communities, newsletter sponsorships

---

## COMMODITIES CARD SPEC (Session 7 - not yet built)

10th globe dot ("CMDTY") with 8 commodities: Brent (BZ=F), WTI (CL=F), Gold (GC=F), Copper (HG=F), Natural Gas (NG=F), Iron Ore (TIO=F), Wheat (ZW=F), Silver (SI=F). 8 metrics per commodity. Grid + popover UX. Full spec in `docs/commodities-spec.md`.

Note from Session 8 discussion: at 20+ countries, commodities may work better as a separate tab ("World | Commodities") rather than a globe dot, since non-country entities don't have a natural geographic position.

---

## GLOSSARY

### All 170 entries enriched (Session 7)
| File | Total | Status |
|---|---|---|
| macro.json | 64 | COMPLETE |
| credit.json | 28 | COMPLETE |
| equity.json | 25 | COMPLETE |
| fx.json | 26 | COMPLETE |
| trade.json | 8 | COMPLETE |
| institutions.json | 19 | COMPLETE |

Verify all commits landed on GitHub.

### Entry format (no HTML)
```json
{
  "Term": {
    "complexity": 1,
    "category": "macro",
    "levels": {
      "beginner": { "bluf": "...", "sections": [...], "formal": "..." },
      "moderate": { "bluf": "...", "sections": [...], "formal": "..." },
      "expert": { "bluf": "...", "sections": [...], "formal": "..." }
    },
    "aliases": [], "relatedTerms": [], "metricLinks": []
  }
}
```

---

## COMPLETE FRED SERIES MATRIX

Full matrix documented in `docs/data-backend-spec.md`. Key highlights:

- **GDP Growth:** FRED has quarterly for 8/9. China requires IMF WEO (annual).
- **Inflation:** FRED monthly CPI for all 9 (compute YoY from index).
- **Unemployment:** FRED has 7/9. China/India require alternative sources.
- **Budget Deficit:** IMF WEO for all 9 (annual, GGXCNL_NGDP).
- **Current Account:** FRED quarterly for all 9 (B6BLTT02STSAQ pattern).
- **Policy Rate:** FRED all 9. DEU/FRA/ITA share ECB rate.
- **10Y Bond Yield:** FRED has 8/9. China not reliable.
- **Exchange Rates:** FRED + Yahoo cover all 9.
- **Derived:** yield curve (10Y-2Y), equity vol (realized/VIX), FX vol (realized).
- **Sov CDS:** no free source. Sovereign spread proxy at launch.

---

## PRODUCTION ARCHITECTURE

### Backend
Python 3.13, Flask, SQLAlchemy, PostgreSQL, Anthropic SDK.

### Data sources
| Source | Cost | Covers |
|--------|------|--------|
| FRED API | Free | US + international macro (80% of needs) |
| Yahoo Finance (yfinance) | Free but fragile | Stock indices, FX, commodities |
| IMF WEO | Free | Budget deficits, annual macro |
| Google Sheets | Free | Proprietary 2026 forecasts |

### Fetcher architecture (current - 18 files)
Each country has `{country}_fetcher.py` + `{country}_loader.py`. Shared: `fred_fetcher.py`, `yahoo_fetcher.py`, `weo_fetcher.py`, `forecast_loader.py`.

### Story generation
`multilevel_claude_service.py` - Claude API generates 3 stories x 3 levels x 9 countries. Country personality strings and theme anchors.

### Environment variables
- `FRED_API_KEY`
- `ANTHROPIC_API_KEY`
- `DATABASE_URL` (default: `postgresql://localhost/macrosnaps`)

---

## GITHUB AND CLAUDE CODE

### Repository
`github.com/ralphlazar/macrosnaps-01` (private). Personal access token auth.

### Claude Code
Homebrew install, Opus 4.6 via Claude Max. Resume:
```bash
cd ~/Downloads/macrosnaps-repo
claude
```

### CLAUDE.md at project root
Gives Claude Code full project context automatically.

---

## WHAT TO DO NEXT SESSION (in priority order)

### 1. Verify glossary enrichment
Check GitHub commits. Confirm 170/170 enriched. Re-run any failures.

### 2. US spelling pass
In Claude Code: "Find and fix all British spellings across all 6 glossary JSON files"

### 3. Build commodities card
Add spec files to repo. Prompt Claude Code to implement from `docs/commodities-spec.md`.

### 4. Extend backend data to 2010
Change start dates in all fetchers. Extend WEO from >=2020 to >=2010. Add missing FRED series for 6 untracked metrics. Add derived metric computations. Backfill 14 metrics x 9 countries.

### 5. Integrate new globe design into main prototype
The new `macrosnaps-globe-weather.html` is a standalone prototype. Merge the weather-dot globe and floating card UX into the main `macrosnaps-globe.html` that has all the actual data, popovers, charts, glossary, and compare views.

### 6. Mobile design pass
### 7. Paywall/trial UI

---

## ARCHITECTURE DECISIONS

1. Single source of truth: glossary JSON files
2. Structured data, no HTML in JSON
3. 6 categories: macro, credit, equity, fx, trade, institutions
4. 3 expertise levels: beginner, moderate, expert
5. BLUF + deep dive pattern
6. GitHub as persistence
7. metricExpl deleted (merged into glossary)
8. policyExpl deleted
9. Assemble/render separation
10. Defensive rendering
11. Uniform country cards (same 14 metrics)
12. US spelling throughout
13. Mobile priority (60-70% of users)
14. Sharing as growth engine (3 shareable units)
15. **Goldman-grade content, startup-grade infrastructure** (Session 7/8)
16. **University-first go-to-market** (Session 7)
17. **Historical data from 2010** (Session 7/8)
18. **Commodities: 8 commodities, 8 metrics** (Session 7)
19. **Globe with weather-colored dots is the home screen** (Session 8). Not a flat map. Not a grid. The globe communicates economic health through color at a glance. Scales to 20+ countries by adding dots.
20. **Floating card over globe** (Session 8). Not a bottom sheet. Not a sidebar. Centered glassmorphism panel with X close button. Globe stays visible underneath.
21. **Weather icons are visual shorthand only** (Session 8). Do not write weather-themed language. Writing stays as sharp economic analysis. The icons just sit on top as instant visual read.

---

## SESSION HISTORY

### Sessions 1-6
(See Session 7 handover for full details)
- Built prototype: globe, 9 countries, cards, 14 metrics, 3 levels, glossary, charts, weather grids, compare views
- Major refactors: data layer separation, assemble/render split, defensive rendering
- Glossary: recategorized 170 entries, separated into 6 JSON files

### Session 7
- GitHub repo created, Claude Code installed
- Glossary enrichment: 170/170 via parallel Claude Code agents
- Commodities card designed (spec + data file)
- Marketing strategy: university-first, X, Reddit, Product Hunt
- Monetization: freemium + trial + B2B

### Session 8
- Data backend audited. Full FRED series matrix documented for 14 metrics x 9 countries from 2010. `docs/data-backend-spec.md` created.
- Launch tightrope resolved: Goldman-grade content, startup-grade infrastructure. 3-phase roadmap (launch free -> reliability -> paid scale). Most dangerous risk is never launching.
- App strategy: domain lockdown, competitive advantage (3-level system), daily habit (stories), legal structure, personal brand.
- **Home screen redesign:** flat weather map rejected ("boring"). 3D globe with weather-colored dots approved. Countries glow amber (sunny), sit muted grey (cloudy), or pulse dark purple (stormy). The globe IS the weather map.
- **Card redesign:** bottom sheet rejected. Floating card centered over globe with X close approved. 2-column metric grid, 6 macro + 8 market metrics (Sov CDS and FX Vol added).
- New prototype delivered: `macrosnaps-globe-weather.html`

---

## FILES

### In repo
```
macrosnaps-01/
  .gitignore, .env.example, CLAUDE.md, README.md
  glossary/ (6 JSON files - all enriched)
  backend/ (Flask API + fetchers + Claude service)
  frontend/macrosnaps-globe.html
  docs/handover-session7.md, setup-guide.md
```

### To add to repo
- `docs/commodities-spec.md`
- `docs/data-backend-spec.md`
- `data/commodities.json`
- `frontend/macrosnaps-globe-weather.html` (new prototype)
- This handover brief as `docs/handover-session8.md`

### Session 8 output files
- `macrosnaps-globe-weather.html` - new globe prototype with weather dots + floating card
- `data-backend-spec.md` - full production architecture spec with FRED series matrix
- `handover-session8.md` - this document
