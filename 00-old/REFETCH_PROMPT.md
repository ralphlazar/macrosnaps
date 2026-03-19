# MacroSnaps - Re-fetch Historical Data Prompt

Use this prompt when you need to run or debug `refetch_historical.py`.
Paste it as your first message in a new chat. No file uploads needed.

---

## PROMPT

I have a Python script called `refetch_historical.py` that re-fetches historical chart data for a dashboard called MacroSnaps. The script runs standalone on my Mac with no backend needed. It pulls data from FRED (Federal Reserve Economic Data API) and Yahoo Finance, then writes the results into `data.json` under the `_frozen_historical` key for each country.

**My project folder is:** `~/Downloads/macrosnaps`

**The script is already written and sitting in that folder.** I am not asking you to write it from scratch. I need help running it, debugging errors, or verifying the output.

**What the script does:**

It loops through all 12 countries (USA, CAN, GBR, JPN, DEU, FRA, ITA, CHN, IND, ZAF, BRA, RUS) and for each one fetches:

- GDP Growth (annual bar, 6 years) from FRED
- Inflation CPI (monthly line, 60 months) from FRED
- Unemployment (monthly line, 60 months) from FRED
- Policy Rate (annual line, 6 years) from FRED
- Current Account (annual bar, 6 years) from FRED
- 10Y Bond Yield (monthly line, 60 months) from FRED
- Yield Curve (10Y minus short rate, monthly line, 60 months) from FRED
- Stock Market YTD (monthly line, 60 months) from Yahoo Finance via yfinance
- FX pair (monthly line, 60 months) from FRED

It does NOT fetch and cannot restore: Equity Vol, Corp Spread, Sov CDS, FX Vol, Budget Deficit. Those have no free public FRED source and will remain as gaps.

The script skips any metric that already has sufficient data points, unless `FORCE_OVERWRITE = True` is set at the top of the file.

**The `_frozen_historical` format it writes:**

Each entry is a dict with a `v` array of floats, a `type` field (`line` or `bar`), and optional fields:
- `annual: True` for annual bar charts
- `stepped: True` for policy rate line charts
- `zeroLine: True` for yield curve charts
- `indexLabel: True` for stock market charts

Example:
```json
"GDP Growth": {"v": [-2.8, 5.9, 2.1, 2.5, 2.9, 2.8], "annual": true, "type": "bar"}
"Inflation (CPI)": {"v": [1.4, 1.7, ...60 values...], "type": "line"}
```

**Requirements to run:**

1. Python 3 installed (already present: `python3`)
2. Dependencies: `pip3 install requests yfinance python-dotenv`
3. A free FRED API key from fred.stlouisfed.org/docs/api/api_key.html
4. A `.env` file in `~/Downloads/macrosnaps/` containing: `FRED_API_KEY=your_key_here`

**To run:**
```bash
cd ~/Downloads/macrosnaps && python3 refetch_historical.py
```

**After it runs successfully:**
```bash
python3 build.py && git add -A && git commit -m "Restore _frozen_historical for all countries"
```

**What I need help with today:**

[describe what you need - e.g. "I am getting this error when I run the script: ..." or "The script ran but some countries still show missing data" or "Help me verify the output looks correct before I rebuild"]

---

## CONTEXT IF NEEDED

The `_frozen_historical` data feeds the metric chart tooltips. The shell reads it at line 5638:
```javascript
if(c._frozen_historical) historicalData[c.code] = c._frozen_historical;
```

The current state before running the script is:
- USA, JPN, ITA: 14/14 charts populated (do not need re-fetching)
- ZAF, BRA, RUS: 6/14 charts populated
- CAN, GBR, DEU, FRA, CHN, IND: 3/14 charts populated

After a successful run, all countries should have 9-10 charts populated (the 4-5 metrics with no FRED source will remain as gaps).

The script has `FORCE_OVERWRITE = False` by default, meaning it will not overwrite USA, JPN, or ITA since they already have full data. To re-fetch everything from scratch, set `FORCE_OVERWRITE = True` at the top of the script.
