#!/usr/bin/env python3
"""
audit_sheets.py — Read-only audit of MARKET-STATS and MACRO-MONTHLY sheets.
Prints last date per series and flags anything stale (>90 days) or blank.

Usage:
    python3 audit_sheets.py

Auth: market-stats-key.json (same directory)
Env:  MACRO_MONTHLY_SHEET_ID (for MACRO-MONTHLY sheet)
"""

import os
import sys
from datetime import datetime, date, timedelta

import gspread
from google.oauth2.service_account import Credentials

# ── Config ────────────────────────────────────────────────────────────────────

MARKET_STATS_ID   = "1tL0BkihqRC0JHW0H43ZEfeU2-MS9Swu8F6xxwddUDKI"
MACRO_MONTHLY_ID  = os.environ.get("MACRO_MONTHLY_SHEET_ID", "")
KEY_FILE          = "market-stats-key.json"
STALE_DAYS        = 90  # flag if last data point is older than this

COUNTRIES = ["USA", "CAN", "GBR", "JPN", "DEU", "FRA", "ITA", "CHN", "IND", "ZAF", "BRA", "RUS"]

MARKET_TABS    = COUNTRIES  # one tab per country code
MARKET_COLS    = ["Stock_Market_Index", "FX_Rate", "Bond_Yield_10Y", "Yield_Curve", "Stock_Market_YTD_USD"]
COMMODITY_COLS = ["WTI Crude", "Brent Crude", "Natural Gas", "Gold", "Silver", "Copper", "Wheat", "Corn", "Soybeans"]

MACRO_TABS     = ["Inflation", "Unemployment", "Policy_Rate"]

TODAY = date.today()

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds  = Credentials.from_service_account_file(KEY_FILE, scopes=scopes)
    return gspread.authorize(creds)

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_date(val):
    """Try to parse a cell value as a date. Returns date or None."""
    if not val or str(val).strip() == "":
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def age_str(d):
    """Return human-readable age string."""
    if d is None:
        return "—"
    delta = (TODAY - d).days
    if delta < 0:
        return f"future ({d})"
    if delta == 0:
        return "today"
    if delta == 1:
        return "yesterday"
    if delta < 32:
        return f"{delta}d ago"
    months = round(delta / 30.4)
    return f"~{months}mo ago"

def flag(d, expected_days=STALE_DAYS):
    """Return a status flag character."""
    if d is None:
        return "✗ BLANK"
    delta = (TODAY - d).days
    if delta > expected_days:
        return "⚠ STALE"
    return "✓"

def last_non_null(col_values):
    """Return (last_date, last_value) for the last non-empty cell in a column."""
    last_date = None
    for row in reversed(col_values):
        val = str(row).strip()
        if val not in ("", "None", "N/A", "#N/A"):
            d = parse_date(val)
            if d:
                return d
    return None

def get_all_values_with_header(ws):
    """Return (headers, rows) where rows is list of dicts."""
    all_vals = ws.get_all_values()
    if not all_vals:
        return [], []
    headers = all_vals[0]
    rows    = all_vals[1:]
    return headers, rows

def col_index(headers, name):
    """Return index of a column name (case-insensitive), or None."""
    name_l = name.lower()
    for i, h in enumerate(headers):
        if h.strip().lower() == name_l:
            return i
    return None

# ── Formatting ────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
DIM    = "\033[2m"

def colour(text, status):
    if "BLANK" in status:
        return RED + text + RESET
    if "STALE" in status:
        return YELLOW + text + RESET
    return GREEN + text + RESET

def print_header(title):
    print()
    print(BOLD + "═" * 72 + RESET)
    print(BOLD + f"  {title}" + RESET)
    print(BOLD + "═" * 72 + RESET)

def print_subheader(title):
    print()
    print(BOLD + f"  ── {title}" + RESET)

def row_fmt(label, d, status, width=28):
    label_str = f"    {label:<{width}}"
    date_str  = str(d) if d else "—"
    age       = age_str(d)
    flag_str  = colour(status, status)
    return f"{label_str}  {date_str}  ({age})  {flag_str}"

# ── MARKET-STATS audit ────────────────────────────────────────────────────────

def audit_market_stats(gc):
    print_header("MARKET-STATS — Country Tabs")
    sh = gc.open_by_key(MARKET_STATS_ID)

    issues = []

    for country in MARKET_TABS:
        try:
            ws = sh.worksheet(country)
        except gspread.exceptions.WorksheetNotFound:
            print(f"    {RED}{country}: tab not found{RESET}")
            issues.append((country, "TAB MISSING", None))
            continue

        headers, rows = get_all_values_with_header(ws)
        print_subheader(country)

        date_col_idx = col_index(headers, "Date")
        if date_col_idx is None:
            print(f"    {RED}No Date column found{RESET}")
            continue

        # Build per-column last-date
        for col_name in MARKET_COLS:
            idx = col_index(headers, col_name)
            if idx is None:
                status = "✗ BLANK"
                print(row_fmt(col_name, None, status))
                issues.append((country, col_name, None))
                continue

            # Find last row where this column is non-empty, and get its date
            last_d = None
            for row in reversed(rows):
                val = row[idx] if idx < len(row) else ""
                if str(val).strip() not in ("", "None", "N/A", "#N/A"):
                    date_val = row[date_col_idx] if date_col_idx < len(row) else ""
                    last_d = parse_date(date_val)
                    break

            status = flag(last_d)
            print(row_fmt(col_name, last_d, status))
            if "✓" not in status:
                issues.append((country, col_name, last_d))

    # Commodities tab
    print_header("MARKET-STATS — Commodities Tab")
    try:
        ws = sh.worksheet("Commodities")
        headers, rows = get_all_values_with_header(ws)
        date_col_idx  = col_index(headers, "Date")

        for col_name in COMMODITY_COLS:
            idx = col_index(headers, col_name)
            if idx is None:
                status = "✗ BLANK"
                print(row_fmt(col_name, None, status))
                issues.append(("Commodities", col_name, None))
                continue

            last_d = None
            for row in reversed(rows):
                val = row[idx] if idx < len(row) else ""
                if str(val).strip() not in ("", "None", "N/A", "#N/A"):
                    date_val = row[date_col_idx] if date_col_idx < len(row) else ""
                    last_d = parse_date(date_val)
                    break

            status = flag(last_d)
            print(row_fmt(col_name, last_d, status))
            if "✓" not in status:
                issues.append(("Commodities", col_name, last_d))

    except gspread.exceptions.WorksheetNotFound:
        print(f"    {RED}Commodities tab not found{RESET}")

    return issues

# ── MACRO-MONTHLY audit ───────────────────────────────────────────────────────

def audit_macro_monthly(gc):
    print_header("MACRO-MONTHLY — All Tabs")

    if not MACRO_MONTHLY_ID:
        print(f"    {RED}MACRO_MONTHLY_SHEET_ID env var not set — skipping{RESET}")
        return []

    sh = gc.open_by_key(MACRO_MONTHLY_ID)
    issues = []

    for tab_name in MACRO_TABS:
        print_subheader(tab_name)
        try:
            ws = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"    {RED}{tab_name}: tab not found{RESET}")
            issues.append((tab_name, "TAB MISSING", None))
            continue

        headers, rows = get_all_values_with_header(ws)
        date_col_idx  = col_index(headers, "Date")

        if date_col_idx is None:
            print(f"    {RED}No Date column found{RESET}")
            continue

        for country in COUNTRIES:
            idx = col_index(headers, country)
            if idx is None:
                print(row_fmt(country, None, "✗ BLANK"))
                issues.append((tab_name, country, None))
                continue

            # Find last non-null value and its date
            last_d = None
            for row in reversed(rows):
                val = row[idx] if idx < len(row) else ""
                if str(val).strip() not in ("", "None", "N/A", "#N/A"):
                    date_val = row[date_col_idx] if date_col_idx < len(row) else ""
                    last_d = parse_date(date_val)
                    break

            # MACRO-MONTHLY is updated monthly — allow up to 90 days stale
            status = flag(last_d, expected_days=90)

            # Known permanent gaps — downgrade stale warning to dim note
            known_blank = (
                (tab_name == "Unemployment" and country in ("CHN", "IND", "ZAF", "BRA", "RUS")) or
                (tab_name == "Policy_Rate"  and country == "CHN")
            )
            if known_blank and last_d is None:
                label_str = f"    {country:<28}"
                print(f"{label_str}  —  (known permanent gap)  {DIM}—{RESET}")
                continue

            print(row_fmt(country, last_d, status))
            if "✓" not in status:
                issues.append((tab_name, country, last_d))

    return issues

# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(market_issues, monthly_issues):
    all_issues = market_issues + monthly_issues
    print_header("SUMMARY")

    if not all_issues:
        print(f"    {GREEN}All series current. No gaps detected.{RESET}")
        return

    print(f"    {len(all_issues)} issue(s) found:\n")
    for (loc, series, d) in all_issues:
        date_str = str(d) if d else "no data"
        age      = age_str(d)
        print(f"    {RED}✗{RESET}  {loc:<12}  {series:<30}  {date_str}  ({age})")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}MacroSnaps — Sheet Audit{RESET}  {DIM}(read-only, no writes){RESET}")
    print(f"{DIM}Run date: {TODAY}  |  Stale threshold: >{STALE_DAYS} days{RESET}")

    if not os.path.exists(KEY_FILE):
        print(f"\n{RED}Error: {KEY_FILE} not found in current directory.{RESET}")
        sys.exit(1)

    gc = get_client()

    market_issues  = audit_market_stats(gc)
    monthly_issues = audit_macro_monthly(gc)

    print_summary(market_issues, monthly_issues)
    print()

if __name__ == "__main__":
    main()
