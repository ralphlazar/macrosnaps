# MacroSnaps Data Backend - Production Architecture

## Current State (Honest Assessment)

### What exists
- Flask/PostgreSQL/SQLAlchemy stack
- 9 country fetcher/loader pairs
- FRED, Yahoo Finance, IMF WEO data sources
- Claude API story generation
- Google Sheets forecast loader

### What's broken or missing

**Metric coverage gap:** Frontend shows 14 metrics. Database tracks 8. The missing 6:
- Equity Vol (VIX for US, VSTOXX for Europe, etc.)
- Yield Curve (10Y - 2Y spread, derived)
- Corp Spread (ICE BofA indices)
- Sov CDS (needs specialist data source)
- FX Vol (derived from options or realized)
- Current Account (added via migration but incomplete)

**Country data gaps:**
- China: GDP growth, unemployment, 10Y bond yield not in FRED
- India: unemployment, 10Y bond yield not in FRED
- Japan: inflation not in FRED

**Architecture issues:**
- `days_back` parameter is fragile (should use fixed start date: 2010-01-01)
- WEO fetcher hardcoded to 2020-2024
- No retry logic on API failures
- Print statements instead of proper logging
- No data validation or quality checks
- No staleness detection (how do you know if data stopped updating?)
- No audit trail for when data was fetched or corrected
- Historical data only exists for 3/9 countries in the prototype

---

## Target Architecture

### Principles
1. **Every metric, every country, from 2010.** No gaps tolerated. If a primary source doesn't have it, find a secondary. If neither works, document why and show "not available" gracefully.
2. **Source hierarchy.** For each metric/country pair, define a primary and fallback source. If FRED is missing Japan inflation, use the Bank of Japan directly.
3. **Derived metrics are first-class.** Yield curve = 10Y minus 2Y. This calculation happens in the pipeline, not the frontend.
4. **Idempotent fetches.** Running the pipeline twice for the same date produces the same result. No duplicates, no overwrites unless the value changed.
5. **Observable.** Every fetch logged with timestamp, source, status, row count. Alerts on failure or staleness.

---

## Complete Metric x Source Matrix

### 14 Metrics x 9 Countries

For each cell: Primary Source | Fallback Source | Frequency | Start Date

#### MACRO METRICS (6)

**GDP Growth (% YoY, quarterly)**
| Country | Primary | Fallback | FRED Series | Notes |
|---------|---------|----------|-------------|-------|
| USA | FRED | BEA | A191RL1Q225SBEA | Quarterly, advance/second/third releases |
| CAN | FRED | StatCan | NAEXKP01CAQ189S | |
| GBR | FRED | ONS | NAEXKP01GBQ189S | |
| JPN | FRED | Cabinet Office | NAEXKP01JPQ189S | |
| DEU | FRED | Destatis | NAEXKP01DEQ189S | |
| FRA | FRED | INSEE | NAEXKP01FRQ189S | |
| ITA | FRED | ISTAT | NAEXKP01ITQ189S | |
| CHN | IMF WEO | NBS via CEIC | Not in FRED reliably | Annual only from WEO; quarterly from NBS |
| IND | FRED | MOSPI | NAEXKP01INQ189S | |

**Inflation (CPI % YoY, monthly)**
| Country | Primary | Fallback | FRED Series |
|---------|---------|----------|-------------|
| USA | FRED | BLS | CPIAUCSL (index, compute YoY) |
| CAN | FRED | StatCan | CPALTT01CAM661S |
| GBR | FRED | ONS | CPALTT01GBM659N |
| JPN | FRED | MIC | JPNCPIALLMINMEI |
| DEU | FRED | Destatis | CPALTT01DEM659N |
| FRA | FRED | INSEE | CPALTT01FRM659N |
| ITA | FRED | ISTAT | CPALTT01ITM659N |
| CHN | FRED | NBS | CHNCPIALLMINMEI |
| IND | FRED | MOSPI | INDCPIALLMINMEI |

**Unemployment (%, monthly)**
| Country | Primary | Fallback | FRED Series |
|---------|---------|----------|-------------|
| USA | FRED | BLS | UNRATE |
| CAN | FRED | StatCan | LRUNTTTTCAM156S |
| GBR | FRED | ONS | LRUNTTTTGBM156S |
| JPN | FRED | MIC | LRUNTTTTJPM156S |
| DEU | FRED | BA | LRUNTTTTDEM156S |
| FRA | FRED | INSEE | LRUNTTTTFRM156S |
| ITA | FRED | ISTAT | LRUNTTTITM156S |
| CHN | NBS | IMF WEO | Not in FRED | Surveyed urban unemployment; quarterly from NBS |
| IND | CMIE | IMF WEO | Not in FRED | CMIE monthly; FRED has LRUNTTTINM156S but patchy |

**Budget Deficit (% of GDP, annual)**
| Country | Primary | Fallback |
|---------|---------|----------|
| All 9 | IMF WEO | National statistics agencies |
CONCEPT_CODE: GGXCNL_NGDP. Extend to 2010.

**Current Account (% of GDP, quarterly)**
| Country | Primary | FRED Series |
|---------|---------|-------------|
| USA | FRED | USAB6BLTT02STSAQ |
| CAN | FRED | CANB6BLTT02STSAQ |
| GBR | FRED | GBRB6BLTT02STSAQ |
| JPN | FRED | JPNB6BLTT02STSAQ |
| DEU | FRED | DEUB6BLTT02STSAQ |
| FRA | FRED | FRAB6BLTT02STSAQ |
| ITA | FRED | ITAB6BLTT02STSAQ |
| CHN | FRED | CHNB6BLTT02STSAQ |
| IND | FRED | INDB6BLTT02STSAQ |

**Policy Rate (%, monthly or as-changed)**
| Country | Primary | FRED Series | Notes |
|---------|---------|-------------|-------|
| USA | FRED | FEDFUNDS | Fed funds effective rate |
| CAN | FRED | IRSTCB01CAM156N | BoC overnight rate |
| GBR | FRED | IRSTCB01GBM156N | BoE bank rate |
| JPN | FRED | IRSTCB01JPM156N | BoJ overnight call rate |
| DEU/FRA/ITA | FRED | IRSTCI01EZM156N | ECB main refinancing rate (shared) |
| CHN | FRED | IRSTCI01CNM156N | PBoC 1Y LPR |
| IND | FRED | IRSTCI01INM156N | RBI repo rate |

#### MARKET METRICS (8)

**Stock Market (index level, daily)**
| Country | Symbol | Name |
|---------|--------|------|
| USA | ^GSPC | S&P 500 |
| CAN | ^GSPTSE | S&P/TSX Composite |
| GBR | ^FTSE | FTSE 100 |
| JPN | ^N225 | Nikkei 225 |
| DEU | ^GDAXI | DAX |
| FRA | ^FCHI | CAC 40 |
| ITA | FTSEMIB.MI | FTSE MIB |
| CHN | 000001.SS | SSE Composite |
| IND | ^BSESN | BSE Sensex |
Source: Yahoo Finance. Compute YTD return as derived metric.

**Equity Vol (index, daily)**
| Country | Symbol/Source | Notes |
|---------|-------------|-------|
| USA | ^VIX | CBOE VIX |
| CAN | ^VIXC | S&P/TSX VIX (or use ^VIX as proxy) |
| GBR | ^VFTSE | FTSE 100 VIX (Yahoo: ^VFTSE or compute realized vol) |
| JPN | ^JNIV | Nikkei VI (or compute realized vol from ^N225) |
| DEU | ^V2TX or ^VSTOXX | VSTOXX (Euro Stoxx 50 vol) |
| FRA | ^V2TX | VSTOXX (same as DEU - Eurozone shared) |
| ITA | ^V2TX | VSTOXX (same as DEU - Eurozone shared) |
| CHN | Compute | 30-day realized vol from SSE Composite |
| IND | ^INDIAVIX | India VIX |
Fallback for all: compute 30-day realized vol from stock index.

**10Y Bond Yield (%, daily)**
| Country | Primary | FRED Series |
|---------|---------|-------------|
| USA | FRED | DGS10 |
| CAN | FRED | IRLTLT01CAM156N |
| GBR | FRED | IRLTLT01GBM156N |
| JPN | FRED | IRLTLT01JPM156N |
| DEU | FRED | IRLTLT01DEM156N |
| FRA | FRED | IRLTLT01FRM156N |
| ITA | FRED | IRLTLT01ITM156N |
| CHN | Investing.com or CEIC | Not reliably in FRED | China 10Y CGB |
| IND | FRED | IRLTLT01INM156N | Or RBI data |

**Yield Curve (bps, daily) - DERIVED**
Computation: 10Y yield minus 2Y yield.
Need 2Y series:
| Country | FRED 2Y Series |
|---------|---------------|
| USA | DGS2 |
| CAN | Compute from BoC data |
| GBR | Compute from DMO data |
| JPN | Compute from MoF data |
| DEU | Compute from Bundesbank data |
| FRA | Compute from AFT data |
| ITA | Compute from MEF data |
| CHN | CEIC |
| IND | RBI |
Fallback: 10Y minus 3M (FRED has T-bill rates for most).

**Corp Spread (bps, daily)**
| Country/Region | Source | Series |
|------|--------|--------|
| USA | FRED | BAMLC0A4CBBB (ICE BofA BBB spread) |
| EUR (DEU/FRA/ITA) | FRED | BAMLHE00EHYIEY (Euro HY) or compute from iBoxx |
| GBR | FRED | BAMLHE00EHYIEY or iBoxx GBP |
| JPN | FRED or BoJ | Japan corporate bond spreads |
| CAN | FRED | BAMLC0A4CBBB (use US as proxy or Canada-specific) |
| CHN | CEIC | China AA+ corp spread |
| IND | CEIC | India AAA corp spread |
Pragmatic approach: use US IG spread (BAMLC0A0CM2EY) for USA, Euro IG for Eurozone, and proxies where direct data unavailable.

**Sov CDS (bps, daily)**
This is the hardest metric to source freely. Options:
- WorldGovernmentBonds.com (scrape, fragile)
- FRED: no direct CDS series
- Bloomberg/Refinitiv (paid)
- Pragmatic: use sovereign bond spread vs Germany (for EUR) or vs US Treasuries (for non-EUR) as a proxy

Recommendation: For launch, use sovereign spread over UST/Bunds as the proxy. Label it "Sovereign Risk Spread" rather than "Sov CDS" if we can't get actual CDS data. Add real CDS data when revenue supports a Bloomberg terminal or Refinitiv feed.

**Exchange Rate (vs USD, daily)**
| Country | Yahoo Symbol | FRED Series |
|---------|-------------|-------------|
| USA | DX-Y.NYB | DTWEXBGS (DXY) |
| CAN | CADUSD=X | DEXCAUS |
| GBR | GBPUSD=X | DEXUSUK |
| JPN | JPYUSD=X | DEXJPUS |
| DEU/FRA/ITA | EURUSD=X | DEXUSEU |
| CHN | CNYUSD=X | DEXCHUS |
| IND | INRUSD=X | DEXINUS |

**FX Vol (%, daily)**
| Country | Source | Notes |
|---------|--------|-------|
| All | Compute | 30-day realized vol from daily FX returns |
Or use implied vol indices where available (CVIX for EUR, JYVIX for JPY, etc.)
Pragmatic: compute realized vol from FRED/Yahoo FX data. It's what most desks use as a sanity check anyway.

---

## Database Schema (Revised)

### Tables

```sql
-- Countries (unchanged, add commodities entity later)
CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    code VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    flag_emoji VARCHAR(10) NOT NULL,
    display_order INTEGER NOT NULL,
    entity_type VARCHAR(10) DEFAULT 'country',  -- 'country' or 'commodity'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Metrics (expand from 8 to 14 + commodity metrics)
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    frequency VARCHAR(10) NOT NULL,  -- 'daily', 'monthly', 'quarterly', 'annual'
    section VARCHAR(10) NOT NULL,    -- 'macro', 'market', 'commodity'
    display_order INTEGER NOT NULL,
    is_derived BOOLEAN DEFAULT FALSE,
    derivation_formula TEXT,         -- e.g. 'yield_10y - yield_2y'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data sources (new table - tracks where each series comes from)
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    metric_id INTEGER REFERENCES metrics(id),
    source_name VARCHAR(30) NOT NULL,   -- 'FRED', 'Yahoo', 'IMF_WEO', 'computed'
    source_series VARCHAR(50),          -- 'DGS10', '^GSPC', etc.
    priority INTEGER DEFAULT 1,         -- 1 = primary, 2 = fallback
    start_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    UNIQUE(country_id, metric_id, priority)
);

-- Time series (expanded from daily_data)
CREATE TABLE time_series (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    metric_id INTEGER NOT NULL REFERENCES metrics(id),
    date DATE NOT NULL,
    value FLOAT,
    source_id INTEGER REFERENCES data_sources(id),
    fetched_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(country_id, metric_id, date)
);

-- Create index for fast lookups
CREATE INDEX idx_ts_country_metric_date ON time_series(country_id, metric_id, date);
CREATE INDEX idx_ts_date ON time_series(date);

-- Fetch log (new - audit trail)
CREATE TABLE fetch_log (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(30) NOT NULL,
    country_code VARCHAR(5),
    metric_code VARCHAR(30),
    status VARCHAR(10) NOT NULL,    -- 'success', 'error', 'empty', 'stale'
    rows_fetched INTEGER DEFAULT 0,
    error_message TEXT,
    duration_ms INTEGER,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Cards (unchanged)
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    date DATE NOT NULL,
    headline_beginner VARCHAR(200),
    headline_moderate VARCHAR(200),
    headline_expert VARCHAR(200),
    story_beginner TEXT,
    story_moderate TEXT,
    story_expert TEXT,
    weather_icon VARCHAR(20),
    ai_generated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(country_id, date)
);
```

### 14 Metrics to Seed

```python
METRICS = [
    # Macro (6)
    {'code': 'gdp_growth', 'name': 'GDP Growth', 'unit': '%', 'frequency': 'quarterly', 'section': 'macro', 'display_order': 1},
    {'code': 'inflation', 'name': 'Inflation (CPI)', 'unit': '%', 'frequency': 'monthly', 'section': 'macro', 'display_order': 2},
    {'code': 'unemployment', 'name': 'Unemployment', 'unit': '%', 'frequency': 'monthly', 'section': 'macro', 'display_order': 3},
    {'code': 'budget_deficit', 'name': 'Budget Deficit', 'unit': '% GDP', 'frequency': 'annual', 'section': 'macro', 'display_order': 4},
    {'code': 'current_account', 'name': 'Current Account', 'unit': '% GDP', 'frequency': 'quarterly', 'section': 'macro', 'display_order': 5},
    {'code': 'policy_rate', 'name': 'Policy Rate', 'unit': '%', 'frequency': 'monthly', 'section': 'macro', 'display_order': 6},
    # Market (8)
    {'code': 'stock_market', 'name': 'Stock Market YTD', 'unit': '%', 'frequency': 'daily', 'section': 'market', 'display_order': 7},
    {'code': 'equity_vol', 'name': 'Equity Vol', 'unit': 'index', 'frequency': 'daily', 'section': 'market', 'display_order': 8},
    {'code': 'bond_yield_10y', 'name': '10Y Bond Yield', 'unit': '%', 'frequency': 'daily', 'section': 'market', 'display_order': 9},
    {'code': 'yield_curve', 'name': 'Yield Curve', 'unit': 'bps', 'frequency': 'daily', 'section': 'market', 'display_order': 10, 'is_derived': True, 'derivation': 'bond_yield_10y - bond_yield_2y'},
    {'code': 'corp_spread', 'name': 'Corp Spread', 'unit': 'bps', 'frequency': 'daily', 'section': 'market', 'display_order': 11},
    {'code': 'sov_spread', 'name': 'Sov CDS', 'unit': 'bps', 'frequency': 'daily', 'section': 'market', 'display_order': 12},
    {'code': 'exchange_rate', 'name': 'Exchange Rate', 'unit': 'rate', 'frequency': 'daily', 'section': 'market', 'display_order': 13},
    {'code': 'fx_vol', 'name': 'FX Vol', 'unit': '%', 'frequency': 'daily', 'section': 'market', 'display_order': 14, 'is_derived': True, 'derivation': '30d realized vol of exchange_rate'},
]
```

---

## Pipeline Architecture

### Daily Pipeline (runs at 06:00 UTC)

```
1. FETCH       Fetch raw data from all sources (FRED, Yahoo, WEO)
2. VALIDATE    Check for missing values, outliers, stale data
3. DERIVE      Compute yield curve, FX vol, equity vol where needed
4. STORE       Upsert into time_series table
5. GENERATE    Run Claude API to generate stories from latest data
6. LOG         Write fetch_log entries for monitoring
7. ALERT       Flag any failures or anomalies
```

### Historical Backfill (run once)

```
For each country x metric:
  1. Identify source from data_sources table
  2. Fetch full history from 2010-01-01 to today
  3. Validate and clean (handle missing, duplicates)
  4. Bulk insert into time_series
  5. Log result
```

### Fetcher Design

Replace the current per-country fetcher/loader pair with a unified fetcher that reads from the `data_sources` table:

```python
class UnifiedFetcher:
    """Fetches data for any country/metric pair using configured sources."""
    
    def fetch(self, country_code, metric_code, start_date, end_date):
        source = self.get_source(country_code, metric_code)
        if source.source_name == 'FRED':
            return self.fetch_fred(source.source_series, start_date, end_date)
        elif source.source_name == 'Yahoo':
            return self.fetch_yahoo(source.source_series, start_date, end_date)
        elif source.source_name == 'IMF_WEO':
            return self.fetch_weo(country_code, source.source_series, start_date, end_date)
        elif source.source_name == 'computed':
            return self.compute_derived(country_code, metric_code, start_date, end_date)
```

This eliminates the 18 separate fetcher/loader files (9 countries x 2 files each) and replaces them with one configurable system.

---

## API Endpoints (Revised)

```
GET  /api/countries                       List all countries
GET  /api/countries/{code}                Country detail + latest metrics
GET  /api/countries/{code}/metrics        All 14 metrics with latest values
GET  /api/countries/{code}/history/{metric}?start=2010-01-01&end=2026-02-10
                                          Time series for charts
GET  /api/compare/{metric}                All 9 countries ranked by metric
GET  /api/cards?level=beginner            Daily cards with stories
GET  /api/commodities                     All 8 commodities with latest data
GET  /api/commodities/{symbol}/history    Commodity price history
GET  /api/health                          Pipeline health / data freshness
```

---

## Data Quality Rules

```python
QUALITY_RULES = {
    'gdp_growth': {'min': -25, 'max': 25, 'max_stale_days': 120},
    'inflation': {'min': -10, 'max': 50, 'max_stale_days': 45},
    'unemployment': {'min': 0, 'max': 30, 'max_stale_days': 45},
    'policy_rate': {'min': -2, 'max': 30, 'max_stale_days': 45},
    'bond_yield_10y': {'min': -2, 'max': 20, 'max_stale_days': 3},
    'stock_market': {'min': 0, 'max': 999999, 'max_stale_days': 3},
    'exchange_rate': {'min': 0, 'max': 99999, 'max_stale_days': 3},
    # etc.
}
```

Any value outside min/max gets flagged. Any series stale beyond max_stale_days triggers an alert.

---

## What to Build First (Priority Order)

### Phase 1: Data Foundation
1. New database schema (migrate from current)
2. Seed `data_sources` table with the full metric x source matrix above
3. Build `UnifiedFetcher` with FRED, Yahoo, WEO adapters
4. Historical backfill script: all 14 metrics x 9 countries from 2010
5. Validation and logging

### Phase 2: Derived Metrics
6. Yield curve computation (10Y - 2Y)
7. FX vol computation (30d realized)
8. Equity vol (realized where implied unavailable)
9. Stock market YTD computation

### Phase 3: API Layer
10. New REST endpoints serving historical data
11. Chart data endpoint (formatted for Chart.js)
12. Compare endpoint (ranked data for bar charts)

### Phase 4: Daily Pipeline
13. Scheduled daily fetch (cron or Celery)
14. Story generation integration
15. Health monitoring endpoint

### Phase 5: Commodities
16. Add 8 commodities to countries table (entity_type = 'commodity')
17. Commodity-specific fetchers (Yahoo Finance for most)
18. Futures curve data (contango/backwardation)

---

## Hard Truths

**Sov CDS:** Free, reliable CDS data doesn't exist. Bloomberg Terminal ($24k/year) or Refinitiv Eikon ($22k/year) are the real sources. For launch, use sovereign spread over benchmark (UST for non-EUR, Bunds for EUR). Relabel accordingly. Add real CDS when revenue supports a data terminal.

**China data:** GDP growth and unemployment are politically managed numbers. FRED doesn't carry them reliably. NBS publishes quarterly GDP; CMIE publishes better unemployment data for India. Both require scraping or a CEIC subscription ($5-10k/year). For launch, use IMF WEO annual estimates and flag them as lower frequency.

**Corp spreads outside the US:** ICE BofA indices (via FRED) are the gold standard for US and European IG/HY. For Japan, China, India - proxies are the pragmatic choice.

**Yahoo Finance reliability:** yfinance is an unofficial scraper, not an API. It can break without warning. For production, consider a paid market data provider (Polygon.io at $99/month covers US equities and FX; IEX Cloud covers international).

---

## Cost Estimate for Data

| Source | Cost | Covers |
|--------|------|--------|
| FRED API | Free | US + international macro (80% of what you need) |
| Yahoo Finance (yfinance) | Free but fragile | Stock indices, FX, commodities |
| IMF WEO | Free | Budget deficits, annual macro |
| Google Sheets forecasts | Free | Your proprietary 2026 forecasts |
| Polygon.io | $99/month | Reliable stock/FX data (replaces Yahoo) |
| CEIC (China/India data) | $5-10k/year | Fills the China/India gaps |
| Bloomberg/Refinitiv | $22-24k/year | Sov CDS, corp spreads, everything |

**Recommendation for launch:** FRED + Yahoo + IMF (all free). Accept the gaps in sov CDS (use spread proxy) and China/India (use WEO annual). Budget $99/month for Polygon.io once you have paying users. Bloomberg/CEIC when B2B revenue justifies it.
