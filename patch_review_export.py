import re, shutil, sys
from pathlib import Path

REPO = Path('/Users/lisaswerling/RALPH/AI/macrosnaps')

# ── headline_review.html ──────────────────────────────────────────────────

HEADLINE_OLD = '''// ── Export ───────────────────────────────────────────────────────────────────
function exportApproved() {
  saveEditsFromDom();

  const approvedKeys = Object.keys(approved);
  if (approvedKeys.length === 0) {
    showToast('Nothing approved yet.');
    return;
  }

  const out = { date: draft.date || new Date().toISOString().slice(0,10), countries: {}, globalStories: null };

  for (const key of approvedKeys) {
    if (key === 'GLOBAL') {
      const d = editedData['GLOBAL'];
      function toArr(s){ return s.split('\\n').map(l=>l.trim()).filter(Boolean); }
        out.globalStories = {
        beginner: d.beginner.map(x=>({...x, bullets: toArr(x.body), body: undefined})),
        moderate: d.moderate.map(x=>({...x, bullets: toArr(x.body), body: undefined})),
        expert:   d.expert.map(x=>({...x, bullets: toArr(x.body), body: undefined}))
      };
      // sources excluded from apply file (stay in draft for reference only)
    } else {
      const d = editedData[key];
      out.countries[key] = {
        stories: {
          beginner: d.beginner,
          moderate: d.moderate,
          expert:   d.expert
        }
      };
    }
  }

  // Remove null globalStories if not approved
  if (!out.globalStories) delete out.globalStories;

  const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `HEADLINES_approved_${out.date}.json`;
  a.click();
  URL.revokeObjectURL(url);

  showToast(`Exported ${approvedKeys.length} approved items.`);
}'''

HEADLINE_NEW = '''// ── Export ───────────────────────────────────────────────────────────────────
async function exportApproved() {
  saveEditsFromDom();

  const approvedKeys = Object.keys(approved);
  if (approvedKeys.length === 0) {
    showToast('Nothing approved yet.');
    return;
  }

  const out = { date: draft.date || new Date().toISOString().slice(0,10), countries: {}, globalStories: null };

  for (const key of approvedKeys) {
    if (key === 'GLOBAL') {
      const d = editedData['GLOBAL'];
      function toArr(s){ return s.split('\\n').map(l=>l.trim()).filter(Boolean); }
        out.globalStories = {
        beginner: d.beginner.map(x=>({...x, bullets: toArr(x.body), body: undefined})),
        moderate: d.moderate.map(x=>({...x, bullets: toArr(x.body), body: undefined})),
        expert:   d.expert.map(x=>({...x, bullets: toArr(x.body), body: undefined}))
      };
      // sources excluded from apply file (stay in draft for reference only)
    } else {
      const d = editedData[key];
      out.countries[key] = {
        stories: {
          beginner: d.beginner,
          moderate: d.moderate,
          expert:   d.expert
        }
      };
    }
  }

  // Remove null globalStories if not approved
  if (!out.globalStories) delete out.globalStories;

  const json = JSON.stringify(out, null, 2);
  const filename = `HEADLINES_approved_${out.date}.json`;

  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{ description: 'JSON', accept: { 'application/json': ['.json'] } }]
      });
      const writable = await handle.createWritable();
      await writable.write(json);
      await writable.close();
      showToast(`Saved ${approvedKeys.length} approved items.`);
      return;
    } catch (err) {
      if (err.name === 'AbortError') return;
      // fall through to legacy download on unexpected error
    }
  }

  // Fallback for browsers without File System Access API
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`Exported ${approvedKeys.length} approved items.`);
}'''

# ── metric_story_review.html ──────────────────────────────────────────────

METRIC_OLD = '''// ── Export approved ────────────────────────────────────────────────────────
function exportApproved() {
  if (!draft) return;
  const approved = {
    date:         draft.date,
    generated_at: draft.generated_at,
    approved_at:  new Date().toISOString().slice(0,16).replace('T',' '),
    countries:    edited
  };
  const blob = new Blob([JSON.stringify(approved, null, 2)], {type:'application/json'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  const dateStr = draft.date || new Date().toISOString().slice(0,10);
  a.href     = url;
  a.download = `METRICS_approved_${dateStr}.json`;
  a.click();
  URL.revokeObjectURL(url);
  toast('Exported METRICS_approved_' + dateStr + '.json');
}'''

METRIC_NEW = '''// ── Export approved ────────────────────────────────────────────────────────
async function exportApproved() {
  if (!draft) return;
  const approved = {
    date:         draft.date,
    generated_at: draft.generated_at,
    approved_at:  new Date().toISOString().slice(0,16).replace('T',' '),
    countries:    edited
  };
  const json    = JSON.stringify(approved, null, 2);
  const dateStr = draft.date || new Date().toISOString().slice(0,10);
  const filename = `METRICS_approved_${dateStr}.json`;

  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{ description: 'JSON', accept: { 'application/json': ['.json'] } }]
      });
      const writable = await handle.createWritable();
      await writable.write(json);
      await writable.close();
      toast('Saved METRICS_approved_' + dateStr + '.json');
      return;
    } catch (err) {
      if (err.name === 'AbortError') return;
      // fall through to legacy download on unexpected error
    }
  }

  // Fallback for browsers without File System Access API
  const blob = new Blob([json], {type:'application/json'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  toast('Exported METRICS_approved_' + dateStr + '.json');
}'''

def patch(filepath, old, new, label):
    text = filepath.read_text()
    if old not in text:
        print(f'ERROR: target block not found in {label}')
        sys.exit(1)
    patched = text.replace(old, new, 1)
    filepath.write_text(patched)
    print(f'Patched {label}')

h = REPO / 'headline_review.html'
m = REPO / 'metric_story_review.html'

patch(h, HEADLINE_OLD, HEADLINE_NEW, 'headline_review.html')
patch(m, METRIC_OLD,   METRIC_NEW,   'metric_story_review.html')

print('Done.')
