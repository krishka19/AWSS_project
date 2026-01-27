# web/app.py
import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, send_file, render_template, send_from_directory

# Allow importing final.py from project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from final import AWSSSystem  # uses your existing hardware + CV logic

# IMPORTANT: point Flask to web/templates and web/static
app = Flask(__name__, template_folder="templates", static_folder="static")

system = None
worker_thread = None
lock = threading.Lock()

STATE = {
    "running": False,
    "startedAt": None,
    "last": None,        # latest detection (dict)
    "history": [],       # list of detections
    "lastImagePath": None,
    "lastError": None
}
MAX_HISTORY = 20


def _push_history(item: dict):
    STATE["history"].insert(0, item)
    if len(STATE["history"]) > MAX_HISTORY:
        STATE["history"] = STATE["history"][:MAX_HISTORY]


def _safe_ir_clear_wait(ir_sensor, timeout_s=2.0):
    """
    Optional: if real sensor supports is_broken(), wait for beam to clear.
    If not supported, just return quickly.
    """
    if not hasattr(ir_sensor, "is_broken"):
        return

    t0 = time.time()
    try:
        while ir_sensor.is_broken():
            if time.time() - t0 > timeout_s:
                break
            time.sleep(0.05)
    except Exception:
        return


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
        try:
            system.ir_sensor.wait_for_bag()
        except Exception as e:
            with lock:
                STATE["lastError"] = f"IR sensor error: {e}"
            time.sleep(0.2)
            continue

        with lock:
            if not STATE["running"]:
                break

        # Process bag (capture image + classify)
        try:
            result = system.process_bag()

            image_path = (result or {}).get("image_path")

            payload = {
                "timestamp": (result or {}).get("timestamp", datetime.now().isoformat()),
                "category": (result or {}).get("category", "UNKNOWN"),
                "confidence": float((result or {}).get("confidence", 0.0)),
                "reason": (result or {}).get("reason", ""),
                "image_path": image_path,
                "image_filename": (result or {}).get("image_filename"),
            }

            with lock:
                STATE["last"] = payload
                STATE["lastImagePath"] = image_path
                STATE["lastError"] = None
                _push_history(payload)

        except Exception as e:
            with lock:
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "category": "ERROR",
                    "confidence": 0.0,
                    "reason": str(e),
                    "image_path": None,
                    "image_filename": None,
                }
                STATE["last"] = payload
                STATE["lastError"] = str(e)
                _push_history(payload)

        # Cooldown: wait for beam clear if supported, then short delay
        _safe_ir_clear_wait(system.ir_sensor, timeout_s=2.0)
        time.sleep(0.5)


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
        STATE["lastError"] = None

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
            "lastImagePath": STATE["lastImagePath"],
            "lastError": STATE["lastError"],
        })


# Latest image (most recent capture)
@app.route("/latest-image")
def latest_image():
    with lock:
        p = STATE["lastImagePath"]

    if not p:
        return ("No image yet", 404)

    abs_path = p if os.path.isabs(p) else os.path.join(BASE_DIR, p)
    if not os.path.exists(abs_path):
        return ("Image not found", 404)

    return send_file(abs_path, mimetype="image/jpeg", conditional=False)


# Optional: serve a specific image by filename (helps frontend use image_filename)
@app.route("/latest-image/<filename>")
def latest_image_by_name(filename):
    capture_dir = os.path.join(BASE_DIR, "data", "captures")
    return send_from_directory(capture_dir, filename)


# ✅ Serve the real dashboard UI
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)

