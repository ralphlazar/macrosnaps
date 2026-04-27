#!/usr/bin/env python3
"""
patch_metric_stories_unpack.py
==============================
Session 78 hotfix: fix tuple-unpacking bug in update_metric_stories.py
that caused all 12 countries to fail when the Day-8 staleness ceiling
started firing post-Session-76 backfill.

Cause: the validator block was unpacking 4-tuples into 3 vars. Every
other call site already uses the 4-tuple shape; only this one was
missed when the trigger reasons were piggybacked onto to_regen.

Fix: add the missing trailing '_' so the validator unpacks all 4 fields.
Pure surgical change, one line, no other behaviour touched.
"""
import sys
from pathlib import Path

TARGET = Path("update_metric_stories.py")
OLD = "        for _, name, _ in to_regen:"
NEW = "        for _, name, _, _ in to_regen:"

if not TARGET.exists():
    print(f"FATAL: {TARGET} not found in current directory.")
    print("Run from /Users/lisaswerling/RALPH/AI/macrosnaps/")
    sys.exit(1)

text = TARGET.read_text(encoding="utf-8")
count = text.count(OLD)

if count == 0:
    print("No match found. Either already patched, or the line has been edited.")
    print("Aborting safely.")
    sys.exit(1)

if count > 1:
    print(f"Multiple matches ({count}). Aborting to avoid ambiguity.")
    sys.exit(1)

TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
print(f"Patched {TARGET}: validator unpack now matches 4-tuple shape.")
print("Re-run: python3 update_metric_stories.py")
