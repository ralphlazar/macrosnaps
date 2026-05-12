#!/bin/bash
# MacroSnaps v2 (MACRO-MAY) — local server
# Serves dist/ on http://localhost:8765/
# Run: bash serve.sh

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$DIR/dist" ] || [ ! -f "$DIR/dist/index.html" ]; then
  echo "No dist/index.html found. Running build first..."
  cd "$DIR" && python3 build.py
  echo ""
fi

PORT=8765
echo "Serving $DIR/dist on http://localhost:$PORT/"
echo "Press Ctrl+C to stop."
echo ""

# Try to open in browser (macOS)
(sleep 0.5 && open "http://localhost:$PORT/" 2>/dev/null || true) &

cd "$DIR/dist" && python3 -m http.server $PORT
