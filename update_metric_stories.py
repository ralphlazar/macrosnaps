#!/usr/bin/env python3
"""
update_metric_stories.py
========================
Drafts fresh 3-bullet metric stories ONLY for metrics that need regenerating.
Triggers per metric (any one fires regen):
  1. New monthly print arrived since last regen (Inflation, Unemployment, Policy Rate)
  2. Daily-tier value moved >= 5% relative to story snapshot (markets)
  3. Story is older than the tier ceiling (daily=7d, weekly=14d, structural=30d)
Anything not triggered is carried forward (zero API cost).

Architecture:
  - Reads harvest_{TODAY}.json produced by update_headlines.py
  - Per country, splits metrics into to-regen vs carry-forward
  - 12 parallel Haiku calls (only metrics that need regen, per country)
  - Saves METRICS_draft_{TODAY}.json with _regenerated flags for the review UI
  - Apply step writes approved bullets back into data.json AND stamps
    story_last_updated / story_value_snapshot / story_last_print_month

Usage:
    python3 update_metric_stories.py                          # trigger-based draft
    python3 update_metric_stories.py --force-all              # ignore triggers, regen everything
    python3 update_metric_stories.py --apply                  # apply most recent approved
    python3 update_metric_stories.py --apply METRICS_approved_2026-04-25.json

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
TODAY_D   = date.today()
MODEL     = "claude-haiku-4-5-20251001"
LEVELS    = ["beginner", "moderate", "expert"]

COUNTRY_ORDER = [
    "USA","CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"
]

# ── Trigger configuration ────────────────────────────────────────────────────

# Which metrics correspond to monthly_actuals keys (for new-print detection)
MONTHLY_ACTUAL_KEY = {
    "Inflation (CPI)": "inflation",
    "Unemployment":    "unemployment",
    "Policy Rate":     "policy_rate",
}

# Staleness ceiling per tier (days)
STALENESS_DAYS = {
    "daily":      7,
    "weekly":     14,
    "structural": 30,
}
DEFAULT_STALENESS = 14

# Move threshold for daily-tier metrics (relative %, computed vs snapshot)
MOVE_THRESHOLD_PCT = 5.0

# ── Editorial config ─────────────────────────────────────────────────────────

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


# ── Utility ──────────────────────────────────────────────────────────────────

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


# ── Trigger logic ────────────────────────────────────────────────────────────

def parse_numeric(v):
    """Extract a float from strings like '+4.2%', '-5.1%', '4.30%', '+69bps', '98.7', '-3.7% GDP'."""
    if v is None: return None
    s = str(v).strip()
    for token in ("%", "bps", "GDP", "+", " "):
        s = s.replace(token, "")
    try:
        return float(s)
    except ValueError:
        return None


def relative_move(snap, cur):
    """Relative % change. Uses max(|snap|, 1.0) as denominator to avoid blow-ups near zero."""
    if snap is None or cur is None:
        return None
    denom = max(abs(snap), 1.0)
    return abs(cur - snap) / denom * 100.0


def should_regenerate(country_data, name, mdata, today):
    """
    Decide whether to regenerate a metric story.
    Returns (regen: bool, reason: str).
    """
    # Trigger 0: never had a story stamp before
    story_last = mdata.get("story_last_updated")
    if not story_last:
        return True, "first run"

    try:
        last_dt  = datetime.strptime(story_last, "%Y-%m-%d").date()
        days_old = (today - last_dt).days
    except Exception:
        return True, f"invalid story_last_updated ({story_last})"

    tier    = mdata.get("tier", "weekly")
    ceiling = STALENESS_DAYS.get(tier, DEFAULT_STALENESS)

    # Trigger 1: new monthly print
    monthly_key = MONTHLY_ACTUAL_KEY.get(name)
    if monthly_key:
        ma = country_data.get("monthly_actuals", {}).get(monthly_key, [])
        if isinstance(ma, list) and ma:
            latest_month = ma[0].get("month") if isinstance(ma[0], dict) else None
            snap_month   = mdata.get("story_last_print_month")
            if latest_month and latest_month != snap_month:
                return True, f"new print {latest_month}"

    # Trigger 2: market move (daily tier only)
    if tier == "daily":
        snap = parse_numeric(mdata.get("story_value_snapshot"))
        cur  = parse_numeric(mdata.get("value"))
        pct  = relative_move(snap, cur)
        if pct is not None and pct >= MOVE_THRESHOLD_PCT:
            return True, f"moved {pct:.1f}%"

    # Trigger 3: staleness
    if days_old >= ceiling:
        return True, f"stale {days_old}d (>={ceiling}d)"

    return False, f"fresh {days_old}d"


# ── Prompt construction ──────────────────────────────────────────────────────

def build_country_prompt(code, country_data, to_regen, recent_data):
    """
    to_regen: list of (section, name, value) tuples for metrics that need regeneration.
    Asks Haiku for ONLY these metrics.
    """
    lines = [
        f"Today is {TODAY}.",
        "",
        f"Write 3-bullet metric stories for {country_data.get('name', code)} ({code}).",
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
        recent_data.get(code, "Use your knowledge of current conditions."),
        "",
        "Metrics to write (with current values):",
        "",
    ]
    for section, name, value in to_regen:
        lines.append(f"  [{section}] {name}: {value}")
    lines += [
        "",
        "BULLET COUNT RULE: EVERY level for EVERY metric listed above must have EXACTLY 3 bullets.",
        "",
        f"Output ONLY a JSON object with this shape (one key per metric listed above), no preamble, no markdown fences:",
        '{',
    ]
    for i, (_, name, _) in enumerate(to_regen):
        comma = "," if i < len(to_regen) - 1 else ""
        lines.append(f'  "{name}": {{')
        lines.append(f'    "beginner": ["bullet 1", "bullet 2", "bullet 3"],')
        lines.append(f'    "moderate": ["bullet 1", "bullet 2", "bullet 3"],')
        lines.append(f'    "expert":   ["bullet 1", "bullet 2", "bullet 3"]')
        lines.append(f'  }}{comma}')
    lines += [
        '}',
        "",
        "Use the exact metric names as shown above. Use straight apostrophes only.",
    ]
    return "\n".join(lines)


# ── Per-country batch ────────────────────────────────────────────────────────

def carry_forward_bullets(country_data, section, name):
    """Pull existing story bullets verbatim from data.json so the review UI shows them in context."""
    mdata = country_data.get("metrics", {}).get(section, {}).get(name, {})
    story = mdata.get("story", {})
    out = {}
    for lv in LEVELS:
        v = story.get(lv, [])
        out[lv] = list(v) if isinstance(v, list) else ["", "", ""]
        while len(out[lv]) < 3:
            out[lv].append("")
    return out


def draft_country(client, code, country_data, recent_data, label, force_all):
    """Run trigger logic for one country; call Haiku only if any metric needs regen."""
    decisions = []  # list of (section, name, value, regen, reason)
    metrics_dict = country_data.get("metrics", {})

    for section, name, value in get_country_metrics(country_data):
        mdata = metrics_dict.get(section, {}).get(name, {})
        if force_all:
            regen, reason = True, "force-all"
        else:
            regen, reason = should_regenerate(country_data, name, mdata, TODAY_D)
        decisions.append((section, name, value, regen, reason))

    to_regen = [(s, n, v, r) for (s, n, v, regen, r) in decisions if regen]
    total    = len(decisions)

    # Assemble payload skeleton: every metric appears, regen ones get fresh bullets later
    metric_payload = {}
    for section, name, value, regen, reason in decisions:
        bullets = carry_forward_bullets(country_data, section, name)
        metric_payload[name] = {
            "beginner": bullets["beginner"],
            "moderate": bullets["moderate"],
            "expert":   bullets["expert"],
            "_section":         section,
            "_value":           value,
            "_regenerated":     regen,
            "_trigger_reason":  reason,
        }

    if not to_regen:
        print(f"  [BATCH {label}] {code}: 0/{total} regen, all carried forward")
        return code, metric_payload, None

    reasons_summary = ", ".join(sorted(set(r for _,_,_,r in to_regen)))
    print(f"  [BATCH {label}] {code}: {len(to_regen)}/{total} regen [{reasons_summary}]...",
          end=" ", flush=True)

    prompt = build_country_prompt(code, country_data, [(s,n,v) for (s,n,v,_) in to_regen], recent_data)

    parsed = None
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
        except Exception as e:
            print(f"FAILED ({e})")
            return code, metric_payload, str(e)

        try:
            parsed = extract_json(response.content[0].text)
        except Exception as e:
            if attempt == 0:
                print(f"(parse failed, retry...)", end=" ", flush=True)
                time.sleep(2)
                continue
            print(f"PARSE FAILED ({e})")
            return code, metric_payload, f"parse: {e}"

        # Validate: each requested metric must have 3 bullets per level
        problems = []
        for _, name, _, _ in to_regen:
            if name not in parsed:
                problems.append(f"missing: {name}")
                continue
            for lv in LEVELS:
                bullets = parsed[name].get(lv, [])
                if not isinstance(bullets, list) or len(bullets) < 3:
                    got = len(bullets) if isinstance(bullets, list) else 0
                    problems.append(f"{name}/{lv}: {got} bullets")

        if not problems:
            break

        if attempt == 0:
            print(f"({len(problems)} problems, retry...)", end=" ", flush=True)
            time.sleep(3)
        else:
            print(f"PARTIAL ({len(problems)} problems)")
            for p in problems[:3]:
                print(f"    {p}")

    # Splice fresh bullets into payload for metrics that came back valid
    for section, name, value, regen, reason in decisions:
        if not regen:
            continue
        if parsed and name in parsed:
            entry = parsed[name]
            for lv in LEVELS:
                bullets = entry.get(lv, [])
                if isinstance(bullets, list) and len(bullets) >= 3:
                    metric_payload[name][lv] = bullets[:3]
        else:
            # Failed to regen this metric; downgrade to carry-forward
            metric_payload[name]["_regenerated"]    = False
            metric_payload[name]["_trigger_reason"] = f"{reason} [API miss, carried forward]"

    print("OK")
    return code, metric_payload, None


# ── Draft assembly ───────────────────────────────────────────────────────────

def generate_draft(client, data, force_all):
    draft = {
        "date":         TODAY,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "force_all":    force_all,
        "countries":    {},
        "_failures":    [],
    }
    countries_data = data.get("countries", {})
    recent_data    = load_harvest()

    def run(code_label):
        code, label = code_label
        cd = countries_data.get(code)
        if not cd:
            return code, None, f"missing in data.json"
        try:
            return draft_country(client, code, cd, recent_data, label, force_all)
        except Exception as e:
            return code, None, str(e)

    pairs = [(c, f"{i+1}/12") for i, c in enumerate(COUNTRY_ORDER)]

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(run, p): p for p in pairs}
        for future in as_completed(futures):
            code, payload, error = future.result()
            if error and payload is None:
                print(f"  [{code}] FAILED: {error}")
                draft["_failures"].append(code)
            else:
                draft["countries"][code] = payload

    return draft


def save_draft(draft):
    filename = f"METRICS_draft_{TODAY}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    return filename


def summarize_draft(draft):
    total = regen = carried = 0
    for code, metrics in draft.get("countries", {}).items():
        for name, payload in metrics.items():
            total += 1
            if payload.get("_regenerated"):
                regen += 1
            else:
                carried += 1
    return total, regen, carried


# ── Apply ────────────────────────────────────────────────────────────────────

def apply_draft(approved_file, data):
    print(f"\n  Reading approved draft: {approved_file}")
    with open(approved_file) as f:
        approved = json.load(f)

    applied_levels = applied_metrics = skipped = 0
    countries_data = data.get("countries", {})

    for code, metrics in approved.get("countries", {}).items():
        if code not in countries_data:
            print(f"  [SKIP] {code} not in data.json")
            continue

        country_metric_count = 0
        for section in ("macro", "market"):
            for name, v in countries_data[code].get("metrics", {}).get(section, {}).items():
                if not isinstance(v, dict) or not isinstance(v.get("story"), dict):
                    continue
                if name not in metrics:
                    continue
                payload = metrics[name]
                country_metric_count += 1

                # Skip carried-forward metrics: keep story untouched and freshness fields untouched.
                # This is what makes the staleness counter actually count.
                if payload.get("_regenerated") is False:
                    skipped += 1
                    continue

                # Write fresh bullets
                wrote_any = False
                for lv in LEVELS:
                    if lv in payload and isinstance(payload[lv], list):
                        v["story"][lv] = payload[lv]
                        applied_levels += 1
                        wrote_any = True
                if not wrote_any:
                    continue

                # Stamp freshness
                v["story_last_updated"]   = TODAY
                v["story_value_snapshot"] = v.get("value", "")
                monthly_key = MONTHLY_ACTUAL_KEY.get(name)
                if monthly_key:
                    ma = countries_data[code].get("monthly_actuals", {}).get(monthly_key, [])
                    if isinstance(ma, list) and ma and isinstance(ma[0], dict):
                        latest = ma[0].get("month")
                        if latest:
                            v["story_last_print_month"] = latest
                applied_metrics += 1

        if country_metric_count:
            print(f"  [{code}] Applied.")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    country_count = len(approved.get("countries", {}))
    print(f"\n  Regenerated: {applied_metrics} metrics ({applied_levels} level-slots) across {country_count} countries")
    print(f"  Carried forward (untouched): {skipped} metrics")
    print(f"  data.json updated.")
    print(f"\n  Next step: python3 build.py\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", nargs="?", const="__latest__", metavar="FILE")
    parser.add_argument("--force-all", action="store_true",
                        help="Ignore triggers and regenerate every metric")
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
    print("  MacroSnaps - Draft Metric Stories (trigger-based)")
    print(f"  {TODAY}")
    if args.force_all:
        print("  Mode: --force-all (ignoring triggers)")
    print("="*60)
    print(f"\n  12 parallel Haiku calls (per-country, only metrics needing regen)\n")

    client  = get_client()
    t0      = time.time()
    draft   = generate_draft(client, data, args.force_all)
    elapsed = int(time.time() - t0)
    filename = save_draft(draft)

    total, regen, carried = summarize_draft(draft)
    succeeded = len(COUNTRY_ORDER) - len(draft["_failures"])

    print(f"\n{'='*60}")
    print(f"  Done: {succeeded}/{len(COUNTRY_ORDER)} countries in {elapsed}s")
    print(f"  Metrics: {regen} regenerated, {carried} carried forward (of {total} total)")
    if total:
        savings = carried * 100 // total
        print(f"  Savings: {savings}% of metric work skipped")
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
