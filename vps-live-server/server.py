"""
Kelly Live Status Server
Runs on the VPS. Returns {"live": true/false} based on schedule + manual override.

Setup:
  pip install flask
  python server.py

Then proxy through nginx with SSL (see nginx.conf.example)
"""

from flask import Flask, jsonify, request
from datetime import datetime
import pytz

app = Flask(__name__)

TOGGLE_KEY = "CHANGE_ME_TO_A_SECRET"  # set a strong secret before deploying

# Manual override: None = use schedule, True = force live, False = force offline
manual_override = None

LONDON = pytz.timezone("Europe/London")

STREAM_DAYS  = {2, 3, 4, 5, 6}  # Wed=2, Thu=3, Fri=4, Sat=5, Sun=6 (Python weekday)
CARRY_DAYS   = {3, 4, 5, 6, 0}  # Thu=3, Fri=4, Sat=5, Sun=6, Mon=0

def is_on_schedule():
    now = datetime.now(LONDON)
    d = now.weekday()   # Mon=0 ... Sun=6
    h = now.hour
    evening   = d in STREAM_DAYS and h >= 21
    late_night = d in CARRY_DAYS and h < 1
    return evening or late_night


@app.route("/live")
def live_status():
    live = manual_override if manual_override is not None else is_on_schedule()
    return jsonify({
        "live": live,
        "mode": "manual" if manual_override is not None else "schedule"
    })


@app.route("/toggle", methods=["POST"])
def toggle():
    global manual_override
    key = request.args.get("key", "")
    if key != TOGGLE_KEY:
        return jsonify({"error": "forbidden"}), 403

    state = request.args.get("state", "").lower()
    if state == "live":
        manual_override = True
    elif state == "offline":
        manual_override = False
    elif state == "auto":
        manual_override = None
    else:
        return jsonify({"error": "use ?state=live, ?state=offline, or ?state=auto"}), 400

    return jsonify({"ok": True, "mode": "manual" if manual_override is not None else "schedule",
                    "live": manual_override if manual_override is not None else is_on_schedule()})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
