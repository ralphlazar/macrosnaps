# MacroSnaps — Handover Brief (v6, March 8 2026)

**Live URL:** https://macrosnaps-01.onrender.com/macrosnaps-globe.html
**Repo:** https://github.com/ralphlazar/macrosnaps-01.git
**Local path:** `/Users/lisaswerling/Downloads/macrosnaps-repo/`
**Hosting:** Render (static site, auto-deploys from `main` branch)

---

## WHAT YOU NEED TO DO FIRST (Carry-over from March 7)

Stories were written on March 7 but the injection script and data refresh were NOT yet run. Do this before anything else:

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo

# Step 1 — Inject today's stories into the HTML
mv ~/Downloads/update_stories_2026-03-07.py .
python3 update_stories_2026-03-07.py

# Step 2 — Run data refresh
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Step 3 — Copy snapshot to frontend
cp snapshot.json frontend/snapshot.json

# Step 4 — Commit and push everything
git add frontend/macrosnaps-globe.html
git commit -m "Story refresh — March 7, 2026"
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — Mar 7"
git push origin main
```

Then hard-refresh the live site: **Cmd+Shift+R** (or open in incognito).

---

## 1. WHAT IS MACROSNAPS

An interactive 3D globe dashboard (Three.js) showing macro/market data for 12 countries and 9 commodities. Users click a country dot → a card slides in with metrics, stories at 3 expertise levels (beginner/moderate/expert), and glossary popover definitions.

**Scope (as of March 7, 2026):**
- 12 countries: USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS
- 9 commodities: WTI Crude, Brent Crude, Natural Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans
- ~192 glossary terms across 7 categories
- 3 expertise levels throughout
- Weather emoji system: ☀️ ⛅ ☁️ ⛈️

---

## 2. FILE ARCHITECTURE

```
macrosnaps-repo/
├── frontend/
│   ├── macrosnaps-globe.html    ← THE monolith (~14,000+ lines). All CSS, HTML, JS, data.
│   └── snapshot.json            ← Daily data output from backend
├── backend/
│   └── build_snapshot.py        ← Data fetcher (~1,860 lines). Runs daily.
├── .env                         ← FRED_API_KEY=xxx (not committed)
├── snapshot.json                ← Copy at repo root (backend writes here first)
└── .gitignore
```

**Two data sources feed the frontend:**

1. **snapshot.json** — Live numeric data refreshed daily by `build_snapshot.py`. Metrics, commodity prices, weather emojis, historical series. Loaded at runtime.
2. **Inline JSON in HTML** — Stories, Metric Briefs, glossary, fxRegime, fallback metrics. Embedded in `<script type="application/json">` blocks. Static — only change via Python injection scripts.

---

## 3. DAILY WORKFLOW

**The goal for every trading day is minimum work, maximum freshness: run both Part 1 (data) and Part 2 (stories) every day.** Do not skip stories. The only things that do NOT change daily are Ralph's forecast sheet values and the historical data arrays — everything else should be refreshed.

### PART 1 — DATA REFRESH (every trading day, ~10 min)

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo

# Fetch fresh data
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Copy to frontend and push
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main
```

**Expected output:**
```
Metrics: 168 total | ~115 live | ~46 fallback | ~7 missing
  🇺🇸 USA: ☀️  14/14 metrics live
  🇨🇦 CAN: ☁️  14/14 metrics live
  🇬🇧 GBR: ☁️  14/14 metrics live
  🇯🇵 JPN: ☀️  14/14 metrics live
  🇩🇪 DEU: ☀️  14/14 metrics live
  🇫🇷 FRA: ⛈️  14/14 metrics live
  🇮🇹 ITA: ☁️  14/14 metrics live
  🇨🇳 CHN: ☁️  14/14 metrics live
  🇮🇳 IND: ☁️  14/14 metrics live
  🇿🇦 ZAF: ☀️  14/14 metrics live
  🇧🇷 BRA: ☁️  14/14 metrics live
  🇷🇺 RUS: ☁️  ~12/14 metrics live (rest fallback — sanctions)
  🛢️ COMM: ☁️  9/9 commodities live
```

### PART 2 — STORY REFRESH (every trading day)

Stories and Metric Briefs must be refreshed daily alongside the data. Do not leave stories stale from a previous day. The injection script updates: country stories, weather emojis, global stories, commodity stories, commodity prices, and Metric Briefs.

**What to update daily:**
- All country stories (3 bullets × 3 levels × 12 countries)
- All global stories (3 × 3)
- All commodity stories (3 × 3) and commodity prices/sparklines
- Weather emojis for all countries and commodities
- Metric Briefs (1 sentence × 3 levels × 6 metrics × 12 countries) — once frontend is implemented

**What NOT to update daily:**
- Ralph's forecast sheet values (GDP_Growth_2026, Inflation_2026, etc.) — only change when Ralph updates the sheet
- Historical data arrays (`historical`, `weatherGrid`) — only update these when doing a periodic structural refresh

**Step 1:** Start a new Claude conversation. Upload:
1. This handover doc
2. `macrosnaps-globe.html` (latest version from `frontend/`)

**Step 2:** Ask Claude to write the stories using this prompt:

```
I need a MacroSnaps story refresh for today [DATE].

Please:
1. Research current macro/market news for all 12 countries (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS) + global themes + commodities
2. Write 3 bullets × 3 expertise levels (beginner, moderate, expert) for each country = 108 country bullets
3. Write 3 × 3 global story bullets (with icon/label/body/source format) = 9 global bullets
4. Write 3 × 3 commodity story bullets = 9 commodity bullets
5. Write Metric Brief entries: 1 sentence × 3 expertise levels × 6 macro metrics × 12 countries = 216 sentences
6. Build a Python injection script (update_stories_[DATE].py) that patches all stories + Metric Briefs into frontend/macrosnaps-globe.html

Totals:
- Headline stories: 126 bullets (12 countries × 9 + 9 global + 9 commodity)
- Metric Briefs: 216 sentences (12 countries × 6 metrics × 3 levels)
- Grand total: 342 content items

The injection script should:
- Parse <script id="countries-data"> and <script id="app-config"> JSON blocks
- Replace stories for all 12 countries (including RUS)
- Replace metricBriefs for all 12 countries
- Replace globalStories and commodities.stories
- Run from the repo root: python3 update_stories_[DATE].py

Country stories format: {"beginner": ["...", "...", "..."], "moderate": [...], "expert": [...]}
Global stories format: {"beginner": [{"icon": "🔥", "label": "...", "body": "...", "source": "..."}, ...], ...}
Commodity stories format: same as country stories (simple string arrays)

Metric Briefs format (1 sentence per level, 6 macro metrics only):
{
  "GDP Growth": {"beginner": "...", "moderate": "...", "expert": "..."},
  "Inflation (CPI)": {"beginner": "...", "moderate": "...", "expert": "..."},
  "Unemployment": {"beginner": "...", "moderate": "...", "expert": "..."},
  "Budget Deficit": {"beginner": "...", "moderate": "...", "expert": "..."},
  "Current Account": {"beginner": "...", "moderate": "...", "expert": "..."},
  "Policy Rate": {"beginner": "...", "moderate": "...", "expert": "..."}
}

Metric Briefs writing rules:
- Each entry is ONE sentence (not a paragraph). Aim for 25–50 words.
- Beginner: plain English, no jargon, explains what's happening and why it matters.
- Moderate: includes specific data, technical terms, and context vs. peers or history.
- Expert: structural analysis, model references, cross-asset implications, or policy transmission mechanisms.
- Each sentence must be specific to THAT country and THAT metric right now — not generic.

Important: Include glossary term markup in stories where relevant:
<span class="glossary-term" data-term="TERM_KEY">visible text</span>
```

**Step 3:** Download the script, run it, then push:

```bash
cd /Users/lisaswerling/Downloads/macrosnaps-repo
mv ~/Downloads/update_stories_[DATE].py .
python3 update_stories_[DATE].py
git add frontend/macrosnaps-globe.html
git commit -m "Story refresh — [DATE]"
git push origin main
```

---

## 4. WHAT REFRESHES WHAT

| What changes | How to refresh | Frequency |
|---|---|---|
| Metric values (GDP, CPI, rates, FX) | Part 1 — `build_snapshot.py` | Every trading day |
| Market data (stock YTD, bond yields, vol) | Part 1 — `build_snapshot.py` | Every trading day |
| Commodity prices | Part 1 — `build_snapshot.py` | Every trading day |
| Weather emojis | Part 1 — `build_snapshot.py` | Every trading day |
| Macro forecasts | Part 1 (from Ralph's Google Sheet) | When Ralph updates |
| **Country stories** | **Part 2 — injection script** | **Every trading day** |
| **Global headline stories** | **Part 2 — injection script** | **Every trading day** |
| **Commodity stories** | **Part 2 — injection script** | **Every trading day** |
| **Metric Briefs** | **Part 2 — injection script** | **Every trading day** |
| Ralph's forecast values (GDP, inflation, etc.) | Part 1 (from Ralph's Google Sheet) | Only when Ralph updates |
| Historical arrays / weatherGrid | Manual edit | Periodic structural refresh only — NOT daily |
| Glossary terms | Manual edit (rarely changes) | As needed |

---

## 5. CURRENT STATE (as of March 7, 2026)

- **Countries:** 12 (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS)
- **Commodities:** 9
- **Glossary terms:** ~192
- **Stories:** Written March 7 — injection script `update_stories_2026-03-07.py` exists but NOT YET RUN
- **Data:** Last refreshed Feb 18 — needs Part 1 run today
- **Metric Briefs:** Not yet implemented in frontend (see Section 11 below)

### Story themes (March 7, 2026)

**Dominant theme: Strait of Hormuz Crisis + US Jobs Shock + Gold ATH ($5,159)**

| Country | Key Themes | Weather |
|---|---|---|
| USA | Feb NFP −92K shock (vs +59K expected), DOGE cuts −330K govt jobs since Oct, unemployment 4.4%, Fed hold 3.50–3.75%, stagflation trap, DXY <96, gold $5,159 ATH | ⛈️ |
| CAN | Q4 GDP −0.6% annualised (first contraction in 2 years), BoC hold 2.25%, CUSMA July 2026 deadline, exports −4%, CAD at 72 US cents | ⛅ |
| GBR | BoE cut expected March 19 to 3.50%, CPI 3.0%, GDP Q4 +0.1%, services inflation 4.4%, April minimum wage +8.5%, twin deficits vulnerable | ⛅ |
| JPN | BoJ hold 0.75% (30yr high), March 18–19 meeting no change expected, 10Y JGB testing 1.50%+, yen 155–158, ~70% oil imports via Hormuz, PM Takaichi ¥783tn record budget | ⛅ |
| DEU | €500bn infrastructure fund + defence Schuldenbremse exemption (constitutional amendment), manufacturing orders +9.6% Q4, ECB hold 2.0%, fiscal inflection from drag to driver | ⛅ |
| FRA | Deficit 5% GDP, EDP, KBRA downgraded to AA−, OAT-Bund spread ~55bps, debt servicing €59bn, three no-confidence votes, TPI activation risk H2 2026 | ⛈️ |
| ITA | Deficit 3.1% (EDP), BTP-Bund spread ~110–120bps, primary balance turning positive for first time in decades, NRRP €113bn of €191bn received, LNG contracts via Eni provide partial insulation | ⛅ |
| CHN | GDP 4.9% but deflation (CPI ~0%, PPI negative), 80M+ empty homes, property −17.2% over 3 years, 6M b/d Hormuz exposure, 15th FYP, $1tn trade surplus, PBOC expected 20bp cut + 100bp RRR | ⛈️ |
| IND | GDP 7.4% FY26, RBI neutral at 5.25% (after 125bp cuts), CPI 3.9–4%, 'goldilocks period', US-India trade deal (25%→18%), ~70% Gulf oil imports via Hormuz | ☀️ |
| ZAF | Gold $5,159 ATH boosts mining revenue, ZAR +13–14% (best since 2009), SARB hold 6.75%, CPI 3.5% (21yr low), FATF grey list removed Oct 2025, S&P upgrade, Eskom improved, unemployment 31.9% | ⛅ |
| BRA | Selic 15% (highest since 2006), COPOM March 17–18 meeting (50bp cut expected to 14.50%), CPI 4.3%, unemployment 5.2% (lowest since 2012), EU-Mercosur advancing, election year spending risk | ⛈️ |
| RUS | CBR cut to 15.5%, GDP stagnating 0.5–1%, ruble +45% YoY, VAT hiked to 22%, sanctions tightening, FRED degraded (3 series active, rest fallback), IMOEX.ME may show delisted | ⛈️ |
| Global | Hormuz crisis since Feb 28 (US+Israel struck Iran), 20% of world oil supply disrupted, gold $5,159 ATH, DXY <96 structural break, stagflation trap for major central banks | — |
| Commodities | WTI $72.50 (+9.8%), Brent $80.50 (+9.2%), NatGas $2.83 (+8.4%), Gold $5,159 (+2.8%), Silver $58.20 (+3.2%), Copper $5.20 (+1.5%), Wheat $585 (+1.2%), Corn $455 (+0.9%), Soybeans $1,065 (+0.7%) | ⛈️ |

---

## 6. STORY STRUCTURE REFERENCE

**Where stories live in the HTML:**
- Country stories: `<script id="countries-data">` → each country → `"stories"` key
- Metric Briefs: `<script id="countries-data">` → each country → `"metricBriefs"` key
- Global stories: `<script id="app-config">` → `"globalStories"` key
- Commodity stories: `<script id="app-config">` → `"commodities"` → `"stories"` key

**Country stories format** (simple string arrays):
```json
{
  "beginner": ["bullet 1", "bullet 2", "bullet 3"],
  "moderate": ["bullet 1", "bullet 2", "bullet 3"],
  "expert":   ["bullet 1", "bullet 2", "bullet 3"]
}
```

**Global stories format** (has icon/label/body/source):
```json
{
  "beginner": [
    { "icon": "🔥", "label": "Today's Story", "body": "HTML string...", "source": "Bloomberg" },
    { "icon": "⚡", "label": "Biggest Movers", "body": "...", "source": "..." },
    { "icon": "📊", "label": "The Connection", "body": "...", "source": "..." }
  ],
  "moderate": [...],
  "expert": [...]
}
```

**Commodity stories format:** Same as country stories (simple string arrays).

**Metric Briefs format:**
```json
{
  "GDP Growth":       { "beginner": "...", "moderate": "...", "expert": "..." },
  "Inflation (CPI)":  { "beginner": "...", "moderate": "...", "expert": "..." },
  "Unemployment":     { "beginner": "...", "moderate": "...", "expert": "..." },
  "Budget Deficit":   { "beginner": "...", "moderate": "...", "expert": "..." },
  "Current Account":  { "beginner": "...", "moderate": "...", "expert": "..." },
  "Policy Rate":      { "beginner": "...", "moderate": "...", "expert": "..." }
}
```

Metric Briefs cover only the 6 macro metrics. One sentence per level, 25–50 words each.

**Glossary term markup:**
```html
<span class="glossary-term" data-term="fed">Federal Reserve</span>
```

**Global story icons per slot:**
- Slot 1: 🔥 Today's Story
- Slot 2: ⚡ Biggest Movers
- Slot 3: 📊 The Connection (beginner) / varies at higher levels

**Content totals per refresh:**
- Headline stories: 12 × 9 + 9 global + 9 commodity = 126 bullets
- Metric Briefs: 12 × 6 × 3 = 216 sentences
- Grand total: 342 content items

---

## 7. DATA FLOW

```
                   ┌────────────────────┐
                   │  Ralph's Google     │
                   │  Sheet (forecasts)  │
                   └────────┬───────────┘
                            │ CSV fetch
                            ▼
┌──────────┐    ┌──────────────────────┐    ┌────────────┐
│ FRED API │───▶│  build_snapshot.py   │◀───│ Yahoo Fin  │
│ (macro)  │    │  Merges all sources  │    │ (markets)  │
└──────────┘    │  Applies fallbacks   │    └────────────┘
                │  Assigns weather     │
                └────────┬─────────────┘
                         ▼
                   snapshot.json
                         │ git push
                         ▼
            ┌─────────────────────────┐
            │   macrosnaps-globe.html │
            │   (reads snapshot.json  │
            │    at load time)        │
            └─────────────────────────┘
```

**Google Sheet URL:**
```
https://docs.google.com/spreadsheets/d/e/2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj/pub?gid=0&single=true&output=csv
```
Columns: Country | GDP_Growth_2026 | Inflation_2026 | Budget_Deficit_2026 | Current_Account_2026 | Unemployment_2026. Policy Rate always comes from FRED.

---

## 8. DEPLOYMENT

```
Local Mac          →  git push  →  GitHub/main  →  webhook  →  Render (live ~2 min)
```

The `.env` file is NOT pushed to GitHub. `FRED_API_KEY` lives only on your Mac.
Cache bust: **Cmd+Shift+R** or incognito (Cmd+Shift+N).

---

## 9. BACKEND FALLBACK METRICS

| Metric | Countries using fallback |
|---|---|
| Corp Spread | All 12 countries |
| Sov CDS | All 12 countries |
| Yield Curve | 10 countries |
| GDP Growth | CHN, RUS |
| Unemployment | CHN, IND, BRA, RUS |
| 10Y Bond Yield | CHN, IND, BRA, RUS |
| Currency (FX) | RUS (Yahoo may override) |

**Russia-specific notes:**
- Only 3 FRED series active (inflation, policy_rate, current_account); rest use fallback
- Yahoo `IMOEX.ME` may show "delisted" — stock YTD and equity vol will be missing
- Yahoo `USDRUB=X` may reflect offshore NDF pricing, not CBR official rate

---

## 10. KNOWN LIMITATIONS

1. Stories are static — must be manually researched and injected via Python scripts
2. No automated scheduling — daily ritual is manual bash commands
3. Single HTML file — any JSON syntax error breaks the entire app
4. Fallback values go stale — corp spread, sov CDS, yield curve should be reviewed periodically
5. Russia FRED degraded — sanctions have broken many OECD-sourced series
6. Russia FX unreliable — Yahoo may reflect NDF rates, not official CBR rate
7. ZAF unemployment FRED broken — `LRHUTTTTZAM156S` returns 400 errors; uses fallback
8. No error monitoring — if Render deploys broken HTML, there is no alert

---

## 11. METRIC BRIEFS — NOT YET IMPLEMENTED IN FRONTEND

**Status:** Content format is designed and the injection script pattern is ready. The frontend code change (one-time, ~15 min) still needs to be made.

**What it does:** When a user clicks a metric (e.g. GDP) in a country card, adds a country-specific explanation between the chart and the glossary BLUF, creating the flow: Chart → "why does Japan's GDP look like this right now" → "what is GDP in general."

**Step 1 — Frontend code change needed (one-time):**

Edit the metric popover renderer in `macrosnaps-globe.html`. After the chart and before the glossary BLUF, add:

```javascript
const brief = countryData.metricBriefs && countryData.metricBriefs[metricName];
if (brief) {
    const level = getCurrentExpertiseLevel(); // beginner | moderate | expert
    const briefText = brief[level];
    if (briefText) {
        // Render: 📍 [Country Name] — [Metric Name] / [briefText]
        // Style subtly distinct from glossary below.
    }
}
// Then render glossary BLUF as before (unchanged)
```

Upload `macrosnaps-globe.html` to a Claude session and ask for the exact patch.

**Step 2 — Injection script pattern** (add to any future update_stories script):

```python
COUNTRY_METRIC_BRIEFS = {
    "USA": {
        "GDP Growth":      {"beginner": "...", "moderate": "...", "expert": "..."},
        "Inflation (CPI)": {"beginner": "...", "moderate": "...", "expert": "..."},
        "Unemployment":    {"beginner": "...", "moderate": "...", "expert": "..."},
        "Budget Deficit":  {"beginner": "...", "moderate": "...", "expert": "..."},
        "Current Account": {"beginner": "...", "moderate": "...", "expert": "..."},
        "Policy Rate":     {"beginner": "...", "moderate": "...", "expert": "..."}
    },
    # ... all 12 countries
}

# In inject():
briefs_updated = 0
for code, briefs in COUNTRY_METRIC_BRIEFS.items():
    if code in countries:
        countries[code]["metricBriefs"] = briefs
        briefs_updated += 1
        print(f"  ✅ {code} Metric Briefs updated ({len(briefs)} metrics)")
print(f"\n  Metric Briefs updated: {briefs_updated}/12")
```

**Phased rollout option:** Start with USA, JPN, ZAF (Phase 1 — 54 sentences), validate UX, then expand to all 12 (Phase 2 — 216 sentences).

---

## 12. POTENTIAL FUTURE WORK

- **Metric Briefs frontend implementation** (see Section 11 — ready to build)
- **Daily PDF briefing** — downloadable morning overview (weather grid, top movers, stories, per-country metrics). Runs as Python script after Part 1. Decisions needed: single expertise level or all three, compact/standard/full detail, whether to use as daily email/notification.
- **Automated story generation** (LLM-powered)
- **Automated daily scheduling** (cron or Render cron job)
- **Error monitoring / alerting** on deploy failures
- **Additional countries** (Turkey, etc.)

---

## 13. USEFUL COMMANDS

```bash
# Check live site
open https://macrosnaps-01.onrender.com/macrosnaps-globe.html

# Check git status
cd /Users/lisaswerling/Downloads/macrosnaps-repo && git status

# View recent commits
git log --oneline -10

# Run data refresh (Part 1)
FRED_API_KEY=$(grep FRED_API_KEY .env | cut -d= -f2) python3 backend/build_snapshot.py

# Deploy data
cp snapshot.json frontend/snapshot.json
git add frontend/snapshot.json snapshot.json
git commit -m "Daily data refresh — $(date +%b\ %d)"
git push origin main

# Deploy stories (Part 2 — after running injection script)
git add frontend/macrosnaps-globe.html
git commit -m "Story refresh — $(date +%b\ %d)"
git push origin main

# Hard refresh browser cache
# Cmd+Shift+R or incognito (Cmd+Shift+N)

# Count countries in frontend
python3 -c "import json; html=open('frontend/macrosnaps-globe.html').read(); s=html.index('<script type=\"application/json\" id=\"countries-data\">')+len('<script type=\"application/json\" id=\"countries-data\">'); e=html.index('</script>',s); c=json.loads(html[s:e]); print(f'{len(c)} countries: {sorted(c.keys())}')"

# Verify FRED series for Russia
KEY=$(grep FRED_API_KEY .env | cut -d= -f2) && for S in RUSCPIALLMINMEI IRSTCI01RUM156N RUSB6BLTT02STSAQ; do echo -n "$S → "; curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=${S}&api_key=${KEY}&file_type=json&sort_order=desc&limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); obs=d.get('observations',[]); print(f'✅ {obs[0][\"date\"]} = {obs[0][\"value\"]}' if obs and obs[0].get('value','.')!='.' else '❌ NO DATA')" 2>/dev/null || echo "❌ ERROR"; done
```

---

## 14. GIT HISTORY (recent)

```
[March 7 — stories written but not yet pushed]
1c53235 Add RUS to countries-data (full entry + Feb 18 stories)
ec3556b Story refresh — Feb 18
[prior]  Daily data refresh — Feb 18
[prior]  Story update Feb 13 2026
```

---

## 15. FOR THE NEXT CLAUDE SESSION

**Files to upload:**
1. This handover doc (macrosnaps-handover-march8.md)
2. `macrosnaps-globe.html` (download fresh from `frontend/` — it is the source of truth)

**You do NOT need to upload `build_snapshot.py`** — Claude doesn't need it for story refreshes.
