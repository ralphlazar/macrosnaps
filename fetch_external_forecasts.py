#!/usr/bin/env python3
"""
fetch_external_forecasts.py — fetches latest 2026 macro forecasts from IMF,
OECD, major brokerages etc. via Anthropic web search. Writes external_forecasts.json.

Recommended cadence: weekly (Monday morning, before the daily ritual).
Cost: ~$0.45–0.75 per run (12 × Haiku 4.5 + web search).

Usage:
    python3 fetch_external_forecasts.py --dry-run   # preview only, no file write
    python3 fetch_external_forecasts.py             # fetch and write
"""

import os
import sys
import json
import time
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
DRY_RUN = "--dry-run" in sys.argv
MODEL   = "claude-haiku-4-5-20251001"   # Haiku is sufficient for retrieval tasks
DELAY_BETWEEN_CALLS = 1.5               # seconds, gentle rate limiting

COUNTRIES = {
    "USA": "United States",
    "CHN": "China",
    "DEU": "Germany",
    "JPN": "Japan",
    "IND": "India",
    "GBR": "United Kingdom",
    "FRA": "France",
    "ITA": "Italy",
    "BRA": "Brazil",
    "CAN": "Canada",
    "RUS": "Russia",
    "ZAF": "South Africa",
}

METRICS = ["GDP_Growth", "Inflation", "Unemployment", "Budget_Deficit", "Current_Account", "Policy_Rate"]

# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a macro research assistant. Find the latest published 2026 economic forecasts for a given country from credible institutions: IMF WEO, World Bank, OECD Economic Outlook, Goldman Sachs, JPMorgan, Morgan Stanley, Citi, Barclays, Deutsche Bank, HSBC, or Trading Economics.

Respond with ONLY a valid JSON object — no preamble, no markdown backticks, no explanation. Use exactly this schema:

{
  "GDP_Growth":      {"value": 2.3,  "source": "IMF WEO",        "date": "Jan 2026", "prior": 2.1,  "notes": "Revised up from Oct WEO"},
  "Inflation":       {"value": 2.6,  "source": "Goldman Sachs",   "date": "Feb 2026", "prior": null, "notes": ""},
  "Unemployment":    {"value": 4.1,  "source": "OECD",            "date": "Dec 2025", "prior": null, "notes": ""},
  "Budget_Deficit":  {"value": -6.2, "source": "IMF WEO",         "date": "Jan 2026", "prior": null, "notes": "% of GDP"},
  "Current_Account": {"value": -3.1, "source": "IMF WEO",         "date": "Jan 2026", "prior": null, "notes": "% of GDP"},
  "Policy_Rate":     {"value": 4.25, "source": "JPMorgan",        "date": "Mar 2026", "prior": null, "notes": "Year-end forecast"}
}

Field rules:
- "value": float or null. GDP Growth, Inflation, Unemployment in %. Budget Deficit and Current Account as % of GDP (negative = deficit). Policy Rate as % (year-end).
- "source": institution name. Use "Not found" if unavailable.
- "date": approximate publication month/year of the forecast (e.g. "Jan 2026").
- "prior": the previous forecast from the same institution if a revision was found, else null.
- "notes": any brief context worth flagging (revision reason, caveats, range). Empty string if none.
- If you cannot find a reliable 2026 forecast for a metric, use null for value and "Not found" for source.

Return ONLY the JSON object. No text before or after it."""


def build_user_prompt(code: str, name: str) -> str:
    return (
        f"Search for the latest published 2026 macroeconomic forecasts for {name} ({code}). "
        "Look for forecasts from IMF WEO (January 2026 or later update), OECD Economic Outlook, "
        "World Bank, or major investment bank research notes published in 2026. "
        "Find the most recent available estimate for each of these six metrics:\n\n"
        "1. GDP Growth — real GDP % change 2026\n"
        "2. Inflation — CPI annual average % 2026\n"
        "3. Unemployment rate — % 2026 annual average\n"
        "4. Budget Balance — general government balance as % of GDP (negative = deficit)\n"
        "5. Current Account — % of GDP (negative = deficit)\n"
        "6. Central bank policy rate — year-end 2026 forecast %\n\n"
        "For each metric, note the source institution, publication date, and whether the "
        "institution revised the forecast recently (and if so, what the prior estimate was)."
    )


# ── Fetch ─────────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def fetch_country(code: str, name: str) -> dict:
    """Fetch external forecasts for one country. Returns dict of 6 metrics."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content": build_user_prompt(code, name)}],
        )

        # Collect all text blocks from the response
        text = "".join(block.text for block in response.content if block.type == "text").strip()

        # Extract JSON robustly — strip preamble prose and ```json fences
        start = text.find("{")
        end   = text.rfind("}")
        if start == -1 or end == -1:
            raise json.JSONDecodeError("No JSON object found in response", text, 0)
        text = text[start:end + 1]

        data = json.loads(text)

        # Validate: ensure all expected keys are present
        result = {}
        for metric in METRICS:
            entry = data.get(metric, {})
            result[metric] = {
                "value":  entry.get("value"),
                "source": entry.get("source", "Not found"),
                "date":   entry.get("date", ""),
                "prior":  entry.get("prior"),
                "notes":  entry.get("notes", ""),
            }
        return result

    except json.JSONDecodeError as e:
        print(f"\n    ⚠  JSON parse error: {e}")
        print(f"    Raw response: {text[:300]}")
        return _empty_result(f"JSON parse error: {e}")
    except Exception as e:
        return _empty_result(str(e))


def _empty_result(error_msg: str) -> dict:
    return {
        m: {"value": None, "source": "Error", "date": "", "prior": None, "notes": error_msg}
        for m in METRICS
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    tag = "DRY RUN — " if DRY_RUN else ""
    print(f"\n{tag}fetch_external_forecasts.py")
    print(f"Model: {MODEL}  |  Countries: {len(COUNTRIES)}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    results   = {}
    errors    = []
    start     = time.time()

    for i, (code, name) in enumerate(COUNTRIES.items(), 1):
        print(f"  [{i:2d}/{len(COUNTRIES)}]  {code:<4}  {name:<20}", end="", flush=True)
        result = fetch_country(code, name)
        results[code] = result

        # Quick summary line
        found = sum(1 for m in METRICS if result[m]["value"] is not None)
        revised = sum(1 for m in METRICS if result[m].get("prior") is not None)
        rev_str = f"  {revised} revised" if revised else ""
        print(f"  {found}/6 found{rev_str}")

        error_metrics = [m for m in METRICS if result[m]["source"] in ("Error", "Not found")]
        if error_metrics:
            errors.append(f"{code}: {', '.join(error_metrics)}")

        if i < len(COUNTRIES):
            time.sleep(DELAY_BETWEEN_CALLS)

    elapsed = round(time.time() - start)
    print(f"\n  Done in {elapsed}s.")

    if errors:
        print(f"\n  ⚠  Missing/errors ({len(errors)}):")
        for e in errors:
            print(f"     {e}")

    output = {
        "_meta": {
            "generated": datetime.utcnow().isoformat() + "Z",
            "model":     MODEL,
            "elapsed_s": elapsed,
        },
        "countries": results,
    }

    if DRY_RUN:
        print("\n─── DRY RUN — output not written ───────────────────────────────────")
        print(json.dumps(output, indent=2)[:3000])
        print("..." if len(json.dumps(output)) > 3000 else "")
    else:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "external_forecasts.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  ✓  Written → {out_path}")


if __name__ == "__main__":
    main()
