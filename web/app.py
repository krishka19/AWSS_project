# web/app.py
import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, send_file

# Allow importing final.py from project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from final import AWSSSystem  # uses your existing hardware + CV logic

app = Flask(__name__)

system = None
worker_thread = None
lock = threading.Lock()

STATE = {
    "running": False,
    "startedAt": None,
    "last": None,        # latest detection (dict)
    "history": [],       # list of detections
    "lastImagePath": None
}
MAX_HISTORY = 20


def _push_history(item: dict):
    STATE["history"].insert(0, item)
    if len(STATE["history"]) > MAX_HISTORY:
        STATE["history"] = STATE["history"][:MAX_HISTORY]


def worker_loop():
    """
    Background loop:
    wait for IR trigger -> process bag -> update STATE -> cooldown
    """
    global system

    while True:
        with lock:
            if not STATE["running"]:
                break

        # Wait for a bag (blocking call)
        system.ir_sensor.wait_for_bag()

        with lock:
            if not STATE["running"]:
                break

        # Process bag (capture image + classify)
        try:
            result = system.process_bag()  # your function already captures/saves image + returns result dict

            # Find latest image path from your results_log (more detailed than result)
            image_path = None
            if getattr(system, "results_log", None):
                image_path = system.results_log[-1].get("image_path")

            payload = {
                "timestamp": datetime.now().isoformat(),
                "category": (result or {}).get("category", "UNKNOWN"),
                "color": (result or {}).get("color", "unknown"),
                "confidence": float((result or {}).get("confidence", 0)),
                "reason": (result or {}).get("reason", ""),
                "hsv": (result or {}).get("hsv", None),
                "image_path": image_path
            }

            with lock:
                STATE["last"] = payload
                STATE["lastImagePath"] = image_path
                _push_history(payload)

        except Exception as e:
            with lock:
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "category": "ERROR",
                    "color": "error",
                    "confidence": 0.0,
                    "reason": str(e),
                    "hsv": None,
                    "image_path": None
                }
                STATE["last"] = payload
                _push_history(payload)

        # Cooldown similar to your run()
        # wait for beam to clear, then short delay before next detection
        try:
            while system.ir_sensor.is_broken():
                time.sleep(0.05)
            time.sleep(1.0)
        except Exception:
            pass


@app.route("/api/start", methods=["POST"])
def api_start():
    global system, worker_thread

    with lock:
        if STATE["running"]:
            return jsonify({"ok": True, "message": "Already running"}), 200

        system = AWSSSystem(delay_after_trigger=1.0)
        system.start()

        STATE["running"] = True
        STATE["startedAt"] = datetime.now().isoformat()
        STATE["last"] = None
        STATE["history"] = []
        STATE["lastImagePath"] = None

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()

    return jsonify({"ok": True, "message": "Started"}), 200


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global system

    with lock:
        if not STATE["running"]:
            return jsonify({"ok": True, "message": "Already stopped"}), 200
        STATE["running"] = False

    # Stop hardware safely
    try:
        if system:
            system.stop()
    except Exception:
        pass

    return jsonify({"ok": True, "message": "Stopped"}), 200


@app.route("/api/status")
def api_status():
    with lock:
        return jsonify({
            "running": STATE["running"],
            "startedAt": STATE["startedAt"],
            "last": STATE["last"],
            "history": STATE["history"],
            "lastImagePath": STATE["lastImagePath"]
        })


@app.route("/latest-image")
def latest_image():
    with lock:
        p = STATE["lastImagePath"]

    if not p:
        return ("No image yet", 404)

    # Your final.py saves relative paths like "captures/images/..."
    abs_path = p if os.path.isabs(p) else os.path.join(BASE_DIR, p)

    if not os.path.exists(abs_path):
        return ("Image not found", 404)

    return send_file(abs_path, mimetype="image/jpeg", conditional=False)


@app.route("/")
def home():
    # If you already have your capstone UI in web/templates/index.html, keep it.
    # This returns a simple message so you can confirm server is up even without templates.
    return """
    <h2>AWSS Web Server is running.</h2>
    <p>If you have the UI files in web/templates + web/static, open the dashboard route instead.</p>
    <p>Try: <a href="/api/status">/api/status</a></p>
    """


if __name__ == "__main__":
    # Use 5050 (safe on macOS, also fine on Pi)
    app.run(host="0.0.0.0", port=5050, debug=False)
