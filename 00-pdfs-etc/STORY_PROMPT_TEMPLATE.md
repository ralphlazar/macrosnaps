# MacroSnaps — Story Prompt Templates

Cadence-based prompts for rewriting USA per-metric stories in `data.json`.
Use the appropriate template based on the metric's tier (see `data.json → _meta.tier_guide`).

---

## Post-Update Checklist (ALL cadences)

After using any prompt below:
1. Replace the `story` field in `data.json` for the relevant metric with the returned JSON.
2. Also update the metric's `value` and `last_updated` fields if the underlying data has changed.
3. Re-run `python3 build.py` to validate and regenerate `macrosnaps-globe.html`.
4. Confirm build output shows `✓ BUILD SUCCESSFUL`.

---

## DAILY Cadence — Market Metrics

**Applies to:** Stock Market YTD, Equity Vol, 10Y Bond Yield, Yield Curve, Corp Spread, Sov CDS, USD/DXY, FX Vol

**When to rewrite:** Every trading day at market close (US Eastern time).

---

### Prompt

```
You are writing per-metric story content for the MacroSnaps economic dashboard.
Today is [DATE]. Market close data for the United States is:

Metric: [METRIC NAME]
Current value: [VALUE]
Prior day value: [PRIOR VALUE]
Change: [CHANGE / % CHANGE]
Key context: [1–2 sentences on what drove today's move — e.g. Fed speaker, macro print, geopolitical event]

Write a "story" JSON object for this metric with three keys: beginner, moderate, expert.

TONE AND LENGTH RULES:
- beginner: Plain English, no jargon. Explain what the number means and why it changed today.
  Target: 60–80 words.
- moderate: Use market vocabulary (e.g. basis points, spreads, yield curve). Reference today's
  data driver and what it signals for the US economic outlook.
  Target: 90–120 words.
- expert: Use precise financial language. Reference specific mechanisms, cross-asset implications,
  and forward-looking policy transmission. Cite data points where relevant (levels, bps, %).
  Target: 120–160 words.

Return ONLY valid JSON — no preamble, no markdown fences, no trailing text:
{"beginner": "...", "moderate": "...", "expert": "..."}
```

---

## WEEKLY Cadence — Economic Data Releases

**Applies to:** Inflation (CPI), Unemployment, Policy Rate

**When to rewrite:** On the day of the official data release only (not every week).
- CPI: BLS release day (typically mid-month)
- Unemployment: BLS Jobs Report Friday (first Friday of month)
- Policy Rate: FOMC meeting decision day

---

### Prompt

```
You are writing per-metric story content for the MacroSnaps economic dashboard.
Today is [DATE]. The following US economic data was just released:

Metric: [METRIC NAME]
New value: [VALUE]
Previous release value: [PRIOR VALUE]
Consensus expectation: [CONSENSUS]
Key surprise or detail: [1–2 sentences on the print — e.g. which components drove CPI, which sectors drove payrolls]
Macro context: [1 sentence on how this fits the current Fed narrative / market pricing]

Write a "story" JSON object for this metric with three keys: beginner, moderate, expert.

TONE AND LENGTH RULES:
- beginner: Explain the number in everyday terms. What does this mean for people's lives —
  jobs, prices, mortgages? Avoid acronyms.
  Target: 65–85 words.
- moderate: Use economic vocabulary. Reference the component breakdown, consensus vs. actual,
  and implications for the Fed's next decision.
  Target: 95–120 words.
- expert: Use precise policy and market language. Reference the relevant Fed reaction function,
  cross-market implications (rates, equities, FX), and any divergence from consensus models.
  Cite specific data points (levels, bps, pps).
  Target: 125–165 words.

Return ONLY valid JSON — no preamble, no markdown fences, no trailing text:
{"beginner": "...", "moderate": "...", "expert": "..."}
```

---

## STRUCTURAL Cadence — Quarterly / Major Revision

**Applies to:** GDP Growth, Budget Deficit, Current Account

**When to rewrite:** On BEA advance/revised/final GDP release; on CBO or OMB budget update;
on BEA current account release. Typically quarterly. Also rewrite on any major policy event
that materially changes the outlook (e.g. new tariff regime, fiscal legislation enacted).

---

### Prompt

```
You are writing per-metric story content for the MacroSnaps economic dashboard.
Today is [DATE]. The following structural US data has been updated or a major policy shift occurred:

Metric: [METRIC NAME — GDP Growth / Budget Deficit / Current Account]
New value: [VALUE e.g. +2.8%]
Previous value: [PRIOR VALUE]
Data source / release: [e.g. BEA Advance Q4 2025 GDP, CBO January Budget Outlook]
Key drivers of change: [2–3 sentences on what structural factors changed — e.g. OBBBA fiscal impulse,
  tariff regime shift, terms-of-trade movement]
Medium-term outlook: [1–2 sentences on consensus or your house view for the next 4 quarters]

Write a "story" JSON object for this metric with three keys: beginner, moderate, expert.

TONE AND LENGTH RULES:
- beginner: Explain what this structural metric measures and what the change means for ordinary
  Americans over the next year or two. Use relatable analogies. No jargon.
  Target: 70–90 words.
- moderate: Use economic vocabulary. Discuss the structural drivers, policy implications, and
  forward path. Reference consensus forecasts where relevant.
  Target: 100–130 words.
- expert: Use precise macro and policy language. Reference the specific mechanism (fiscal multiplier,
  Lerner symmetry, output gap dynamics, etc.), cross-asset or cross-country implications, and
  any material risks to the baseline. Cite data points and institutional sources.
  Target: 135–180 words.

Return ONLY valid JSON — no preamble, no markdown fences, no trailing text:
{"beginner": "...", "moderate": "...", "expert": "..."}
```

---

## Reference: USA Metric → Cadence Mapping

| Metric | Section | Tier | Rewrite cadence |
|---|---|---|---|
| GDP Growth | macro | structural | Quarterly / BEA release |
| Inflation (CPI) | macro | weekly | CPI release day only |
| Unemployment | macro | weekly | Jobs Report Friday only |
| Budget Deficit | macro | structural | Quarterly / CBO update |
| Current Account | macro | structural | Quarterly / BEA release |
| Policy Rate | macro | weekly | FOMC decision day only |
| Stock Market YTD | market | daily | Every trading day at close |
| Equity Vol | market | daily | Every trading day at close |
| 10Y Bond Yield | market | daily | Every trading day at close |
| Yield Curve | market | daily | Every trading day at close |
| Corp Spread | market | daily | Every trading day at close |
| Sov CDS | market | daily | Every trading day at close |
| USD/DXY | market | daily | Every trading day at close |
| FX Vol | market | daily | Every trading day at close |

---

## Notes on Quality

- **Ground stories in data**: Every claim should reflect the actual current value and recent change.
  Avoid generic statements that could apply to any period.
- **Level consistency**: The three levels should tell the same underlying story at different depths —
  not three different narratives. A beginner reading all three should not feel contradicted by the expert.
- **Word count discipline**: LLMs tend to over-write. Use the upper bound as a hard cap.
  If the model exceeds it, instruct it to trim.
- **Avoid recency hallucination**: If context window data is stale, instruct the model explicitly
  with today's date and fresh values before calling the prompt.
