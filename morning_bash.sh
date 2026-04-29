#!/usr/bin/env bash
#
# morning_bash.sh
# Consolidated pre-review steps of the Daily Bash Ritual.
# Runs fetch through draft generation in one go, halts at the headline review gate.
#
# Behaviour:
#   - set -e: halts on the first non-zero exit code
#   - On Fridays, prompts to confirm forecast_server.py has been run; hard-exits on "n"
#   - Tee's all output to logs/morning_bash_YYYY-MM-DD.log
#   - Reports total runtime at the end
#
# Run from anywhere:
#   bash /Users/lisaswerling/RALPH/AI/macrosnaps/morning_bash.sh

set -e
set -o pipefail

REPO=/Users/lisaswerling/RALPH/AI/macrosnaps
cd "$REPO"

# ------------------------------------------------------------------
# Friday pre-ritual check (runs before logging so the prompt is direct).
# ------------------------------------------------------------------
if [ "$(date +%u)" = "5" ]; then
  echo ""
  echo "=================================================================="
  echo "  FRIDAY PRE-RITUAL CHECK"
  echo "=================================================================="
  read -p "Have you run forecast_server.py and saved forecasts today? (y/n) " ANSWER
  if [ "$ANSWER" != "y" ] && [ "$ANSWER" != "Y" ]; then
    echo ""
    echo "Stopping. Run the forecast server first, then re-run morning_bash.sh."
    echo ""
    echo "  cd $REPO && python3 forecast_server.py"
    echo "  open $REPO/forecast_cms.html"
    echo ""
    exit 1
  fi
  echo ""
fi

# ------------------------------------------------------------------
# Logging setup.
# ------------------------------------------------------------------
mkdir -p logs
TODAY=$(date +%Y-%m-%d)
LOG="logs/morning_bash_${TODAY}.log"

exec > >(tee -a "$LOG") 2>&1

START=$SECONDS

banner() {
  echo ""
  echo "=================================================================="
  echo "  $1"
  echo "=================================================================="
  echo ""
}

banner "MORNING BASH STARTED $(date '+%Y-%m-%d %H:%M:%S %Z')"

# ------------------------------------------------------------------
# Steps 1-6: fetch through draft generation.
# ------------------------------------------------------------------

banner "STEP 1/6: fetch_market_data.py"
python3 fetch_market_data.py

banner "STEP 2/6: sync_market_historical.py --apply"
python3 sync_market_historical.py --apply

banner "STEP 3/6: sync_commodity_data.py --apply"
python3 sync_commodity_data.py --apply

banner "STEP 4/6: update_commodity_stories.py"
python3 update_commodity_stories.py

banner "STEP 5/6: update_headlines.py (draft)"
python3 update_headlines.py

banner "STEP 6/6: update_metric_stories.py (draft)"
python3 update_metric_stories.py

# ------------------------------------------------------------------
# Done.
# ------------------------------------------------------------------
ELAPSED=$((SECONDS - START))
MINS=$((ELAPSED / 60))
SECS=$((ELAPSED % 60))

banner "MORNING BASH COMPLETE - ${MINS}m ${SECS}s"

echo "Drafts ready. Next steps:"
echo ""
echo "  1. Start the local HTTP server (in a separate terminal):"
echo "       cd $REPO && python3 -m http.server 8080"
echo ""
echo "  2. Open http://localhost:8080/headline_review.html"
echo "     Load HEADLINES_draft_${TODAY}.json, review, export approved."
echo ""
echo "  3. Run the apply / build / audit steps:"
echo "       python3 update_headlines.py --apply HEADLINES_approved_${TODAY}.json"
echo "       python3 update_metric_stories.py --apply METRICS_draft_${TODAY}.json"
echo "       python3 build.py"
echo "       python3 audit_ritual.py"
echo ""
echo "Full log: $REPO/$LOG"
echo ""
