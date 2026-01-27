# web/app.py
import threading
import sys
import os
from flask import Flask, jsonify, render_template, send_file
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from final import AWSSSystem

app = Flask(__name__)

system = None
thread = None
state = {
    "running": False,
    "last": None,
    "history": []
}


def worker():
    global system
    while state["running"]:
        system.ir_sensor.wait_for_bag()
        if not state["running"]:
            break
        result = system.process_bag()
        state["last"] = result
        state["history"].insert(0, result)
        state["history"] = state["history"][:20]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start():
    global system, thread
    if not state["running"]:
        system = AWSSSystem()
        system.start()
        state["running"] = True
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    return jsonify({"running": True})


@app.route("/api/stop", methods=["POST"])
def stop():
    global system
    state["running"] = False
    if system:
        system.stop()
    return jsonify({"running": False})


@app.route("/api/status")
def status():
    return jsonify(state)


@app.route("/latest-image")
def latest_image():
    if state["last"] and os.path.exists(state["last"]["image_path"]):
        return send_file(state["last"]["image_path"], mimetype="image/jpeg")
    return ("No image", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
