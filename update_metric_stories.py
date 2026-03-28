#!/usr/bin/env python3
"""
update_metric_stories.py
========================
Drafts fresh 3-bullet metric stories for all 12 countries across all metrics.

Architecture:
  - Reads harvest_{TODAY}.json produced by update_headlines.py (reuses the
    Sonnet+search harvest, no extra API cost)
  - 12 parallel Haiku calls (1 country each): generates 3 bullets per metric
    per level (beginner / moderate / expert)
  - Saves METRICS_draft_{TODAY}.json for review in metric_story_review.html
  - Apply step writes approved bullets back into data.json

Usage:
    python3 update_metric_stories.py                          # generate draft
    python3 update_metric_stories.py --apply                  # apply most recent approved
    python3 update_metric_stories.py --apply METRICS_approved_2026-03-28.json

Requires:
    ANTHROPIC_API_KEY in .env
    data.json in the same folder
    harvest_{TODAY}.json produced by update_headlines.py
    pip3 install anthropic python-dotenv
"""

import json, os, sys, time, glob, argparse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime

try:
    import anthropic
except ImportError:
    print("\n  FATAL: anthropic package not installed.")
    print("  Run: pip3 install anthropic python-dotenv\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATA_FILE = "data.json"
TODAY     = date.today().isoformat()
MODEL     = "claude-haiku-4-5-20251001"
LEVELS    = ["beginner", "moderate", "expert"]

COUNTRY_ORDER = [
    "USA","CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"
]

LEVEL_GUIDANCE = {
    "beginner": "3 punchy points. No jargon. Answer: what's the story with this metric right now? Interpret, never describe the data.",
    "moderate": "3 punchy points. Interpret the metric, add one piece of context: a historical comparison, a regional comparison, or the key causal driver.",
    "expert":   "3 punchy points. Specific numbers, a directional signal, one forward implication. Interpret, the reader can see the data.",
}

STYLE_GUIDE = """STORY WRITING RULES - apply to every bullet at every level:
- No em dashes or en dashes, ever. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural.
- No hedging openers. Never start with "It is worth noting" or "It is important to understand."
- No AI-typical sentence starters. Do not begin consecutive bullets with "This metric," "This reflects," or "This suggests."
- Write numbers as real and specific. "Inflation hit 8.4%" not "the inflation rate stands at 8.4%."
- No filler conclusions. Never end with "overall," "in summary," or "taken together."
- No committee language. Write as if explaining to a smart friend, not presenting a report.
- GOLDEN RULE: The reader can see the data. Do not describe it. Tell them what it means, why it matters today, and what to watch next.
- Each bullet is ONE punchy sentence. Not a paragraph. One sentence."""


def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  FATAL: ANTHROPIC_API_KEY not set. Add it to .env.\n")
        sys.exit(1)
    return anthropic.Anthropic(
        api_key=api_key,
        timeout=anthropic.Timeout(connect=30.0, read=180.0, write=30.0, pool=10.0)
    )


def extract_json(text):
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.startswith("json"):
                part = part[4:]
            part = part.strip()
            if part.startswith("{"):
                text = part
                break
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found")
    text = text[start:end]

    def attempt(s):
        try: return json.loads(s)
        except: return None

    r = attempt(text)
    if r: return r
    t = re.sub(r",[ \t\n]*([]|}])", r"\1", text)
    t = t.replace("\u2018","'").replace("\u2019","'").replace("\u201c",'"').replace("\u201d",'"')
    r = attempt(t)
    if r: return r
    def fix(m):
        inner = m.group(1).replace("\n"," ").replace("\r"," ").replace("\t"," ")
        return '"' + inner + '"'
    t2 = re.sub(r'"((?:[^"\\\n]|\\.)*)"', fix, t)
    r = attempt(t2)
    if r: return r
    raise ValueError(f"Could not parse JSON. Tail: ...{text[-200:]}")


def load_harvest():
    filename = f"harvest_{TODAY}.json"
    if os.path.exists(filename):
        with open(filename) as f:
            data = json.load(f)
        print(f"  [HARVEST] Loaded {filename}")
        return data
    candidates = sorted(glob.glob("harvest_*.json"), reverse=True)
    if candidates:
        print(f"  [HARVEST] Today's harvest not found, using {candidates[0]}")
        with open(candidates[0]) as f:
            return json.load(f)
    print("  [HARVEST] WARNING: No harvest file found. Run update_headlines.py first.")
    return {}


def get_country_metrics(cd):
    """Return list of (section, metric_name, current_value) for metrics with stories."""
    metrics = []
    for section in ["macro", "market"]:
        for name, v in cd.get("metrics", {}).get(section, {}).items():
            if isinstance(v, dict) and isinstance(v.get("story"), dict):
                metrics.append((section, name, v.get("value", "")))
    return metrics


def build_batch_prompt(codes, countries_data, recent_data):
    lines = [
        f"Today is {TODAY}.",
        "",
        "Write 3-bullet metric stories for each of the following countries.",
        "Each metric needs 3 bullets at each of 3 audience levels (beginner, moderate, expert).",
        "",
        STYLE_GUIDE,
        "",
        "Level guidance:",
    ]
    for lv, guide in LEVEL_GUIDANCE.items():
        lines.append(f"  {lv}: {guide}")
    lines += [
        "",
        "IMPORTANT: Lead each bullet with recent data and events, not with annual forecast numbers.",
        "",
        "Recent country context (use as lead context):",
        "",
    ]
    for code in codes:
        recent = recent_data.get(code, "")
        lines.append(f"{code}: {recent if recent else 'Use your knowledge of current conditions.'}")
    lines += ["", "Metrics per country with current values:", ""]
    for code in codes:
        cd = countries_data.get(code)
        if not cd:
            continue
        lines.append(f"{code} - {cd.get('name', code)}")
        for section, name, value in get_country_metrics(cd):
            lines.append(f"  [{section}] {name}: {value}")
        lines.append("")
    lines += [
        "BULLET COUNT RULE: EVERY level for EVERY metric for EVERY country must have EXACTLY 3 bullets.",
        "",
        "Output ONLY a JSON object. No preamble, no markdown fences:",
        '{',
        '  "USA": {',
        '    "GDP Growth": {',
        '      "beginner": ["bullet 1", "bullet 2", "bullet 3"],',
        '      "moderate": ["bullet 1", "bullet 2", "bullet 3"],',
        '      "expert":   ["bullet 1", "bullet 2", "bullet 3"]',
        '    },',
        '    "Inflation (CPI)": { ... },',
        '    ... (all metrics for this country)',
        '  },',
        '  ... (all countries listed above)',
        '}',
        "",
        "Use the exact metric names as shown above. Use straight apostrophes only.",
    ]
    return "\n".join(lines)


def draft_batch(client, codes, countries_data, recent_data, label):
    print(f"  [BATCH {label}] {', '.join(codes)}...", end=" ", flush=True)
    prompt = build_batch_prompt(codes, countries_data, recent_data)

    for attempt in range(2):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
        except anthropic.RateLimitError:
            print("(rate limit, waiting 30s...)", end=" ", flush=True)
            time.sleep(30)
            continue

        text   = response.content[0].text
        parsed = extract_json(text)

        problems = []
        for code in codes:
            if code not in parsed:
                problems.append(f"missing: {code}")
                continue
            cd = countries_data.get(code)
            if not cd:
                continue
            for _, name, _ in get_country_metrics(cd):
                if name not in parsed[code]:
                    problems.append(f"{code}/{name}: missing metric")
                    continue
                for lv in LEVELS:
                    bullets = parsed[code][name].get(lv, [])
                    if not isinstance(bullets, list) or len(bullets) < 3:
                        got = len(bullets) if isinstance(bullets, list) else 0
                        problems.append(f"{code}/{name}/{lv}: got {got} bullets")

        if not problems:
            print("OK")
            return parsed

        if attempt == 0:
            print(f"({len(problems)} problems, retrying...)", end=" ", flush=True)
            time.sleep(5)
        else:
            print(f"PARTIAL ({len(problems)} problems)")
            for p in problems[:5]:
                print(f"    {p}")
            return parsed

    return {}


def generate_draft(client, data):
    draft = {
        "date": TODAY,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "countries": {},
        "_failures": []
    }
    countries_data = data.get("countries", {})
    recent_data    = load_harvest()

    batches = [
        ([COUNTRY_ORDER[0]],  "1/12"),
        ([COUNTRY_ORDER[1]],  "2/12"),
        ([COUNTRY_ORDER[2]],  "3/12"),
        ([COUNTRY_ORDER[3]],  "4/12"),
        ([COUNTRY_ORDER[4]],  "5/12"),
        ([COUNTRY_ORDER[5]],  "6/12"),
        ([COUNTRY_ORDER[6]],  "7/12"),
        ([COUNTRY_ORDER[7]],  "8/12"),
        ([COUNTRY_ORDER[8]],  "9/12"),
        ([COUNTRY_ORDER[9]],  "10/12"),
        ([COUNTRY_ORDER[10]], "11/12"),
        ([COUNTRY_ORDER[11]], "12/12"),
    ]

    def run_batch(args):
        codes, label = args
        try:
            result = draft_batch(client, codes, countries_data, recent_data, label)
            return codes, label, result, None
        except Exception as e:
            return codes, label, {}, str(e)

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(run_batch, b): b for b in batches}
        for future in as_completed(futures):
            codes, label, result, error = future.result()
            if error:
                print(f"  [BATCH {label}] FAILED: {error}")
                draft["_failures"].extend(codes)
            else:
                for code in codes:
                    if code in result:
                        draft["countries"][code] = result[code]
                    else:
                        draft["_failures"].append(code)

    return draft


def save_draft(draft):
    filename = f"METRICS_draft_{TODAY}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    return filename


def apply_draft(approved_file, data):
    print(f"\n  Reading approved draft: {approved_file}")
    with open(approved_file) as f:
        approved = json.load(f)

    applied        = 0
    countries_data = data.get("countries", {})

    for code, metrics in approved.get("countries", {}).items():
        if code not in countries_data:
            print(f"  [SKIP] {code} not in data.json")
            continue
        for section in ["macro", "market"]:
            for name, v in countries_data[code].get("metrics", {}).get(section, {}).items():
                if not isinstance(v, dict) or not isinstance(v.get("story"), dict):
                    continue
                if name not in metrics:
                    continue
                for lv in LEVELS:
                    if lv in metrics[name] and isinstance(metrics[name][lv], list):
                        v["story"][lv] = metrics[name][lv]
                        applied += 1
        print(f"  [{code}] Applied.")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    country_count = len(approved.get("countries", {}))
    print(f"\n  Applied: {applied} metric story levels across {country_count} countries")
    print(f"  data.json updated.")
    print(f"\n  Next step: python3 build.py\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", nargs="?", const="__latest__", metavar="FILE")
    args = parser.parse_args()

    if not os.path.exists(DATA_FILE):
        print(f"\n  FATAL: {DATA_FILE} not found.\n")
        sys.exit(1)

    with open(DATA_FILE) as f:
        data = json.load(f)

    if args.apply is not None:
        if args.apply == "__latest__":
            candidates = sorted(glob.glob("METRICS_approved_*.json"), reverse=True)
            if not candidates:
                candidates = sorted(glob.glob("METRICS_draft_*.json"), reverse=True)
            if not candidates:
                print("\n  FATAL: No approved or draft file found.\n")
                sys.exit(1)
            approved_file = candidates[0]
        else:
            approved_file = args.apply
            if not os.path.exists(approved_file):
                print(f"\n  FATAL: File not found: {approved_file}\n")
                sys.exit(1)

        print("\n" + "="*60)
        print("  MacroSnaps - Apply Metric Stories")
        print("="*60)
        apply_draft(approved_file, data)
        return

    print("\n" + "="*60)
    print("  MacroSnaps - Draft Metric Stories")
    print(f"  {TODAY}")
    print("="*60)
    print(f"\n  12 parallel Haiku calls (1 country each)\n")

    client  = get_client()
    t0      = time.time()
    draft   = generate_draft(client, data)
    elapsed = int(time.time() - t0)
    filename = save_draft(draft)

    succeeded = len(COUNTRY_ORDER) - len(draft["_failures"])
    print(f"\n{'='*60}")
    print(f"  Done: {succeeded}/{len(COUNTRY_ORDER)} countries in {elapsed}s")
    if draft["_failures"]:
        print(f"  Failures: {', '.join(draft['_failures'])}")
    print(f"  Saved: {filename}")
    print(f"\n  Next steps:")
    print(f"  1. Open metric_story_review.html and load {filename}")
    print(f"  2. Review, edit, approve, export METRICS_approved_{TODAY}.json")
    print(f"  3. python3 update_metric_stories.py --apply METRICS_approved_{TODAY}.json")
    print(f"  4. python3 build.py\n")


if __name__ == "__main__":
    main()
