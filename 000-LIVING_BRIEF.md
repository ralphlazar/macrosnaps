# MacroSnaps - Living Brief
Last updated: May 7, 2026 (Session 80: Daily ritual completed 2026-05-07. morning_bash.sh ran in 4m 36s. 3 commodity rewrites (WTI -5.7%, Brent -11.1%, Silver +8.5%). Headlines 13/13 in 187s. Metric stories: 21 regenerated, 111 carried forward (84% saved), 15s. Build clean, audit clean. Social Media Bash retired permanently from Daily Bash Ritual (section removed from brief). France Stock Market YTD homepage null flagged at session start; today's fetch_market_data.py wrote FRA +1.3% local / +1.47 USD cleanly and the build pushed the fix to the homepage. Root cause not investigated; parked. Several large metric-story trigger moves observed (FRA 130%/147%, ZAF 139%/180%, DEU 50%/62%, JPN 41%/47%) consistent with stale/null snapshots, supporting the FRA observation. 7 FRED bond/yield endpoints returned HTTP 500 (transient); affected fields retain prior day's values. Cosmetic: fetch_market_data.py summary counter undercounts failures (7 actual, says 1).)

Session 80 changes in detail:

(1) **Daily ritual completed 2026-05-07.** Full ritual ran successfully. No Friday pre-ritual (Thursday). morning_bash.sh completed in 4m 36s. 3 commodity rewrites: WTI Crude (moved 5.7%, was 98.53 now 92.93), Brent Crude (moved 11.1%, was 111.5 now 99.11), Silver (moved 8.5%, was 73.83 now 80.08). Headlines 13/13 drafted in 187s. Metric stories: 21 regenerated, 111 carried forward (84% saved), 12/12 countries in 15s. Headline review gate passed. Build successful. Audit: all checks passed.

(2) **Procedural change: Social Media Bash retired permanently from Daily Bash Ritual.** Section removed from this brief. No longer part of the daily sequence. digest_server.py and digest_ui.html remain in the repo as inert artefacts (can be cleaned up in a future tidy-up session if desired).

(3) **France Stock Market YTD homepage null - flagged at session start, self-healed by today's fetch.** Ralph reported the homepage Stock Market YTD ranking showed null for FRA. Today's fetch_market_data.py wrote FRA Stock Market YTD +1.3% local and +1.47 USD cleanly to data.json; values appended successfully to MARKET-STATS sheet. Build pushed the fix to the homepage. Root cause not investigated. Suspicious supporting evidence parked: step 6 (update_metric_stories.py) triggered FRA on 2 metrics with relative moves of 130% and 147%, plus DEU (50%, 62%), JPN (41%, 47%), ZAF (139%, 180%), RUS (80%, 9.8%). Move sizes of this scale are signatures of a snapshot baseline that was null/zero or near-zero. Worth a closer look in a future session if FRA or others go null again. The investigation path would be: pull yesterday's morning_bash log and the previous data.json (via git show on master) to see what FRA looked like 24h ago, identify which 2 FRA metrics tripped the trigger and what their baselines were, then decide whether it is a recurring fetch gap (specific metric occasionally returning null and the snapshot picking up the null) or a one-off.

(4) **FRED HTTP 500 outages on bond/yield endpoints.** During fetch_market_data.py step 1, 7 FRED calls returned HTTP 500: USA DGS10, USA TB3MS, JPN IRLTLT01JPM156N, JPN IR3TIB01JPM156N, FRA ECBDFR, ZAF IRLTLT01ZAM156N, ZAF IRSTCI01ZAM156N. These are transient FRED server issues. Affected fields (USA 10Y, USA Yield Curve, JPN 10Y, JPN Yield Curve, FRA Yield Curve, ZAF 10Y, ZAF Yield Curve) retain previous day's values in data.json. Will likely self-heal next ritual. Not actioned.

(5) **Cosmetic: fetch_market_data.py summary counter undercount.** Per-country output in step 1 shows 7 failed FRED fetches (USA x2, JPN x2, FRA x1, ZAF x2) but the script's end-of-run summary line reads "Updated: 47, Failed: 1". The counter is undercounting failures. Logging-only issue, no impact on data.json. Worth tidying when next touched.

(6) **No code changes this session.** All changes are procedural (Social Media Bash retirement) and observational (FRA flag, FRED 500s, counter cosmetic). No files shipped.

---

Session 79 changes in detail:

(1) **Daily ritual completed 2026-04-29.** Full ritual ran successfully. No Friday pre-ritual (Wednesday). 4 commodity rewrites: WTI Crude (moved 11.4%, was 94.63 now 105.39), Brent Crude (moved 6.0%, was 103.54 now 109.73), Gold (moved 5.9%, was 4837.9 now 4551.0), Wheat (moved 8.1%, was 614.75 now 664.75). Headlines 13/13 drafted in 205s. Metric stories: 20 regenerated, 112 carried forward (84% saved), 12/12 countries in 24s. Headline review gate passed. Build successful, auto-committed and pushed to master. Audit: all checks passed.

(2) **New tooling: morning_bash.sh shipped.** Consolidates pre-review steps 1-6 of the Daily Bash Ritual (fetch_market_data.py, sync_market_historical.py --apply, sync_commodity_data.py --apply, update_commodity_stories.py, update_headlines.py, update_metric_stories.py) into a single script. Replaces the previous step-by-step "paste output, get next command" flow for these six steps. Manual gate (headlines) remains unchanged after the script completes. Apply / build / audit steps remain separate as before.

(3) **morning_bash.sh design choices:**
- `set -e` plus `set -o pipefail` halts on the first non-zero exit code, preventing downstream steps from running on bad data
- Friday-only check: `date +%u` returns 5 on Fridays, prompts "Have you run forecast_server.py and saved forecasts today? (y/n)". Hard exit on "n" with reminder of forecast server commands. Friday check runs before tee redirection so the prompt is direct, no buffering issues.
- Step banners: `===== STEP N/6: description =====` between each step so failures are easy to locate visually
- Logging: `exec > >(tee -a "$LOG") 2>&1` writes all output to both stdout and `logs/morning_bash_YYYY-MM-DD.log`. `mkdir -p logs` ensures the log directory exists.
- Runtime stamp: `SECONDS` counter at start and end, prints total `Xm Ys` at the end (useful for the brief notes)
- Final "next steps" message includes today's date already substituted into the apply commands so no manual YYYY-MM-DD replacement needed
- Script lives at repo root, made executable via `chmod +x`

(4) **First production run successful.** 5m 15s end-to-end, zero errors. All 12 countries appended cleanly to MARKET-STATS sheet on first try (no Google 502 this time, unlike Session 78). Commodities sheet append clean. All draft files written cleanly to repo root.

(5) **Notable Stock Market YTD moves on the day:**
- BRA: +18.1% to +16.2% (-2.64 USD)
- GBR: +4.1% to +2.5% (sterling sold off)
- CAN: +6.1% to +4.6%
- ITA: +6.2% to +5.2%
- RUS: -0.9% to -2.2%
- USA: +4.2% to +4.0%

(6) **Cosmetic flagged for future tidy.** `update_metric_stories.py` end-of-run "Next steps" message still references the retired METRICS_approved convention (`update_metric_stories.py --apply METRICS_approved_2026-04-29.json` plus the metric_story_review.html step). Per Session 78 the apply step takes the draft file directly. Script itself works correctly; only the on-screen instructions are stale. Worth tidying when next touched. Not actioned this session.

(7) **Files shipped this session:**
- `morning_bash.sh` (new): consolidated pre-review ritual script described above. ~90 lines of bash.

(8) **Pipeline integration.** Daily Bash Ritual section in this brief updated to show the new flow: `bash morning_bash.sh` replaces the six individual `python3 ...` commands. Manual headline review gate, apply / build / audit steps, Social Media Bash all unchanged.

---

Session 78 changes in detail:

(1) **Daily ritual completed 2026-04-28.** Full ritual ran successfully. No Friday pre-ritual (Tuesday). 1 commodity story rewrite: Silver (moved 6.4%, was 78.86 now 73.83). Headlines 13/13 drafted in 200s. Metric stories 12/12 countries in 13s. Both review gates (headline_review.html, metric_story_review.html) passed. Build successful, auto-committed and pushed to master. Audit: all checks passed.

(2) **First production run of trigger-based metric story regeneration (Session 76 system).** Of 132 metrics across 12 countries, 17 regenerated and 115 carried forward at zero API cost. Per-country regen counts: USA 0, CAN 1, GBR 2, JPN 2, DEU 2, FRA 2, ITA 2, CHN 2, IND 1, ZAF 2, BRA 0, RUS 1. Several large relative-move flags surfaced (ZAF 111%, FRA 77%, DEU 72%, ZAF 60%, FRA 30%, ITA 26.5%, ITA 14.1%, GBR 13.2%, CHN 12.5%, RUS 11.2%) - these are bps moves on small base values where the relative-change formula `abs(cur - snap) / max(abs(snap), 1.0) * 100` amplifies optically. System working as designed; eyeballed in the review UI without issue. 87% API savings vs the old "regenerate all 132 daily" baseline.

(3) **DEU MARKET-STATS sheet append failure recovered.** First run of fetch_market_data.py: 11/12 countries appended cleanly to MARKET-STATS Google Sheet, DEU returned a Google 502 (`The server encountered a temporary error and could not complete your request.`). data.json itself was fine - DEU values written correctly to data.json - only the historical sheet row for DEU on 2026-04-28 failed to append. Retried at end of ritual by re-running `python3 fetch_market_data.py`; the script's idempotent skip behaviour (checks for today's row already present) appended only the missing rows. Result: DEU appended successfully, plus CHN also appended (suggests CHN had been quietly missing from an earlier session - the retry caught it). Net: 2 appended, 10 skipped, 0 failed.

(4) **Intraday data.json delta after retry left as-is.** The retry of fetch_market_data.py also pulled fresh intraday market values, leaving data.json with small deltas vs the build that had already been pushed to master (e.g. DEU stock -1.7 -> -1.6, GBR +4.1 -> +4.2, ITA +6.2 -> +6.4, EUR/USD 1.1700 -> 1.1693, plus minor commodity moves). Per Ralph's call, no intraday rebuild ran - next daily or intraday ritual will overwrite cleanly. Note for future: the build.py value_at_generation integrity check could trip on these deltas if a build were attempted before another fetch.

(5) **Procedural change: Manual Gate 2 (metric stories review) RETIRED.** Effective immediately, the Daily Bash Ritual no longer includes the metric_story_review.html gate. New sequence: `python3 update_metric_stories.py` (writes METRICS_draft_YYYY-MM-DD.json) -> `python3 update_metric_stories.py --apply METRICS_draft_YYYY-MM-DD.json`. The --apply step takes the draft file directly. No review UI, no copy/rename to "approved". Manual Gate 1 (headlines via headline_review.html) remains in place unchanged. Daily Bash Ritual section below updated to reflect the new sequence.

(6) **No code changes this session.** All changes are procedural. metric_story_review.html and the METRICS_approved file convention remain in the repo as inert artefacts (can be cleaned up in a future tidy-up session if desired).

---

Session 77 changes in detail:

(1) **Bug report.** Homepage Stock Market YTD ranking for USA showed +4.20% local / -3.12% USD on the same day. USD return must equal local return for USA by definition (USA's local currency is USD, so no FX conversion). Visible only on USA because for every other country the spread is real and small enough that staleness is invisible.

(2) **Root cause.** The render layer is fine. Homepage reads `metrics.market['Stock Market YTD'].value` for col1 and `metrics.market['Stock Market YTD (USD)'].value` for col2. The local field refreshes daily via fetch_market_data.py. The USD field was only ever written by `sync_sheet.py --market` which is not in any scheduled ritual. Last sync was 2026-03-22; the field had been silently rotting for five weeks while local YTD updated each day.

(3) **Architectural fix: USD-YTD moved into fetch_market_data.py as a derived metric.** Removes dependency on sync_sheet.py for this field. After the existing FX block in `process_country()`, compute and write `Stock Market YTD (USD)` to `metrics.market[...]['value']` with today's `last_updated` stamp. USA mirrors the parsed value of the local YTD string (e.g. "+4.5%" -> 4.5) to guarantee bit-identical homepage display. All other countries compute compound USD return: `(1 + local%) * (1 + USD-per-local%) - 1`. FX YTD pulled via existing `yf_price_and_ytd()` helper. Direction depends on Yahoo ticker convention: tickers ending `USD=X` (GBPUSD=X, BRLUSD=X, etc) return USD-per-LOCAL directly so raw_ytd is USD-per-local YTD; tickers starting `USD` (USDRUB=X) return LOCAL-per-USD and need inversion via `1/(1 + raw_ytd/100) - 1`. Storage is Python float rounded to 2dp for non-USA, parsed-from-local-string for USA. Format matches what sync_sheet.py was writing so generate_digest.py and other consumers continue to work.

(4) **sync_sheet.py left untouched.** Its `Stock_Market_YTD_USD` mapping becomes dead-but-harmless. fetch_market_data.py overwrites the field daily so any future `sync_sheet.py --market` run gets immediately superseded. Cleanup deferred.

(5) **Top-level fields not addressed.** `country.stock_market_ytd_usd` and `country.stock_market_ytd` at the data.json top level are stale (separate from the `metrics.market` entries the homepage reads). Neither is on the homepage render path. Different writer, separate fix if ever needed.

(6) **GitHub HTTPS auth refreshed.** Cached PAT in macOS Keychain had expired (90-day default rotation, last successful use was Session 73 on 2026-04-24). Auto-push from build.py failed with "No anonymous write access". Resolved by installing `gh` (GitHub CLI) via Homebrew and running `gh auth login` (HTTPS, web browser flow) which writes a fresh token into the system keyring. No PAT manually generated. Future pushes work silently again. New tool installed: gh 2.91.0 at /opt/homebrew/bin/gh.

(7) **New rule.** RULE 15 added under ABSOLUTE NON-NEGOTIABLE OUTPUT RULES: USA Stock Market YTD (USD) must equal local YTD verbatim - col2 mirrors col1, no separate calculation.

(8) **Files shipped this session:**
- fetch_market_data.py: docstring updated to list `Stock Market YTD (USD)` as a written metric. Added `stock_ytd_usd` field to `raw` dict in process_country(). New ~50-line block at end of process_country() after the FX section deriving USD-YTD per country with USA special-cased to mirror local string.

(9) **Pipeline integration: no changes to the Daily Bash Ritual itself.** fetch_market_data.py runs in the same slot, writes one extra field per country. Headlines flow, commodity stories, build.py and audit all unchanged.

---

Session 76 changes in detail:

(1) **Daily cost review.** Strategic discussion on reducing daily spend (API and operator time). Three options on the table: (a) kill daily metric story rewrites, (b) swap manual annual forecasts for IMF WEO consensus, (c) cut headlines (largest API line item). Decision: harvest (a) first (biggest API saving, editorial output goes up not down because the model only writes when there's something new to say); leave headlines alone (the editorial heart of the daily, cutting there is product surgery not cost optimisation); park (b) as a separate piece of work since it saves Friday operator time, not API cost.

(2) **Trigger-based metric story regeneration shipped.** Replaces the previous "regenerate all 132 metrics every day" with per-metric trigger logic. Three triggers, any one fires a regen:
- New monthly print arrived since last regen (Inflation, Unemployment, Policy Rate via `monthly_actuals[0]['month']` vs stored `story_last_print_month`)
- Daily-tier value moved 5% or more relative to story snapshot, where relative move is `abs(cur - snap) / max(abs(snap), 1.0) * 100` (covers Stock Market YTD, 10Y Bond Yield, Yield Curve, USD/DXY)
- Story is older than the tier ceiling: daily=7d, weekly=14d, structural=30d
Anything not triggered is carried forward at zero API cost. A `--force-all` flag bypasses triggers for full regen runs.

(3) **New fields added to every metric in data.json:**
- `story_last_updated` (YYYY-MM-DD): when the bullets were last regenerated
- `story_value_snapshot` (str, e.g. "+4.2%"): value at story write time, used by the move trigger
- `story_last_print_month` (YYYY-MM, monthly metrics only): latest print month at story write
These fields sit alongside `story` and never touch the existing `last_updated`, `value`, or `value_at_generation` fields, which are still managed by the rest of the pipeline.

(4) **Apply step changed.** `update_metric_stories.py --apply` now skips carried-forward metrics entirely. Their bullets are kept untouched, and crucially their `story_last_updated` stamps are kept untouched too (this is what makes the staleness counter actually count). Only regenerated metrics get fresh bullets and refreshed stamps. The integrity check between `value_at_generation` and current value in `build.py` continues to apply for regenerated metrics; carried metrics retain their existing `value_at_generation` from the last regen.

(5) **Review UI rebuilt.** `metric_story_review.html` now renders carried-forward metrics dimmed and collapsed by default, with a small "carried" badge and the trigger reason shown inline ("fresh 3d", "stale 17d", "moved 8.2%", "new print 2026-04"). Regenerated metrics keep the existing edit-as-normal treatment with a "regen" badge. New status filter dropdown (regenerated only / carried only / all) sits alongside the existing country and section filters. Header meta line shows the regen/carried split for the loaded draft.

(6) **One-off backfill ran.** `backfill_story_freshness.py --apply` stamped 132 metrics with `story_last_updated=2026-04-25`, `story_value_snapshot` set to current value, and `story_last_print_month` set for the 35 monthly metrics with `monthly_actuals` data (12 countries times 3 monthly metrics minus CHN Unemployment which has no programmatic source). Backfill script kept in the repo for reference, not part of the daily ritual.

(7) **Expected steady-state saving: 75-85% reduction in Haiku calls for metric stories.** First daily ritual after backfill will show 0/132 regen (everything carried, everything fresh). Real triggers start firing once the day-7 ceiling kicks in for daily-tier metrics that haven't moved 5%+ before then. Monthly-print and big-move triggers will be the dominant regen drivers in normal weeks.

(8) **Files shipped this session:**
- `update_metric_stories.py`: full rewrite. Trigger logic, per-country Haiku prompt asking only for to-regen metrics, modified apply step that respects `_regenerated` flag, console summary of regen/carried split per country and overall.
- `metric_story_review.html`: full rewrite. Status filter, carry/regen visual treatment, header counter.
- `backfill_story_freshness.py`: one-off migration script (already applied, retained in repo).

(9) **Pipeline integration: no changes to the Daily Bash Ritual itself.** `update_metric_stories.py` runs in the same slot, just does much less work most days. Headlines flow, commodity stories, harvest, build.py and audit all unchanged. The two review gates work the same way (load draft, edit, export approved). Carry-forward metrics still appear in the draft so the reviewer sees full context, they just can't be edited usefully (the apply step ignores them).

(10) **Parked for later work.** Two items raised in the cost review but not actioned this session:
- **IMF WEO forecast swap.** Kills `forecast_server.py`, `forecast_cms.html`, and the Friday pre-ritual. Replace with `fetch_imf_forecasts.py` running twice yearly when WEO publishes (April / October). Saves Ralph's Friday but does not reduce API spend. Worth doing as a standalone piece of work.
- **Headlines optimisation.** 13 x Sonnet with web search on the global call is probably the largest single API line item. Options on the table: card-of-the-day model (one deep-dive country + 11 brief Haiku refreshes, ~70% saving on this line but quality drops), or Sonnet+search on global only with Haiku on country headlines (compromise). Editorial risk is real, leave alone unless API spend becomes a problem.

---

Session 75 changes in detail:

(1) **Cards system Phase 1 built end-to-end, then entire concept aborted.** Session began as the Phase 1 build for the Session 74 cards / faces redesign. Ralph drew the full 24-face library (3 boil variants each, 72 PSDs total) in Photoshop and converted to PNGs via psd-tools. Built the full Phase 1 deliverable: prep_faces.py (PSD-to-PNG conversion + white-to-alpha + bbox-trim + 1024x1024 normalisation), card_config.py (palette, dimensions, anchor metric set per country, font fallback chain with macOS Baskerville and Helvetica auto-detect), card_text_draft.json (hand-composed mood + ralph_line + per-metric mood + blurb per country, all 12 countries), render_cards.py (static card renderer producing 13 PNGs per day with per-metric face icons, white-filled paper-cutout faces against cream, FX label "Exchange Rate" with pair note such as "GBPUSD (USD per GBP)"). All 13 cards rendered cleanly against live data.json. Layout converged after several iterations to match the Session 74 mocks: hero face 260px, three metric rows with 80px white-filled icons, blurb under each global tile, masthead left-aligned, country-name-centred tiles, no Ralph Lazar attribution, mood word dropped from global tiles (face does the work).

(2) **Five product decisions locked along the way (now all moot, but recorded):** (a) cadence b - global daily plus news-weighted Card of the Day; (b) cards consume latest prints not forecasts (forecasts are still in data.json from the Google Sheet but stay confined to the dashboard); (c) anchor metric set defined for all 12 countries (USA: inflation/unemployment/stock_market_ytd; CAN: inflation/policy_rate/fx_rate; GBR: inflation/unemployment/fx_rate; JPN: fx_rate/policy_rate/inflation; DEU: inflation/stock_market_ytd/bond_yield_10y; FRA: inflation/unemployment/bond_yield_10y; ITA: inflation/unemployment/bond_yield_10y; CHN: fx_rate/stock_market_ytd/inflation; IND: inflation/stock_market_ytd/fx_rate; ZAF: fx_rate/inflation/policy_rate; BRA: fx_rate/inflation/policy_rate; RUS: brent_crude/inflation/fx_rate); (d) IMF WEO swap planned for next session to replace Ralph's proprietary 2026 forecasts on GDP/Budget Deficit/Current Account with consensus IMF forecasts (now also moot since cards are dead and the dashboard already uses sheet forecasts fine); (e) "smirking" mood reserved for schadenfreude / contrarian wins / one-party-benefiting-from-another's-pain - never as a generic positive face.

(3) **Animation was the failure point.** Built make_animated_previews.py (24 mood GIFs cycling on cream) and make_animated_cards.py (HTML overlay of animated GIFs on top of static PNG cards using percentage-positioned absolutes, so GIFs scale with browser-resized PNGs). Source library was deliberately sparse (3 frames per mood). First pass at 10 fps with no jitter looked amateur; whole page flashed in sync. Second pass added per-mood phase offset and slight duration variation, slowed to 5 fps. Third pass added ping-pong sequencing (1,2,3,2,1,2,3,2 → 8 displayed frames) plus per-frame jitter (±2px translation, ±0.6° rotation, deterministic per mood). Ralph's read after the third pass: still felt weak. The honest path forward would have been redrawing the library at 8-10 frames per mood (real hand-drawn variation per frame), which is meaningful drawing time with no guarantee of payoff.

(4) **Started a partial CMS before abort.** sync_face_library.py was begun as a "drop-PSDs-into-folder, run-script" workflow that would auto-detect frame count per mood (3 to 10) and rebuild GIFs at appropriate richness. Adaptive sequence logic built (3 frames = ping-pong; 4 frames = short ping-pong; 5+ frames = forward play; frame rate scales with library richness). Untested. File deleted along with the rest.

(5) **Aborted the entire face / cards / animation concept.** Decision: kill the redesign, keep the existing dashboard architecture as-is. The cards added complexity without a clear pull from readers, and the animation gap between concept and execution would have required ongoing drawing investment with uncertain return.

(6) **Files to delete from repo:** render_cards.py, card_config.py, card_text_draft.json, prep_faces.py, make_animated_previews.py, make_animated_cards.py, sync_face_library.py, faces/ directory (72 PNGs), fonts/ directory (Baskerville/Helvetica TTC paths are macOS system fonts so nothing to clean there). Source PSDs in ~/Desktop/emotions/ are Ralph's personal artwork and stay outside the repo. The repo returns to its Session 74 state.

(7) **Existing dashboard preserved unchanged.** Daily Bash Ritual, weather icon system, three-act story formula, complexity tiers, edu pipeline, Substack flow - all untouched. No changes to standing operations as a result of this session.

(8) **Cards system - design spec (locked Session 74) section deleted from brief.** Replaced with brief abort note. Next-session-build section also deleted. Concept is dead - do not revive without a fresh strategic conversation.

---

Session 74 changes in detail:

(1) **Strategic pivot agreed: site redesigns around hand-drawn faces, not data.** Ralph raised the long-standing positioning problem - "I'm still not sure what MacroSnaps is and who uses it." Diagnosis: it is currently five products glued together (free, for-everyone, daily, 12-country, multi-complexity dashboard), and no single identity has formed. Decision: cut four of those five and go deep on one. The chosen direction is the "shareable cards" route - every country-day becomes a single hand-drawn-face card, designed to be screenshotted and shared. The data dashboard does not disappear; it demotes to a third-click detail view behind the cards.

(2) **Visual system: hand-drawn faces replace weather icons.** The three weather icons (sunny, cloudy, stormy) were the most distinctive thing in the product but were buried under tables. Replacing them with hand-drawn faces gives a wider expressive range (dozens of states vs four) and is more honest to the subject (markets are sentiment, faces convey sentiment). Style direction is "dry not cute" - rough, slightly imperfect, ink-on-paper, in the register of David Shrigley / Jean Jullien / Quentin Blake. Ralph is the illustrator. The previously-drafted illustrator brief (Word doc) is shelved, not sent.

(3) **Face library spec: 24 faces, in 5 emotional groups, 3 boil variants each (72 drawings total).** Ralph confirmed he will redraw the library properly on Bristol paper with a consistent black brush pen, scanned at 600dpi. The 24 faces are:

- **Positive (6):** Euphoric, Grinning, Content, Serene, Smirking, Amused
- **Neutral (4):** Neutral, Alert, Blank, Sceptical
- **Mildly Negative (5):** Puzzled, Worried, Uneasy, Exhausted, Asleep
- **Acute Negative (5):** Grimacing, Panicked, Shocked, Weeping, Furious
- **Sideways (4):** Goofy, Drunk, Suspicious, Sheepish

Drawing rules: identical head shape across all 24 (variation in eyes and mouth only); draw all three frames of one face in the same sitting (consistency within a face beats consistency across faces); name files `worried_1.png`, `worried_2.png`, `worried_3.png` etc. Animation cycle on the site uses the three frames at 8-12fps in randomised order ("boil" technique, ref Terry Gilliam / Don't Hug Me I'm Scared). Static cards for sharing use frame 1 only. Animation is for the site only, not for shareable PNGs.

(4) **Card anatomy locked.** Country card is 1080x1080. Top strip: MACROSNAPS wordmark, date, serial number (No. 0427 format, sequential from launch). Country heading in serif caps. Hero face (340px) left-aligned. Mood tag (one italic word in serif, in quotes, e.g. "worried.") to the right of the hero, hero-height. Three metric rows below: small face + label + italic note + reading. Bottom: Ralph line in italic serif quotes, signed "- Ralph". Watermark macrosnaps.app and serial. Palette: cream paper (244, 237, 224), black ink (28, 26, 22), soft ink for secondary text (90, 85, 75). Fonts: Lora (serif), DejaVu Sans (utility) - to be replaced with proper paid fonts at production stage.

(5) **Homepage anatomy locked.** 1600x1100 (desktop). Top strip same as country card. Masthead "The world today" with subtitle "twelve economies, twelve moods, one glance." 4x3 grid of 12 country tiles. Each tile: country code + name (small), face (110px), italic mood word, one-line caption (e.g. "polite stagnation"). Hairline dividers between tiles. Footer: "Tap any face for that country's card." + Ralph signature. Mobile version not yet designed - probably 2x6 grid, to be tested when build starts.

(6) **Site architecture: three layers.** Layer 1 = homepage (12-face grid, the world today). Layer 2 = country card (one country, hero face + 3 metrics + Ralph line). Layer 3 = the existing dashboard (charts, history, complexity tiers) reached only by clicking a metric on the country card. Most visitors never reach Layer 3. The current dashboard work is preserved in full, just demoted from front door to detail view.

(7) **Metric rotation rule.** Country cards always have exactly three metric slots (template never varies). Which three metrics fill the slots is decided daily by priority: (i) event-driven - if a major release landed in the last 24h, that metric takes slot 1; (ii) move-driven - anything that moved >1.5 standard deviations in the last day takes a slot; (iii) default - fall back to the country's three "anchor" metrics. Each country has a pool of 8-10 tracked metrics and a country-specific anchor set (UK = Inflation/Growth/Employment; India might default to Monsoon in season; Russia anchors on Oil; etc.). Anchor sets need to be defined per country - one afternoon's design work, not yet done.

(8) **URL model: every country-day is a permalink.** macrosnaps.app/uk/2026-04-24 is a permanent URL showing the UK card as it appeared on 24 April 2026. The card on that URL is the same image as the shareable PNG. The archive becomes the product as much as the daily does. This is the moat - nobody else in macro has time-stamped, linkable, visually-distinctive daily artefacts.

(9) **Cadence question parked.** Three options on the table: (a) daily Global card + on-demand country cards (only when something moves); (b) daily Global + one Card of the Day; (c) all 12 country cards every day. My recommendation was (b). Decision deferred to the build session.

(10) **Mocks produced and approved this session:**
- `card_uk_mock.png` - UK country card, "worried" mood, hero face + 3 metrics + Ralph line "Another quarter of polite stagnation"
- `card_usa_mock.png` - USA country card, "ebullient" mood, hero face + 3 metrics + Ralph line "Party like it's 2007"
- `homepage_mock.png` - 12-face grid showing the world today

(11) **Editorial cost flagged.** Twelve mood tags and twelve Ralph lines per day, fresh, sharp, that don't read as Mad Libs, is the real ongoing cost of this concept. Generation runs through `update_metric_stories.py` (extended). A review gate (similar to existing headline / metric story gates) will be needed to eyeball cards before publish. Editorial discipline is the long-term make-or-break of this concept, not the tech.

(12) **Cards-as-tweets.** PNGs aren't clickable on their own. The shareable model is: tweet contains the link (macrosnaps.app/uk/2026-04-24), card image is the visual hook, card watermark carries the URL for screenshot-only viewers. Same on LinkedIn, Substack, WhatsApp.

(13) **Standing rules expanded.** A new set of operating rules added by Ralph this session, locked in to appear in every future brief. See "Standing rules" section below.

(14) **Lisa is not a person.** Lisa is the name of Ralph's computer (hence the home directory `/Users/lisaswerling/`). Ralph is doing all the work himself. All future brief language refers to Ralph as the operator. The path stays as-is.

---

Session 73 changes in detail:

(1) **Daily ritual completed 2026-04-24.** Full ritual ran successfully. Friday pre-ritual: forecast CMS opened and 2026 forecasts reviewed. No commodity stories rewritten (all 9 within 5% threshold - WTI, Brent, Nat Gas, Gold, Silver, Copper, Wheat, Corn, Soybeans). Headlines 13/13 drafted in 177s (Sonnet + web search, healthy runtime). Metric stories 12/12 in 78s, no retries. Both review gates (headline_review.html, metric_story_review.html) passed. Build successful, auto-committed and pushed to master. Audit: all checks passed. Social Media Bash skipped per Ralph's instruction.

(2) **No procedural changes this session.** URL-as-clickable-hyperlinks rule (RULE 2 under ABSOLUTE NON-NEGOTIABLE OUTPUT RULES) re-confirmed and added to Claude's persistent memory for reinforcement across sessions. No code, script, or ritual changes.

(3) **Forecast CMS 404 quirk noted.** `forecast_server.py` (Flask on :5050) only serves API endpoints (`/forecasts`, `/forecast`, `/external_forecasts`, `/run_fetch`, `/fetch_status`, `/health`) - it does not serve `forecast_cms.html` as a static route. The CMS page must be opened directly from the filesystem: `open /Users/lisaswerling/RALPH/AI/macrosnaps/forecast_cms.html`. The page itself then makes CORS requests to the Flask server on :5050 for data. No fix needed - behaviour is as designed, just not intuitive from the 404 in the server log.

---

Session 72 changes in detail:

(1) **Daily ritual completed 2026-04-16.** Full ritual ran successfully. 4 commodity stories rewritten: WTI Crude (-7.2% move), Silver (+7.4%), Copper (+5.0%), Wheat (+6.9%). Headlines 13/13 drafted in 188s. Metric stories 12/12 in 80s, no retries needed. Build successful, auto-committed and pushed to master. Audit: all checks passed.

(2) **No procedural changes this session.** Both review gates used the File System Access API (showSaveFilePicker, Session 71) to save approved JSON directly into the repo - no `mv` step needed. `sync_edu.py` and the macedu-v2/BRAINsmoothie pushes remain removed from the ritual (Session 69).

---

Session 71 changes in detail:

(1) **Daily ritual completed 2026-04-12.** Full ritual ran successfully. No commodity stories rewritten (all within threshold). Headlines 13/13 in 175s. Metric stories 12/12 in 71s. Build successful, pushed to master. Audit: all checks passed.

(2) **Review UI export patched - direct repo save.** `patch_review_export.py` patches both `headline_review.html` and `metric_story_review.html` to use the browser File System Access API (`showSaveFilePicker`) instead of forcing a download to `~/Downloads/`. On export, a save dialog opens; navigate to `/Users/lisaswerling/RALPH/AI/macrosnaps/` once and the browser remembers it. Falls back to the old `~/Downloads/` behaviour if the API is unavailable. The `mv` step after each review gate is no longer needed once the browser has the repo location saved.

---

Session 70 changes in detail:

(1) **Daily ritual completed 2026-04-10.** Full ritual ran successfully. Copper (5.6% move) and Wheat (5.0% move) commodity stories rewritten. Headlines 13/13 in 164s. Metric stories 12/12 in 126s (RUS retried once). Build: 24 metric changes, 36 story changes, 9 commodity changes. Pushed to master. Audit: all checks passed.

(2) **Google Sheets 429 quota hit.** On the first run of `sync_market_historical.py`, DEU through RUS tabs all returned 429 (quota exceeded). USA, CAN, GBR, JPN completed cleanly. `sync_commodity_data.py` also failed immediately. Fix: wait ~60s and rerun both scripts. Second run completed all 12 countries cleanly. No data loss.

---

Session 69 changes in detail:

(1) **Daily ritual completed 2026-04-09.** Full ritual ran successfully. No commodity stories rewritten (all within threshold). Headlines 13/13 in 172s. Metric stories 12/12 in 77s. Build: 24 metric changes, 9 commodity changes, 0 story changes. Pushed to master. Audit: all checks passed.

(2) **sync_edu.py and macedu-v2 removed from Daily Bash Ritual.** `sync_edu.py`, the macedu-v2 git push, and the BRAINsmoothie git push have been removed from the Daily Bash Ritual permanently. These steps are no longer part of the standard daily sequence.

---

[Earlier session entries 68 down to 45 preserved in full in the prior version of this brief; collapsed here for length. See the unabridged history at the bottom of this document.]

---

## Standing rules

### ABSOLUTE NON-NEGOTIABLE OUTPUT RULES

These apply to EVERY SINGLE RESPONSE. No exceptions. Ever. Listed verbatim below; Ralph adds to this list session by session.

**RULE 1 - File downloads always to ~/Downloads/. Always provide the bash copy command using the latest-file pattern.**
After presenting any file for download, always provide the bash command to copy it into the correct repo path. The copy command must use:
```bash
cp "$(ls -t ~/Downloads/filename*.ext | head -1)" /Users/lisaswerling/RALPH/AI/macrosnaps/filename.ext
```
The `$(ls -t ... | head -1)` subshell grabs the most recently downloaded version. Quotes around the subshell are mandatory to handle macOS filenames containing spaces. Then provide the run command. In that order. Always.

**RULE 2 - URLs always as clickable markdown links.**
Every URL in every response must be a clickable markdown link. Never paste a bare URL. Example: [http://localhost:8080](http://localhost:8080) - never `http://localhost:8080` as plain text.

**RULE 3 - Always show a plan before building. Never start without it.**
Before writing any code, generating any file, or making any change to the repo, show the plan first. The plan should be short and concrete: what will change, what files are touched, what the user will see at the end.

**RULE 4 - Always ask for confirmation after showing the plan. Wait for the go-ahead.**
After presenting the plan, stop. Do not proceed until Ralph has confirmed. No "I'll go ahead and start" momentum.

**RULE 5 - All text must never look AI-written.**
No em-dashes (use regular hyphens). No apostrophes inside JSON summary fields. No "delve", "tapestry", "boasts", "robust", "leverage" (verb), "in conclusion", "it's important to note", or other LLM tells. Plain, human, readable English. Specific over vague. Numbers over hand-waves.

**RULE 6 - Add to brief when asked. Never present the brief as a download unless asked.**
When Ralph says "add this to the brief" or "remember this", add it silently. Do not produce the revised brief unless he explicitly asks for it.

**RULE 7 - The brief is always delivered as a .md file for download.**
When Ralph asks for the updated brief, produce a `.md` file (not Word, not PDF, not inline text). Save to `~/Downloads/` so it follows Rule 1.

**RULE 8 - When asked for bash code, respond with just the code block. No preamble.**
If Ralph asks for a command, give the command. No "Here's the command:". No "This will do X:". Just the fenced code block. After the block, the cp + run command pair if relevant (Rule 1).

**RULE 9 - Do not push to git during development.**
Push only when session work is complete and Ralph has confirmed the push. Build locally, preview locally, ship only when explicitly told to.

**RULE 10 - When you need to see a file from the local repo, give the bash code to copy it to Downloads, then wait for Ralph to upload it.**
Claude cannot read Ralph's local filesystem. The flow is: Claude asks for the file, gives a `cp /Users/lisaswerling/RALPH/AI/macrosnaps/path/to/file ~/Downloads/` command, Ralph runs it and uploads the file from Downloads to the chat.

**RULE 11 - When asked to add a rule, add it to the brief silently. Do not present the revised brief unless asked.**
Same as Rule 6 but for rules specifically. The acknowledgement is the addition. No restating the rule back, no "I've added that".

**RULE 12 - Never ask two questions at the same time.**
One question per turn, maximum. If clarification needs more than one question, ask the most important one first and follow up after the answer.

**RULE 13 - Ralph never manually edits files. Claude does it.**
If a file needs a patch, Claude writes a patch script, delivers it to Downloads, gives the cp + run commands. If Claude needs to see the current state of the file first, use Rule 10. Ralph does not open files in an editor.

**RULE 14 - There is no Lisa.**
"Lisa" is the name of Ralph's MacBook (which is why home is `/Users/lisaswerling/`). Ralph is the operator, designer, owner, and only human in the loop. All language in briefs and responses refers to Ralph. The directory path stays unchanged - it's just a hostname.

**RULE 15 - USA Stock Market YTD (USD) must equal local YTD verbatim.**
On the homepage Stock Market YTD ranking, the USA row's USD column (col2) must display identically to the local column (col1). USA's local currency is USD, so any FX adjustment is conceptually zero. In fetch_market_data.py, the USA branch parses the local YTD string back to a float and stores that as the USD value. Never apply DXY or any other FX-adjusted calculation to USA. Other countries continue to use the standard compound formula.

### Other standing notes

**Local preview before push.** Since the site is live, all changes must be tested locally before pushing. Always provide a local preview step before any git push command. Never combine build and push.

**Plan-confirm-build-test-ship loop.** Standard cycle: Claude shows plan → Ralph confirms → Claude builds (delivers files via Downloads + cp commands) → Ralph runs locally → both review → Ralph confirms → Claude pushes (or gives push command).

---

## Daily Bash Ritual

**Friday only - run this first, before anything else:**
```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 forecast_server.py
```
Open `forecast_cms.html` directly from the filesystem (the Flask server only serves API endpoints, not the static page):
```bash
open /Users/lisaswerling/RALPH/AI/macrosnaps/forecast_cms.html
```
Review and update forecasts, then close the server before proceeding.

Run the consolidated pre-review script (Session 79: replaces the six individual python3 commands that used to be run step-by-step):

```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps && bash morning_bash.sh
```

`morning_bash.sh` runs the following six steps in sequence with `set -e` (halts on first error), step banners, and tee'd logging to `logs/morning_bash_YYYY-MM-DD.log`:

```
python3 fetch_market_data.py
python3 sync_market_historical.py --apply
python3 sync_commodity_data.py --apply
python3 update_commodity_stories.py
python3 update_headlines.py
python3 update_metric_stories.py
```

On Fridays, the script prompts to confirm `forecast_server.py` has been run first; "n" hard-exits and reminds you to run the forecast server before re-running morning_bash.sh.

Manual gate (headlines only - metric stories gate retired Session 78): open `headline_review.html` (via [http://localhost:8080](http://localhost:8080)), load `HEADLINES_draft_YYYY-MM-DD.json`, review and edit, export `HEADLINES_approved_YYYY-MM-DD.json`. The browser save dialog (File System Access API, Session 71) writes directly into the repo - no `mv` step needed.

Metric stories now apply directly from the draft file - no review UI, no rename step.

```bash
python3 update_headlines.py --apply HEADLINES_approved_YYYY-MM-DD.json
python3 update_metric_stories.py --apply METRICS_draft_YYYY-MM-DD.json
python3 build.py
cd /Users/lisaswerling/RALPH/AI/macrosnaps && python3 audit_ritual.py
```

Note: to open the headline review UI locally without CORS errors, run `python3 -m http.server 8080` in the macrosnaps directory first, then use [http://localhost:8080](http://localhost:8080).

### Intraday Bash Ritual (ad hoc, news-driven)

Run when markets are moving fast and the global story needs refreshing mid-day. Can be run 2-4x per day. No review gates. Takes 2-3 minutes.

```bash
cd /Users/lisaswerling/RALPH/AI/macrosnaps
python3 fetch_market_data.py --apply
python3 sync_commodity_data.py --apply
python3 update_global_stories.py
python3 build.py --apply
```

---

## Cards system - aborted (Session 75)

The hand-drawn face / cards / animation redesign locked in Session 74 was built to Phase 1 in Session 75 and then aborted. The static-card concept rendered cleanly but the animation gap could not be closed without a much denser hand-drawn library, and the cards themselves added complexity without a clear pull from readers.

Concept is dead. Do not revive without a fresh strategic conversation. The existing dashboard architecture (weather icons, three-act stories, complexity tiers, daily ritual) remains the canonical product. See Session 75 detail above for what was built and removed.

---

## MacroSnaps product overview

MacroSnaps (macrosnaps.app) is a free daily macro and markets dashboard covering 12 major economies with data explained at beginner / moderate / expert levels. Built by Ralph Lazar, former macro strategist at Goldman Sachs and fixed-income prop trader at CSFB. Educator landing page: macrosnaps.app/educators.html.

As of Session 75 the product is the live data dashboard. The face / cards redesign attempted in Sessions 74-75 was aborted; existing architecture preserved unchanged.

---

## Architecture notes (latest state)

Key invariants:
- sync_sheet.py --apply writes only annual forecast fields
- sync_monthly_actuals.py writes only the monthly_actuals field
- These two scripts must never touch each other's fields
- build.py fails with a clear error if value_at_generation differs from current value for any metric story

### Header date (as of Session 68)
- The top-left "Updated" date in `macrosnaps-shell.html` is set by a JS IIFE using `new Date()` in UTC
- It always reflects today's GMT date when the page loads - it does not read from `data._meta.generated`
- The site never looks stale between builds

### _frozen_historical alignment (as of Session 66)
- Every monthly `_frozen_historical` series carries a `"startDate": "YYYY-MM"` field
- The JS left-aligns from `startDate`: data is placed at the correct label position regardless of array length or build date
- Live series (Yield Curve, Bond Yield, Stock Market, FX) are kept at 316 pts by `sync_market_historical.py` and are always current
- Inflation (CPI) is rebuilt from the MACRO-MONTHLY sheet via `rebuild_cpi_historical.py` - re-run this whenever the sheet is materially updated
- Live series remain current; frozen series show a null gap after their freeze date
- Any future series added to `_frozen_historical` must include a `startDate`

**Known data quality gaps - require FRED backfill:**
- **IND 10Y Bond Yield** - only 2 data points; placeholder array; needs FRED backfill
- **IND Yield Curve** - only 2 data points; placeholder array; needs FRED backfill

### Story formula (three-act global arc)
- Card 1 - The Trigger: one economic event or data print driving global attention
- Card 2 - Biggest Movers: which markets, currencies, or economies are reacting and how
- Card 3 - The Connection: what ties cards 1 and 2 together, the "so what" for the global picture

All three levels (beginner, moderate, expert) tell the same arc at different depths.

### Editorial principle: forecasts vs stories
Forecast values (source: Ralph's Google Sheet) are annual consensus views for 2026. They drive the metric value and weather icon. Stories should be written off recent data and trends, not off the forecast values.

### JSON file naming (as of Session 59)
- `harvest_YYYY-MM-DD.json` - raw web search data; internal only; consumed by `update_metric_stories.py`; never loaded in a UI
- `HEADLINES_draft_YYYY-MM-DD.json` - country card + global stories draft; loaded in `headline_review.html`
- `HEADLINES_approved_YYYY-MM-DD.json` - approved headlines; applied via `update_headlines.py --apply`
- `METRICS_draft_YYYY-MM-DD.json` - per-metric bullet stories draft; loaded in `metric_story_review.html`
- `METRICS_approved_YYYY-MM-DD.json` - approved metric stories; applied via `update_metric_stories.py --apply`

### MACRO-MONTHLY sheet (as of Session 60)
- Sheet ID: `1-s4hppAkoTZbjGGEkHSUDK2H7E00RHhVuHrYKWLuHpI` (env var: `MACRO_MONTHLY_SHEET_ID`)
- Three tabs: Inflation, Unemployment, Policy_Rate
- Unemployment sources by country:
  - USA: FRED `UNRATE` (BLS, monthly)
  - CAN/JPN/DEU/FRA/ITA/RUS: IMF LS dataset (monthly)
  - GBR: FRED `LRHUTTTTGBM156S` (ONS via FRED, monthly)
  - BRA: IBGE SIDRA table 6381 (PNAD Contínua, monthly) - wired into `update_monthly_actuals.py`
  - ZAF: FRED `LRUNTTTTZAQ156S` (OECD quarterly, interpolated) - backfilled via `backfill_unemployment.py`
  - IND: World Bank `SL.UEM.TOTL.ZS` (annual, interpolated) - backfilled via `backfill_unemployment.py`
  - CHN: no free programmatic source - permanent blank
  - RUS 2000-2009: no free programmatic source - permanent blank

---

## Substack strategy

**Goal for first 3 months:** audience building only. No paywall, no monetisation pressure.

**Cadence: daily posts + weekly digest**

- Daily post: short, low-friction, almost verbatim from the pipeline's three-act global story output. Proves the pipeline is alive, creates a scrollable archive, feeds Substack's algorithm.
- Weekly digest: longer and more considered; what mattered this week, which countries moved, what surprised, what to watch next week.

Keep daily posts genuinely short.

**Funnel: glossary links + one CTA per post.** Every glossary term hyperlinked to live glossary on macrosnaps.app (first occurrence per post only). One explicit CTA at end of every post.

**Voice:** Substack readers follow people, not products. A 2-3 sentence human intro each day (written by Ralph) is important.

**Promotion (first 3 months), in priority order:**
1. Personal outreach - first 50-100 subscribers from known network
2. LinkedIn - weekly post with chart or insight + link
3. Cross-recommendations on Substack
4. Twitter/X - slow burn, worth maintaining for macro community
5. Ask early subscribers to forward to one person

What not to bother with in first 3 months: paid promotion, SEO, press outreach, ProductHunt-style launches.

Do not position against Bloomberg or data terminals. The competition is a good morning read, not a data subscription.

---

## Full session history

Session 80: Daily ritual completed 2026-05-07. morning_bash.sh ran in 4m 36s. 3 commodity rewrites (WTI -5.7% to 92.93, Brent -11.1% to 99.11, Silver +8.5% to 80.08). Headlines 13/13 in 187s. Metric stories: 21 regenerated, 111 carried forward (84% saved), 12/12 in 15s. Headline review gate passed. Build successful. Audit clean. Procedural change: Social Media Bash retired permanently from Daily Bash Ritual; section removed from brief; digest_server.py and digest_ui.html remain in the repo as inert artefacts. France Stock Market YTD homepage null flagged at session start; today's fetch_market_data.py wrote FRA +1.3% local / +1.47 USD cleanly and the build pushed the fix to the homepage; root cause parked. Several large metric-story trigger moves observed (FRA 130%/147%, ZAF 139%/180%, DEU 50%/62%, JPN 41%/47%, RUS 80%/9.8%) consistent with stale/null snapshots, supporting the FRA observation. 7 FRED bond/yield endpoints returned HTTP 500 (USA DGS10, USA TB3MS, JPN x2, FRA ECBDFR, ZAF x2); affected fields retain prior day's values; transient. Cosmetic: fetch_market_data.py summary counter undercounts failures (7 actual, says 1).
Session 79: Daily ritual completed 2026-04-29. New tooling: morning_bash.sh shipped, consolidates pre-review steps 1-6 of the Daily Bash Ritual into a single script with set -e (halts on first error), step banners, tee'd log to logs/morning_bash_YYYY-MM-DD.log, Friday forecast_server.py confirmation prompt with hard exit on "n", and runtime stamp. First production run completed in 5m 15s, zero errors, 12/12 MARKET-STATS countries appended cleanly. 4 commodity rewrites (WTI +11.4%, Brent +6.0%, Gold +5.9%, Wheat +8.1%). Headlines 13/13 in 205s. Metric stories: 20 regenerated, 112 carried forward (84% saved), 24s. Headline review gate passed. Build successful, auto-committed and pushed to master. Audit clean. Cosmetic noted for future tidy: update_metric_stories.py end-of-run "Next steps" output still references the retired METRICS_approved convention; should be tidied to reference draft file directly per Session 78. Daily Bash Ritual section in brief updated to show new bash morning_bash.sh entry point.
Session 78: Daily ritual completed 2026-04-28. First production run of Session 76 trigger-based metric story system - 17 regenerated, 115 carried forward (87% saved), 12/12 countries in 13s. 1 commodity story rewrite (Silver, moved 6.4%, was 78.86 now 73.83). Headlines 13/13 in 200s. Both review gates passed. Build successful, pushed to master. Audit clean. DEU MARKET-STATS sheet append failed in step 1 with Google 502; retried via fetch_market_data.py rerun and DEU + CHN both appended (idempotent skip caught a quietly-missing CHN row from an earlier session; net 2 appended, 10 skipped, 0 failed). Intraday data.json delta after retry left as-is per Ralph's call. Procedural change: Manual Gate 2 (metric stories review via metric_story_review.html) RETIRED. New sequence: update_metric_stories.py -> update_metric_stories.py --apply METRICS_draft_YYYY-MM-DD.json. No review UI, no copy/rename to "approved". Manual Gate 1 (headlines) remains in place. Daily Bash Ritual section in brief updated.
Session 77: Bug fix - USA Stock Market YTD homepage glitch (showed +4.20% local / -3.12% USD, an embarrassing mismatch since USD return must equal local for USA by definition). Root cause: metrics.market['Stock Market YTD (USD)'] was only written by sync_sheet.py --market (not in any scheduled ritual); field had been stale since 2026-03-22. Fix: USD-YTD computation moved into fetch_market_data.py as a derived metric. USA hard-coded to mirror local YTD string verbatim; other countries computed via FX YTD compound (1 + local%) * (1 + USD-per-local%) - 1 using yf_price_and_ytd() and Yahoo ticker direction (LOCALUSD=X gives USD-per-local, USDLOCAL=X gives local-per-USD requiring inversion). RULE 15 added (USA col2 = col1, no separate calculation). GitHub HTTPS auth refreshed via gh auth login after PAT expiry in macOS Keychain (gh 2.91.0 installed via Homebrew). Pushed to origin master.
Session 76: Daily cost review and trigger-based metric story regeneration shipped. Replaces "regenerate all 132 metrics daily" with per-metric triggers (new monthly print, daily-tier move 5%+ relative to snapshot, or staleness past tier ceiling 7/14/30d); anything else carried forward at zero API cost. New fields story_last_updated, story_value_snapshot, story_last_print_month added to data.json. backfill_story_freshness.py ran (132 stamped, 35 with print month). update_metric_stories.py rewritten (per-country prompt requesting only to-regen metrics, --force-all escape hatch, modified apply step that preserves carried-forward stamps). metric_story_review.html rewritten with carry/regen badges, status filter, header counter. Daily Bash Ritual unchanged. Expected 75-85% Haiku call reduction steady state. Headlines and IMF forecast swap parked for separate sessions.
Session 75: Cards system Phase 1 built end-to-end (static cards working for all 13 PNGs from live data.json) then entire face / cards / animation concept aborted by Ralph. Animation synthesis (ping-pong sequencing + per-frame jitter on sparse 3-frame library) couldn't substitute for hand-drawn variation. All Session 75 scripts (render_cards.py, card_config.py, card_text_draft.json, prep_faces.py, make_animated_previews.py, make_animated_cards.py, sync_face_library.py), faces/ directory (72 PNGs), and fonts/ directory removed from repo. Existing dashboard architecture preserved unchanged. Cards system design spec from Session 74 deleted from active brief sections.
Session 74: Strategy / design session. No code, no ritual, no commits. Decision taken to redesign the site around hand-drawn faces (24-face library, 3 boil variants each, drawn by Ralph). Country card and homepage mocks built and approved. Three-layer site architecture locked: homepage 12-face grid → country card → existing dashboard. Per-country-per-day permalinks. Metric rotation rule defined. 14 absolute operating rules formalised. "Lisa" clarified as computer name only; Ralph is the sole operator.
Session 73: Daily ritual completed 2026-04-24; 0 commodity stories rewritten (all within threshold); headlines 13/13 in 177s; metric stories 12/12 in 78s, no retries; all checks passed; Social Media Bash skipped per Ralph's instruction. No procedural changes - URL clickable-link rule reconfirmed and added to Claude memory.
Session 72: Daily ritual completed 2026-04-16; 4 commodity stories rewritten (WTI -7.2%, Silver +7.4%, Copper +5.0%, Wheat +6.9%); headlines 13/13 in 188s; metric stories 12/12 in 80s, no retries; all checks passed. No procedural changes.
Session 71: Daily ritual completed 2026-04-12; both review UIs (headline_review.html, metric_story_review.html) patched to save approved JSON directly to repo via showSaveFilePicker (File System Access API) with ~/Downloads/ fallback (patch_review_export.py).
Session 70: Daily ritual completed 2026-04-10; Copper and Wheat commodity stories rewritten; Google Sheets 429 quota hit on first sync_market_historical.py run - resolved by waiting 60s and rerunning.
Session 69: Daily ritual completed 2026-04-09; sync_edu.py and macedu-v2 push removed from Daily Bash Ritual permanently.
Session 68: Daily ritual completed 2026-04-08; header date fix (macrosnaps-shell.html top-left "Updated" now uses browser clock UTC, not stale data._meta.generated); sync_edu.py now writes to BRAINsmoothie as well as macedu-v2; Daily Bash Ritual updated to push BRAINsmoothie.
Session 67: Daily ritual completed 2026-04-07; macedu-v2 confirmed as live edu repo (sync_edu.py writes to macedu-v2/app/data/metrics.js); Social Media Bash ritual instructions updated (stop http.server first; open digest_ui.html directly).
Session 66: _frozen_historical date alignment architecture fixed (startDate added to all 86 monthly series; JS updated to left-align from startDate); Inflation (CPI) historical rebuilt from MACRO-MONTHLY sheet for all 12 countries (rebuild_cpi_historical.py); sync_monthly_actuals.py date format bug fixed (DD/MM/YYYY[:7] → strptime YYYY-MM); IND 10Y Bond Yield and Yield Curve flagged for FRED backfill.
Session 65: Daily Bash Ritual updated - mv commands added after each review gate for HEADLINES_approved and METRICS_approved files.
Session 64: Intraday Bash Ritual added (update_global_stories.py built; ad hoc mid-day refresh procedure documented).
Session 63: Daily ritual completed 2026-04-02; build.py timezone fix (UTC → Europe/London for date stamp); http.server must run from macrosnaps directory for review UIs.
Session 62: Daily ritual completed 2026-03-31; sync_edu.py path fix (runs from macrosnaps repo, not macedu); Daily Bash Ritual updated.
Session 61: Daily ritual completed 2026-03-29; commodity stories migrated to bullet arrays; sync_market_historical.py/audit_ritual.py/build.py bug fixes; Brent Crude backfill complete; macedu deployed to Cloudflare Pages; commodity story prompt overhauled.
Session 60: MARKET-STATS daily append fixed (fetch_market_data.py patched; yf_ytd_and_level() added); Mar 16-27 backfill run across 12 country tabs (backfill_market_stats.py); bond yield patch script built (patch_bond_yields.py); MACRO-MONTHLY unemployment backfilled for IND/ZAF (backfill_unemployment.py) and BRA (update_bra_unemployment.py); BRA IBGE SIDRA wired into update_monthly_actuals.py; historical unemployment and policy rate gaps filled via backfill_historical_gaps.py; backfill --apply run (13 cells); MACRO_MONTHLY_SHEET_ID added to .env.
Session 59: Metric story pipeline fixed (Haiku truncation → 1 country per call → parallelised to 12 concurrent calls, 990s → 74s); JSON file renames (HEADLINES/METRICS); headline_review.html patched for bullets schema; build.py validator updated; Daily Bash Ritual updated.
Session 58: Forecast CMS added (forecast_server.py + forecast_cms.html); Friday pre-ritual rule added to Daily Bash Ritual.
Session 57: Favicon added (favicon.ico + favicon-192.png); favicon link tags added to macrosnaps-shell.html; X Card Validator confirmed icon picked up.
Session 56: Repo moved to /Users/lisaswerling/RALPH/AI/macrosnaps; MARKET_STATS_KEY_FILE env var added; node_modules scrubbed from macrosnaps and macedu repos; Daily Bash Ritual fixed (sync_edu.py before audit_ritual.py; macedu push added).
Session 55: macroeconomics.education data layer complete. sync_edu.py added to Daily Bash Ritual. macedu pushed to GitHub.
Session 54: US and UK educator outreach campaigns complete/paused per Ralph's instruction.
Session 53: US educator outreach ranks 55-51 complete; 10 contacts, 5 universities (Georgia Tech skip confirmed); LIVING_BRIEF updated; session prompt for ranks 50-1 created.
Session 52: Teaching-staff-first rule formalised; session prompt for ranks 55-1 revised.
Session 51: US educator outreach ranks 70-56 complete; 59 contacts, 15 universities; 3 CSV files produced.
Session 50: Social Media Bash documented; local preview rule added to standing rules.
Session 49: US educator outreach ranks 100-71 complete; 76 contacts, 30 universities; 5 CSV files produced.
Session 48: UK top 20 educator outreach complete (178 contacts); US top 100 outreach plan built.
Session 47: Educator cold email outreach campaign built; UK university macro contacts database started ranks 20-13.
Session 46: educators.html created; Twitter/OG meta tags added; Subscribe + Educators buttons moved to footer; #ping hash handler added; educator outreach strategy added to brief.
Session 45: build.py structural date fix; US to Commodities nav flash fixed.
[Earlier sessions: see prior LIVING_BRIEF history for complete record]
