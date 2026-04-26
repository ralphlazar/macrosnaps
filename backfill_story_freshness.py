#!/usr/bin/env python3
"""
backfill_story_freshness.py
============================
One-off migration. Stamps every metric story in data.json with:
  - story_last_updated   = today
  - story_value_snapshot = current value
  - story_last_print_month = latest month from monthly_actuals (where applicable)

Run this ONCE before the first trigger-based update_metric_stories.py run.
After this, the natural decay logic takes over.

Usage:
    python3 backfill_story_freshness.py            # dry run, prints what would change
    python3 backfill_story_freshness.py --apply    # writes data.json
"""

import json, sys, argparse
from datetime import date

DATA_FILE = "data.json"
TODAY     = date.today().isoformat()

MONTHLY_ACTUAL_KEY = {
    "Inflation (CPI)": "inflation",
    "Unemployment":    "unemployment",
    "Policy Rate":     "policy_rate",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to data.json")
    args = ap.parse_args()

    with open(DATA_FILE) as f:
        data = json.load(f)

    stamped       = 0
    print_stamped = 0

    for code, cd in data.get("countries", {}).items():
        monthly_actuals = cd.get("monthly_actuals", {})
        for section in ("macro", "market"):
            for name, mdata in cd.get("metrics", {}).get(section, {}).items():
                if not isinstance(mdata, dict):
                    continue
                if not isinstance(mdata.get("story"), dict):
                    continue

                mdata["story_last_updated"]   = TODAY
                mdata["story_value_snapshot"] = mdata.get("value", "")
                stamped += 1

                monthly_key = MONTHLY_ACTUAL_KEY.get(name)
                if monthly_key:
                    ma = monthly_actuals.get(monthly_key, [])
                    if isinstance(ma, list) and ma and isinstance(ma[0], dict):
                        latest = ma[0].get("month")
                        if latest:
                            mdata["story_last_print_month"] = latest
                            print_stamped += 1

    print(f"  Would stamp {stamped} metrics with story_last_updated={TODAY}")
    print(f"  Of those, {print_stamped} got story_last_print_month from monthly_actuals")

    if not args.apply:
        print(f"\n  Dry run. Re-run with --apply to write data.json.")
        return

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  data.json updated.")


if __name__ == "__main__":
    main()
