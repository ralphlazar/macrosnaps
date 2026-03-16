#!/usr/bin/env python3
"""
audit_market_data.py
Audits the MARKET-STATS Google Sheet for each country tab.
Checks: last data point per series, gap count, staleness.
Usage: python3 audit_market_data.py
"""

import csv
import io
import urllib.request
from datetime import datetime, timedelta

SHEET_ID = "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI"
COUNTRIES = ["USA", "GBR", "DEU", "JPN", "FRA", "ITA", "CAN", "CHN", "IND", "BRA", "RUS", "ZAF"]
COLUMNS = ["Stock_Market_Index", "FX_Rate", "Bond_Yield_10Y", "Bond_Yield_3M", "Yield_Curve", "Stock_Market_YTD_USD"]
STALE_DAYS = 5  # flag if last value is older than this many business days

def fetch_tab(country):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={country}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        return None

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def audit_column(rows, col):
    values = [r.get(col, "").strip() for r in rows]
    total = len(values)
    gaps = sum(1 for v in values if v == "")
    # find last non-empty value and its date
    last_val = None
    last_date = None
    for r in reversed(rows):
        v = r.get(col, "").strip()
        if v:
            last_val = v
            last_date = r.get("Date", "").strip()
            break
    return {"total": total, "gaps": gaps, "last_val": last_val, "last_date": last_date}

def is_stale(date_str, stale_days=STALE_DAYS):
    if not date_str:
        return True
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        # count business days between last date and today
        today = datetime.today()
        delta = (today - d).days
        # rough: stale if more than stale_days + 2 (for weekends)
        return delta > stale_days + 2
    except:
        return True

def flag(result):
    if result["last_val"] is None:
        return "❌ EMPTY"
    if is_stale(result["last_date"]):
        return f"⚠️  STALE ({result['last_date']})"
    return f"✅ {result['last_date']}"

def print_report(country, rows, error=None):
    print(f"\n{'─'*60}")
    print(f"  {country}  ({len(rows)} rows)" if rows else f"  {country}")
    print(f"{'─'*60}")
    if error:
        print(f"  ❌ FETCH ERROR: {error}")
        return
    if not rows:
        print("  ❌ No data")
        return
    first_date = rows[0].get("Date", "?")
    last_date  = rows[-1].get("Date", "?")
    print(f"  Date range : {first_date} → {last_date}")
    print()
    col_w = max(len(c) for c in COLUMNS) + 2
    print(f"  {'Series':<{col_w}} {'Gaps':>6}  {'Last value':>14}  Status")
    print(f"  {'-'*col_w} {'------':>6}  {'-'*14}  ------")
    for col in COLUMNS:
        r = audit_column(rows, col)
        gap_pct = f"{r['gaps']}/{r['total']}"
        last = r["last_val"] if r["last_val"] else "—"
        status = flag(r)
        print(f"  {col:<{col_w}} {gap_pct:>6}  {last:>14}  {status}")

def main():
    print("MacroSnaps — MARKET-STATS audit")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Stale threshold: >{STALE_DAYS} business days since last value\n")

    summary_stale = []
    summary_empty = []

    for country in COUNTRIES:
        text = fetch_tab(country)
        if text is None:
            print_report(country, [], error="could not fetch tab")
            continue
        try:
            rows = parse_csv(text)
        except Exception as e:
            print_report(country, [], error=str(e))
            continue

        print_report(country, rows)

        # collect summary flags
        for col in COLUMNS:
            r = audit_column(rows, col)
            if r["last_val"] is None:
                summary_empty.append(f"{country}.{col}")
            elif is_stale(r["last_date"]):
                summary_stale.append(f"{country}.{col} (last: {r['last_date']})")

    print(f"\n{'═'*60}")
    print("  SUMMARY")
    print(f"{'═'*60}")
    if summary_empty:
        print(f"\n  ❌ Empty series ({len(summary_empty)}):")
        for s in summary_empty:
            print(f"     {s}")
    else:
        print("\n  ❌ Empty series: none")

    if summary_stale:
        print(f"\n  ⚠️  Stale series ({len(summary_stale)}):")
        for s in summary_stale:
            print(f"     {s}")
    else:
        print("\n  ⚠️  Stale series: none")

    print()

if __name__ == "__main__":
    main()
