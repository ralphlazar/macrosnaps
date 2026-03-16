#!/usr/bin/env python3
"""
forecast_server.py — local Flask proxy for forecast_cms.html
Reads and writes 2026 forecast values (Column AB) in the Macro-stats Google Sheet.

Usage:
    pip install flask flask-cors gspread google-auth python-dotenv
    python3 forecast_server.py
    # Runs on http://localhost:5050 — open forecast_cms.html in your browser
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
# Set MACRO_STATS_SHEET_ID in your .env, or paste the sheet ID directly here.
SHEET_ID        = os.getenv("MACRO_STATS_SHEET_ID", "YOUR_MACRO_STATS_SHEET_ID_HERE")
SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Column AB = 28 (A=1 ... Z=26, AA=27, AB=28). This is the 2026 forecast column.
FORECAST_COL = 28

# Row mapping: which sheet row holds each metric (1-indexed, row 1 = header).
# Adjust if your Macro-stats tabs use a different order.
METRIC_ROWS = {
    "GDP_Growth":      2,
    "Inflation":       3,
    "Unemployment":    4,
    "Budget_Deficit":  5,
    "Current_Account": 6,
    "Policy_Rate":     7,
}

# Countries in GDP-nominal order (must match worksheet tab names exactly).
COUNTRIES = ["USA", "CHN", "DEU", "JPN", "IND", "GBR", "FRA", "ITA", "BRA", "CAN", "RUS", "ZAF"]
METRICS   = list(METRIC_ROWS.keys())

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Tracks background fetch status
_fetch_state = {"running": False, "last_run": None, "last_error": None}

# ── Google Sheets helpers ─────────────────────────────────────────────────────
def get_sheet():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)


def _parse_number(val):
    """Convert cell value to float if possible, else return as string."""
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except ValueError:
        return val


# ── Routes ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)


@app.route("/forecasts", methods=["GET"])
def get_forecasts():
    """Return all 12 × 6 forecast values from Column AB."""
    try:
        sh = get_sheet()
        result = {}
        for country in COUNTRIES:
            try:
                ws = sh.worksheet(country)
                # Single API call: read entire column AB at once
                col_vals = ws.col_values(FORECAST_COL)
                forecasts = {}
                for metric, row in METRIC_ROWS.items():
                    raw = col_vals[row - 1] if len(col_vals) >= row else None
                    forecasts[metric] = _parse_number(raw)
                result[country] = forecasts
            except gspread.exceptions.WorksheetNotFound:
                result[country] = {m: None for m in METRICS}
                result[country]["_error"] = f"Tab '{country}' not found"
        return jsonify({"ok": True, "data": result, "fetched_at": datetime.utcnow().isoformat() + "Z"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/forecast", methods=["POST"])
def update_forecast():
    """
    Update a single forecast cell.
    Body: {"country": "USA", "metric": "GDP_Growth", "value": 2.3}
    """
    try:
        body = request.json
        country = body.get("country", "")
        metric  = body.get("metric", "")
        value   = body.get("value")

        if country not in COUNTRIES:
            return jsonify({"ok": False, "error": f"Unknown country: {country}"}), 400
        if metric not in METRIC_ROWS:
            return jsonify({"ok": False, "error": f"Unknown metric: {metric}"}), 400
        if value is None or str(value).strip() == "":
            return jsonify({"ok": False, "error": "Value cannot be empty"}), 400

        # Parse to float for clean sheet storage
        try:
            value = float(str(value).strip())
        except ValueError:
            return jsonify({"ok": False, "error": f"Invalid number: {value}"}), 400

        row = METRIC_ROWS[metric]
        sh  = get_sheet()
        ws  = sh.worksheet(country)
        ws.update_cell(row, FORECAST_COL, value)

        return jsonify({
            "ok":      True,
            "country": country,
            "metric":  metric,
            "value":   value,
            "saved_at": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/external_forecasts", methods=["GET"])
def get_external_forecasts():
    """Serve external_forecasts.json if it exists."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "external_forecasts.json")
    if os.path.exists(path):
        with open(path) as f:
            return jsonify(json.load(f))
    return jsonify({"_meta": {"generated": None}, "countries": {}}), 200


@app.route("/run_fetch", methods=["POST"])
def run_fetch():
    """Trigger fetch_external_forecasts.py as a background subprocess."""
    if _fetch_state["running"]:
        return jsonify({"ok": False, "error": "Fetch already in progress"}), 409

    def _run():
        _fetch_state["running"]    = True
        _fetch_state["last_error"] = None
        try:
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_external_forecasts.py")
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                _fetch_state["last_error"] = result.stderr[-500:] if result.stderr else "Unknown error"
        except Exception as e:
            _fetch_state["last_error"] = str(e)
        finally:
            _fetch_state["running"]  = False
            _fetch_state["last_run"] = datetime.utcnow().isoformat() + "Z"

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "Fetch started in background"})


@app.route("/fetch_status", methods=["GET"])
def fetch_status():
    return jsonify(_fetch_state)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "server": "MacroSnaps Forecast CMS", "time": datetime.utcnow().isoformat() + "Z"})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n──────────────────────────────────────────────")
    print("  MacroSnaps Forecast CMS — local proxy")
    print("  http://localhost:5050")
    print("──────────────────────────────────────────────")

    if SHEET_ID == "YOUR_MACRO_STATS_SHEET_ID_HERE":
        print("\n  ⚠  SHEET_ID not set. Add MACRO_STATS_SHEET_ID to .env")

    if not os.path.exists(SERVICE_ACCOUNT):
        print(f"\n  ⚠  Service account file not found: {SERVICE_ACCOUNT}")
        print("     Set GOOGLE_SERVICE_ACCOUNT_FILE in .env if using a different path.")

    print()
    app.run(port=5050, debug=False)
