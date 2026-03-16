#!/usr/bin/env python3
"""
audit_macro_monthly.py
Audits the MACRO-MONTHLY Google Sheet (Inflation, Unemployment, Policy_Rate tabs).
Countries are columns; dates are rows.
Usage: python3 audit_macro_monthly.py
"""

import csv
import io
import urllib.request
from datetime import datetime

SHEET_ID = "1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI"
TABS = ["Inflation", "Unemployment", "Policy_Rate"]
COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]
STALE_DAYS = 60  # monthly data — flag if last value is older than ~2 months

def fetch_tab(tab):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        return None

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def audit_country(rows, country):
    total = len(rows)
    gaps = 0
    last_val = None
    last_date = None
    first_date = None

    for r in rows:
        v = r.get(country, "").strip()
        date = r.get("Date", "").strip()
        if first_date is None and date:
            first_date = date
        if v == "":
            gaps += 1
        else:
            last_val = v
            last_date = date

    return {
        "total": total,
        "gaps": gaps,
        "last_val": last_val,
        "last_date": last_date,
        "first_date": first_date,
    }

def is_stale(date_str, stale_days=STALE_DAYS):
    if not date_str:
        return True
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.today() - d).days > stale_days
    except:
        return True

def flag(result):
    if result["last_val"] is None:
        return "❌ EMPTY"
    if is_stale(result["last_date"]):
        return f"⚠️  STALE ({result['last_date']})"
    return f"✅ {result['last_date']}"

def print_report(tab, rows, error=None):
    print(f"\n{'═'*65}")
    print(f"  TAB: {tab}  ({len(rows)} rows)" if rows else f"  TAB: {tab}")
    print(f"{'═'*65}")
    if error:
        print(f"  ❌ FETCH ERROR: {error}")
        return
    if not rows:
        print("  ❌ No data")
        return

    first_date = rows[0].get("Date", "?")
    last_date  = rows[-1].get("Date", "?")
    print(f"  Date range : {first_date} → {last_date}\n")

    print(f"  {'Country':<8} {'Gaps':>8}  {'Last value':>12}  Status")
    print(f"  {'-'*8} {'--------':>8}  {'-'*12}  ------")

    stale = []
    empty = []
    for country in COUNTRIES:
        r = audit_country(rows, country)
        gap_str = f"{r['gaps']}/{r['total']}"
        last = r["last_val"] if r["last_val"] else "—"
        status = flag(r)
        print(f"  {country:<8} {gap_str:>8}  {last:>12}  {status}")
        if r["last_val"] is None:
            empty.append(country)
        elif is_stale(r["last_date"]):
            stale.append(f"{country} (last: {r['last_date']})")

    return empty, stale

def main():
    print("MacroSnaps — MACRO-MONTHLY audit")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Stale threshold: >{STALE_DAYS} days since last value\n")

    all_empty = {}
    all_stale = {}

    for tab in TABS:
        text = fetch_tab(tab)
        if text is None:
            print_report(tab, [], error="could not fetch tab")
            all_empty[tab] = ["FETCH ERROR"]
            all_stale[tab] = []
            continue
        try:
            rows = parse_csv(text)
        except Exception as e:
            print_report(tab, [], error=str(e))
            continue

        result = print_report(tab, rows)
        if result:
            all_empty[tab], all_stale[tab] = result

    print(f"\n{'═'*65}")
    print("  SUMMARY")
    print(f"{'═'*65}")
    for tab in TABS:
        empty = all_empty.get(tab, [])
        stale = all_stale.get(tab, [])
        print(f"\n  {tab}:")
        if empty:
            print(f"    ❌ Empty  : {', '.join(empty)}")
        else:
            print(f"    ❌ Empty  : none")
        if stale:
            print(f"    ⚠️  Stale  : {', '.join(stale)}")
        else:
            print(f"    ⚠️  Stale  : none")
    print()

if __name__ == "__main__":
    main()
