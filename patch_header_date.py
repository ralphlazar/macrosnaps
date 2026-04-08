#!/usr/bin/env python3
"""
Patch macrosnaps-shell.html so the top-left "Updated" date always
shows today's date in GMT (read from the browser clock, not from
data._meta.generated which can be stale).
"""

import sys

SHELL = '/Users/lisaswerling/RALPH/AI/macrosnaps/macrosnaps-shell.html'

OLD = """    // Set header "Updated DD Mon YYYY" from _meta.generated.
    (function() {
      const genStr = data._meta && data._meta.generated;
      if (genStr) {
        const d = new Date(genStr);
        const label = d.toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric'});
        const el = document.getElementById('headerUpdated');
        if (el) el.textContent = 'Updated ' + label;
      }
    })();"""

NEW = """    // Set header "Updated DD Mon YYYY" — always today's date in GMT.
    // Using the browser clock (UTC) so the site never looks stale,
    // regardless of when build.py last ran.
    (function() {
      const label = new Date().toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
      const el = document.getElementById('headerUpdated');
      if (el) el.textContent = 'Updated ' + label;
    })();"""

with open(SHELL, 'r', encoding='utf-8') as f:
    content = f.read()

if OLD not in content:
    print('ERROR: target block not found — shell may have changed.')
    sys.exit(1)

patched = content.replace(OLD, NEW, 1)

with open(SHELL, 'w', encoding='utf-8') as f:
    f.write(patched)

print('Done. macrosnaps-shell.html patched.')
