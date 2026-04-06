#!/usr/bin/env python3
"""
patch_shell_alignment.py
=========================
Replaces the right-align logic in macrosnaps-shell.html with left-align-
from-startDate in both hasChartData() and renderMetricChart().

The commodity chart (renderCommodityMonthlyChart) uses live spark data
and is intentionally left unchanged.

Run from the macrosnaps repo directory:
    python3 ~/Downloads/patch_shell_alignment.py
"""

import sys, os

SHELL_FILE = "macrosnaps-shell.html"

if not os.path.exists(SHELL_FILE):
    print(f"FATAL: {SHELL_FILE} not found. Run from the macrosnaps repo directory.")
    sys.exit(1)

with open(SHELL_FILE, "r", encoding="utf-8") as f:
    html = f.read()

changes = 0

# ── Patch 1: hasChartData() ──────────────────────────────────────────────────
# Single-line right-align used purely to test for any non-null value.
# Behaviour is identical under left-alignment (same non-null elements).

OLD_HAS = (
    "  const padded=totalLen>rawVals.length"
    "?Array(totalLen-rawVals.length).fill(null).concat(rawVals)"
    ":rawVals.slice(rawVals.length-totalLen);\n"
    "  return padded.some(v=>v!==null&&v!==undefined);"
)
NEW_HAS = (
    "  // Left-align from startDate when present; fall back to right-align for\n"
    "  // series without startDate (e.g. annual). Non-null check is alignment-invariant.\n"
    "  let padded;\n"
    "  if(!isAnnual && cfg.startDate){\n"
    "    const [sy,sm]=cfg.startDate.split('-').map(Number);\n"
    "    const startIdx=(sy-2000)*12+(sm-1);\n"
    "    const trail=Math.max(0,totalLen-startIdx-rawVals.length);\n"
    "    padded=Array(startIdx).fill(null).concat(rawVals).concat(Array(trail).fill(null));\n"
    "  } else {\n"
    "    padded=totalLen>rawVals.length\n"
    "      ?Array(totalLen-rawVals.length).fill(null).concat(rawVals)\n"
    "      :rawVals.slice(rawVals.length-totalLen);\n"
    "  }\n"
    "  return padded.some(v=>v!==null&&v!==undefined);"
)

if OLD_HAS in html:
    html = html.replace(OLD_HAS, NEW_HAS, 1)
    changes += 1
    print("  Patch 1 applied: hasChartData() alignment updated.")
else:
    print("  WARN: Patch 1 target not found in hasChartData() — already patched or source changed.")

# ── Patch 2: renderMetricChart() ─────────────────────────────────────────────
OLD_RENDER = (
    "  // Fixed window: Jan 2000 → current month/year. Right-align data into the full label\n"
    "  // range, left-padding with nulls so gaps are visible rather than the axis shrinking.\n"
    "  const totalLen=allLabels.length;\n"
    "  const padded=totalLen>rawVals.length\n"
    "    ?Array(totalLen-rawVals.length).fill(null).concat(rawVals)\n"
    "    :rawVals.slice(rawVals.length-totalLen);"
)
NEW_RENDER = (
    "  // Fixed window: Jan 2000 → current month/year.\n"
    "  // Left-align from cfg.startDate so frozen series (e.g. Inflation) render at the\n"
    "  // correct historical dates regardless of array length or build date.\n"
    "  // Live series whose startDate equals their genuine FRED start align identically\n"
    "  // to the previous right-align behaviour. Trailing nulls appear as a visible gap\n"
    "  // for months after the freeze — honest representation of data staleness.\n"
    "  const totalLen=allLabels.length;\n"
    "  let padded;\n"
    "  if(!isAnnual && cfg.startDate){\n"
    "    const [sy,sm]=cfg.startDate.split('-').map(Number);\n"
    "    const startIdx=(sy-2000)*12+(sm-1);\n"
    "    const trail=Math.max(0,totalLen-startIdx-rawVals.length);\n"
    "    padded=Array(startIdx).fill(null).concat(rawVals).concat(Array(trail).fill(null));\n"
    "  } else {\n"
    "    padded=totalLen>rawVals.length\n"
    "      ?Array(totalLen-rawVals.length).fill(null).concat(rawVals)\n"
    "      :rawVals.slice(rawVals.length-totalLen);\n"
    "  }"
)

if OLD_RENDER in html:
    html = html.replace(OLD_RENDER, NEW_RENDER, 1)
    changes += 1
    print("  Patch 2 applied: renderMetricChart() alignment updated.")
else:
    print("  WARN: Patch 2 target not found in renderMetricChart() — already patched or source changed.")

if changes == 0:
    print("\n  No changes made. Exiting without writing.")
    sys.exit(0)

with open(SHELL_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n  Written: {SHELL_FILE} ({changes}/2 patches applied)")
print("\n  Done. Run build.py to rebuild and verify.\n")
