# MacroSnaps: Data and Stories Audit
*Last revised March 12, 2026. Reflects commodity price automation (fetch_market_data.py) and commodity story automation (update_commodity_stories.py) completed March 12, 2026.*

---

## Part 1: Data Series

### 1A. Macro Metrics (6 per country)

These are annual consensus forecasts. Source of truth is Ralph's Google Sheet. Written into `data.json` by `sync_sheet.py`. Updated infrequently, only when consensus forecasts change. Tier: **structural** (GDP Growth, Budget Deficit, Current Account) or **weekly** (Inflation, Unemployment, Policy Rate).

| Metric | Update frequency | Source | Script | Notes |
|---|---|---|---|---|
| GDP Growth | Structural (rarely) | Google Sheet | sync_sheet.py | Year-end 2026 consensus forecast |
| Inflation (CPI) | Weekly | Google Sheet | sync_sheet.py | Year-end 2026 consensus forecast |
| Unemployment | Weekly | Google Sheet | sync_sheet.py | Year-end 2026 consensus forecast |
| Budget Deficit | Structural (rarely) | Google Sheet | sync_sheet.py | Year-end 2026 consensus forecast. Historical arrays empty for 9 of 12 countries. |
| Current Account | Structural (rarely) | Google Sheet | sync_sheet.py | % of GDP (converted March 10, 2026 using IMF WEO denominators). Historical arrays complete. |
| Policy Rate | Weekly | Google Sheet | sync_sheet.py | Year-end 2026 forecast, not current rate |

**Current values by country:**

| Country | GDP Growth | Inflation | Unemployment | Budget Deficit | Current Account | Policy Rate |
|---|---|---|---|---|---|---|
| USA | +2.2% | 2.3% | 4.2% | -7.5% GDP | -3.8% GDP | 3.25% |
| CAN | +1.7% | 2% | 6.5% | -1.5% GDP | -0.5% GDP | 2.25% |
| GBR | +1.5% | 2.1% | 5.0% | -4.2% GDP | -2.5% GDP | 3.5% |
| JPN | +0.8% | 1.8% | 2.5% | -1.2% GDP | +4.8% GDP | 1.25% |
| DEU | +1.2% | 2.2% | 3.8% | -2% GDP | +4.5% GDP | 2.50% |
| FRA | +1.4% | 2% | 7.7% | -4.8% GDP | +1% GDP | 2.50% |
| ITA | +1% | 2.3% | 5.6% | -3.2% GDP | +0.8% GDP | 2.50% |
| CHN | +4.7% | 2% | 5.1% | -6.8% GDP | +2.5% GDP | 2.75% |
| IND | +6.3% | 4.2% | 4.7% | -7.2% GDP | -1.2% GDP | 6% |
| ZAF | +1.5% | 3.5% | 32.5% | -4.8% GDP | -1.4% GDP | 6.25% |
| BRA | +1.7% | 4.2% | 5.7% | -0.8% GDP | -2.6% GDP | 12% |
| RUS | +0.9% | 4.7% | 2.5% | -2.5% GDP | +2% GDP | 12% |

---

### 1B. Market Metrics (8 per country)

Fetched daily by `fetch_market_data.py` from Yahoo Finance and FRED. Tier: **daily**.

| Metric | Source | Fetch method | Notes |
|---|---|---|---|
| Stock Market YTD | Yahoo Finance | YTD % change from Jan 1 close | Fails for RUS (IMOEX.ME delisted) |
| Equity Vol | Yahoo Finance | Implied vol index; 30-day realized vol as fallback | Data-void: displayed as "not available" |
| 10Y Bond Yield | FRED | Daily series per country | Fails for CHN and BRA (no FRED series) |
| Yield Curve | FRED (derived) | 10Y minus short rate | Fails for CHN and BRA; fixed for USA/DEU/FRA/JPN in March 2026 |
| Corp Spread | FRED | ICE BofA IG/HY OAS series | Data-void: displayed as "not available". No RUS series configured. |
| Sov CDS | Derived proxy | Local 10Y minus UST (EM only) | Data-void: displayed as "not available" |
| FX pair | Yahoo Finance | Varies by country (see table below) | Succeeds for all countries |
| FX Vol | Yahoo Finance (derived) | 30-day realized vol from daily FX returns | Data-void: displayed as "not available" |

**FX pairs by country:**

| Country | Pair | Current value | Last updated |
|---|---|---|---|
| USA | USD/DXY | 99.2 | 2026-03-11 |
| CAN | CAD/USD | 0.74 | 2026-03-11 |
| GBR | GBP/USD | 1.34 | 2026-03-11 |
| JPN | USD/JPY | 158.8 | 2026-03-11 |
| DEU | EUR/USD | 1.1575 | 2026-03-11 |
| FRA | EUR/USD | 1.1575 | 2026-03-11 |
| ITA | EUR/USD | 1.1575 | 2026-03-11 |
| CHN | USD/CNY | 6.86 | 2026-03-11 |
| IND | USD/INR | 92.15 | 2026-03-11 |
| ZAF | USD/ZAR | 16.40 | 2026-03-11 |
| BRA | USD/BRL | 5.15 | 2026-03-11 |
| RUS | USD/RUB | 79.1 | 2026-03-11 |

**Current market metric values by country:**

| Country | Stock YTD | Equity Vol | 10Y Yield | Yield Curve | Corp Spread | Sov CDS | FX Vol |
|---|---|---|---|---|---|---|---|
| USA | -1.4% | ~25 | 4.12% | +52bps | 84bps | 42bps | 5.8% |
| CAN | +3.7% | ~20 | 3.40% | +121bps | 84bps | 45bps | 5.8% |
| GBR | +4.0% | ~15 | 4.45% | +74bps | 84bps | 32bps | 6.8% |
| JPN | +6.2% | ~32 | 2.24% | +112bps | 84bps | 28bps | 8.5% |
| DEU | -3.6% | ~20 | 2.81% | +81bps | 84bps | 20bps | 6.3% |
| FRA | -2.0% | ~16 | 3.53% | +153bps | 84bps | 38bps | 6.3% |
| ITA | -1.3% | ~22 | 3.49% | +149bps | 84bps | 70bps | 6.3% |
| CHN | +2.7% | ~13 | 2.40% | +35bps | 162bps | 72bps | 3.2% |
| IND | -9.8% | ~21 | 6.73% | +123bps | 162bps | 261bps | 7.2% |
| ZAF | +1.1% | ~29 | 8.62% | +187bps | 162bps | 450bps | 17.2% |
| BRA | +14.8% | ~22 | 13.80% | -140bps | 162bps | 180bps | 10.5% |
| RUS | +5.0% | ~32 | 13.5% | -140bps | 380bps | 320bps | 15.0% |

**Known permanent data gaps (not bugs):**
- RUS: Stock Market YTD and Equity Vol always fail (IMOEX.ME delisted on Yahoo)
- CHN and BRA: 10Y Bond Yield, Yield Curve, and Sov CDS always fail (no FRED series)
- RUS: Corp Spread not configured
- Equity Vol, Corp Spread, Sov CDS, FX Vol: all four are data-void metrics with no reliable free daily source. All displayed as "not available" in UI.

---

### 1C. Historical Chart Data (`_frozen_historical`)

Populated by `refetch_historical.py` from FRED and Yahoo Finance. Updated manually, not daily. Never touch by hand.

Each metric has 7 data points: actuals for 2020-2025, plus the 2026F forecast as the final point.

**Population status by country:**

| Country | Charts populated | Known gaps |
|---|---|---|
| USA | 14/14 | None |
| CAN | 14/14 | Budget Deficit array empty |
| GBR | 14/14 | Budget Deficit array empty |
| JPN | 14/14 | None |
| DEU | 14/14 | Budget Deficit array empty |
| FRA | 14/14 | Budget Deficit array empty |
| ITA | 14/14 | None |
| CHN | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source. Budget Deficit array empty. |
| IND | 11/14 | Unemployment, 10Y Bond Yield, Yield Curve: no free source. Budget Deficit array empty. |
| ZAF | 12/14 | Unemployment: no monthly source. Budget Deficit array empty. |
| BRA | 12/14 | 10Y Bond Yield, Yield Curve: no free source. Budget Deficit array empty. |
| RUS | 10/14 | GDP Growth, Unemployment, historical data discontinued post-2022 sanctions. Budget Deficit array empty. |

**Known data quality flags:**
- IND 2025 GDP Growth (16.77) and ZAF 2025 GDP Growth (6.76) appear to reflect nominal USD growth from FRED rather than real % growth. Pending investigation.
- Budget Deficit historical arrays are intentionally empty for 9 countries (CAN, GBR, DEU, FRA, CHN, IND, ZAF, BRA, RUS). A single forecast point with no history would be meaningless as a chart.
- Running `refetch_historical.py` overwrites Current Account arrays with raw dollar values, undoing the % of GDP conversion. Must re-apply the CA conversion after any refetch run.

---

### 1D. Commodities (9 items)

Source: CME, ICE, COMEX, CBOT, Yahoo Finance. Updated manually as part of daily content session. Tier: **daily** for price and spark array.

Each commodity has: `price`, `change` (YoY % from Yahoo Finance), `spark` (rolling 12-point array), `annual` (long-run annual price history), `storyWrittenAtPrice` (price at time of last story write, used for drift detection), and `storyUpdatedDate`.

| Commodity | Symbol | Category | Unit | Current price | Last updated |
|---|---|---|---|---|---|
| WTI Crude | CL | Energy | $/bbl | 94.19 | Mar 12, 2026 |
| Brent Crude | BZ | Energy | $/bbl | 95.30 | Mar 12, 2026 |
| Natural Gas | NG | Energy | $/mmBtu | 3.23 | Mar 12, 2026 |
| Gold | GC | Metals | $/oz | 5,185 | Mar 12, 2026 |
| Silver | SI | Metals | $/oz | 87.23 | Mar 12, 2026 |
| Copper | HG | Metals | $/lb | 5.87 | Mar 12, 2026 |
| Wheat | ZW | Agriculture | cents/bu | 604 | Mar 12, 2026 |
| Corn | ZC | Agriculture | cents/bu | 465.75 | Mar 12, 2026 |
| Soybeans | ZS | Agriculture | cents/bu | 1,229 | Mar 12, 2026 |

**How commodity data is updated:** `fetch_market_data.py` pulls price, YoY change, spark array, and `asOf` for all 9 commodities daily via Yahoo Finance continuous futures tickers (CL=F, BZ=F, NG=F, GC=F, SI=F, HG=F, ZW=F, ZC=F, ZS=F). No manual edits needed. The `annual` array is long-run history and updated rarely.

---

## Part 2: Stories and Headlines

### 2A. Per-Metric Stories (168 total)

12 countries x 14 metrics x 3 audience levels (beginner, moderate, expert) = 168 story blocks.

Each story lives inside its metric entry in `data.json` as a `story` object. Stories appear in the metric tooltip between the value and the chart.

**How they are created:** `update_stories.py` diffs `data.json` against the last git commit, identifies metrics that moved past a configurable threshold, calls the Claude API (claude-sonnet-4-20250514), and rewrites affected stories at all three levels in one pass.

**When to run:** After every `sync_sheet.py --apply` and every `fetch_market_data.py` run. Part of the daily bash ritual (Step 5).

**Stories for the 4 data-void metrics** (Equity Vol, Corp Spread, Sov CDS, FX Vol) are not maintained going forward as those metrics display as "not available."

**Completion status:** All 168 stories are complete as of March 11, 2026.

**Story length targets:**
- Beginner: 2-3 sentences. No jargon. Plain English explanation of what the number means for everyday life.
- Moderate: 3-4 sentences. One piece of context (historical comparison, regional comparison, or causal driver).
- Expert: 4-5 sentences. Specific numbers, a directional signal, one forward-looking implication.

**Known value/story drift (as of March 12, 2026):**

The following metrics have live values that have moved since their stories were last written. These need a story rewrite session.

| Country | Metric | Current value | Story references |
|---|---|---|---|
| USA | Stock Market YTD | -1.4% | ~+2% |
| USA | Equity Vol (VIX) | ~25 | ~16 |
| USA | 10Y Bond Yield | 4.12% | 4.28% |
| USA | Yield Curve | +52bps | +8bps |
| USA | USD/DXY | 99.2 | 104.2 |
| USA | FX Vol | 5.8% | 8.5% |
| CAN | Stock Market YTD | +3.7% | 6.8% |
| CAN | 10Y Bond Yield | 3.40% | (check story) |
| CAN | Yield Curve | +121bps | +30bps |
| CAN | CAD/USD | 0.74 | (check story) |
| CAN | FX Vol | 5.2% | 7.2% |
| GBR | Stock Market YTD | +4.0% | (check story) |
| GBR | 10Y Bond Yield | 4.45% | (check story) |
| GBR | Yield Curve | +74bps | (check story) |
| GBR | GBP/USD | 1.34 | (check story) |
| JPN | Equity Vol | ~32 | (check story) |
| JPN | 10Y Bond Yield | 2.24% | (check story) |
| JPN | Yield Curve | +112bps | (check story) |
| JPN | USD/JPY | 158.8 | (check story) |
| DEU | Stock Market YTD | -3.6% | (check story) |
| DEU | 10Y Bond Yield | 2.81% | (check story) |
| DEU | Yield Curve | +81bps | (check story) |
| DEU | EUR/USD | 1.1575 | (check story) |
| FRA | Stock Market YTD | -2.0% | (check story) |
| FRA | 10Y Bond Yield | 3.53% | (check story) |
| FRA | Yield Curve | +153bps | (check story) |
| ITA | Stock Market YTD | -1.3% | (check story) |
| ITA | 10Y Bond Yield | 3.49% | (check story) |
| ITA | Yield Curve | +149bps | (check story) |
| CHN | Stock Market YTD | +2.7% | (check story) |
| CHN | USD/CNY | 6.86 | (check story) |
| IND | Stock Market YTD | -9.8% | (check story) |
| IND | 10Y Bond Yield | 6.73% | (check story) |
| IND | Yield Curve | +123bps | (check story) |
| IND | Sov CDS | 261bps | (check story) |
| IND | USD/INR | 92.15 | (check story) |
| ZAF | Stock Market YTD | +1.1% | (check story) |
| ZAF | Equity Vol | ~29 | (check story) |
| ZAF | 10Y Bond Yield | 8.62% | (check story) |
| ZAF | Yield Curve | +187bps | (check story) |
| ZAF | Sov CDS | 450bps | (check story) |
| ZAF | USD/ZAR | 16.40 | (check story) |
| BRA | Stock Market YTD | +14.8% | (check story) |
| BRA | USD/BRL | 5.15 | (check story) |
| RUS | USD/RUB | 79.1 | (check story) |

---

### 2B. Country-Level Headline Stories (12 countries)

Each country has a `stories` block with 3 bullet points per level (beginner, moderate, expert). These are the top-of-card narrative bullets visible on each country panel.

**How they are created:** `update_headlines.py` runs a two-phase pipeline:
1. Phase 1: A single Sonnet + web search "harvest" call pulls recent macro data for all 12 countries (capped at 2 search turns, 1500 max tokens).
2. Phase 2: 3 Haiku batches (4 countries each) write story bullets with recent data leading and forecast values as background context only.

The script writes a draft to `stories_draft_YYYY-MM-DD.json`. Review is done in `headline_review.html` (browser tool). After approval, apply with `python3 update_headlines.py --apply stories_approved_YYYY-MM-DD.json`.

**Update frequency:** Daily, as part of the daily bash ritual (Step 6).

**Current status:** All 12 countries complete. Last full run: March 12, 2026 (first successful run with two-phase architecture, 13/13 calls successful).

**Story format per country:** 3 bullets at each of 3 levels (9 blocks per country, 108 blocks total).

---

### 2C. Global Stories (3 slots)

Three top-of-page story cards that frame the global macro picture for the day. Each slot has 3 levels (beginner, moderate, expert) totaling 9 text blocks.

**Three-act structure (fixed):**
- Slot 1 (Today's Story): dominant macro event of the day
- Slot 2 (Biggest Movers): which markets, currencies, or economies are reacting and how
- Slot 3 (The Connection): what ties slots 1 and 2 together, the "so what" for the global picture

**How they are created:** Same `update_headlines.py` pipeline. Global runs first (before country stories) to avoid Sonnet rate limit exhaustion from the harvest call. Uses Sonnet + web search, 5000 max tokens.

**Update frequency:** Daily.

**Current global stories (as of March 12, 2026):**
- Slot 1: Iran Crisis Shuts Key Oil Route
- Slot 2: (Biggest Movers)
- Slot 3: (The Connection)

---

### 2D. Commodity Stories (9 commodities)

Each commodity has a `story` object with `beginner`, `moderate`, and `expert` keys (each as a `{"text": "..."}` object). These describe the commodity market context and outlook.

**How they are created:** `update_commodity_stories.py` runs daily as part of the bash ritual (Step 5, immediately after `fetch_market_data.py`). It compares each commodity's current `price` against `storyWrittenAtPrice` stored in `data.json`. Any commodity that has moved past its threshold gets new stories written at all three levels via a single Haiku API call. Changes are applied directly to `data.json` with no review step.

**Thresholds:**
- Natural Gas: 10%
- All other commodities: 5%

**Update frequency:** Daily (automated). On quiet days the script exits in under a second with no API call made.

**Last bootstrapped:** March 12, 2026. All 9 `storyWrittenAtPrice` values set.

**Story length targets:**
- Beginner: 2-3 sentences. What this commodity is and why its price matters to ordinary people.
- Moderate: 3-4 sentences. One driver of the current price level and one downstream effect.
- Expert: 4-5 sentences. Specific price, directional trend, supply/demand driver, one forward implication.

---

### 2E. metricBriefs (short summaries)

Each country has a `metricBriefs` object with a short explanatory sentence for each of its 14 metrics. These appear in the tooltip as a plain-English "what is this metric" blurb.

**Update frequency:** Rarely. These are definitional and do not change with data.

**Status:** Complete for all 12 countries.

---

### 2F. fxRegime Descriptions

Each country has a `fxRegime` object describing its foreign exchange policy at three levels (beginner, moderate, expert).

**Update frequency:** Rarely. Structural information that only changes if a country changes its FX policy regime.

**Status:** Complete for all 12 countries.

---

## Part 3: Summary - How Everything Fits Together

| Data / content type | Source | Update script | Frequency |
|---|---|---|---|
| Macro metrics (GDP, CPI, Unemployment, Budget, CA, Policy Rate) | Google Sheet | sync_sheet.py | When consensus forecasts change (infrequent) |
| Market metrics (Stock YTD, 10Y Yield, Yield Curve, FX pair) | Yahoo Finance / FRED | fetch_market_data.py | Daily |
| Data-void metrics (Equity Vol, Corp Spread, Sov CDS, FX Vol) | No free source | N/A | Displayed as "not available" |
| Historical chart arrays | FRED / Yahoo Finance | refetch_historical.py | Manually, when needed |
| Commodity prices | Yahoo Finance (continuous futures) | fetch_market_data.py | Daily (automated) |
| Per-metric stories (168 blocks) | Claude API (Sonnet) | update_stories.py | After each data fetch, for metrics that moved past threshold |
| Country headline stories (108 blocks) | Claude API (Haiku + harvest) | update_headlines.py | Daily |
| Global stories (9 blocks) | Claude API (Sonnet + web search) | update_headlines.py | Daily |
| Commodity stories (27 blocks) | Claude API (Haiku) | update_commodity_stories.py | Daily (automated, threshold-gated) |
| metricBriefs | Manual (written once) | None | Rarely |
| fxRegime descriptions | Manual (written once) | None | Rarely |
