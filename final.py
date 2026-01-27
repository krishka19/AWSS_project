# final.py
#!/usr/bin/env python3
"""
AWSS Engine (final.py)
- Real IR sensor (RPi.GPIO) + real Pi camera (Picamera2)
- HSV-based classification (explainable)
- Saves captures to data/captures/
- Saves logs to data/logs/
- Designed to be IMPORTED by Flask (do not run as main for the dashboard)
"""

from picamera2 import Picamera2
import RPi.GPIO as GPIO
import cv2
import numpy as np
import time
import os
from datetime import datetime

# ====== HARDWARE CONFIG ======
IR_PIN_DEFAULT = 23  # BCM numbering
# Old logic in your file: HIGH=clear, LOW=broken
IR_CLEAR_LEVEL = GPIO.HIGH
IR_BROKEN_LEVEL = GPIO.LOW


# ====== IR SENSOR ======
class IRSensor:
    """IR Breakbeam sensor using RPi.GPIO.
    Logic: HIGH = clear, LOW = broken (bag detected)
    """

    def __init__(self, pin=IR_PIN_DEFAULT):
        self.pin = pin

        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)

        # Input with pull-up (matches your old file)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"  - IR sensor initialized on GPIO {self.pin}")
        print("    Logic: HIGH=clear, LOW=broken")

    def is_clear(self) -> bool:
        return GPIO.input(self.pin) == IR_CLEAR_LEVEL

    def is_broken(self) -> bool:
        return GPIO.input(self.pin) == IR_BROKEN_LEVEL

    def wait_for_bag(self, debounce_ms=80):
        """Block until beam is broken (bag detected). Includes small debounce."""
        # Wait for transition into broken state
        while self.is_clear():
            time.sleep(0.01)

        # Debounce: ensure it stays broken briefly
        t0 = time.time()
        while (time.time() - t0) < (debounce_ms / 1000.0):
            if self.is_clear():
                # false trigger; restart
                return self.wait_for_bag(debounce_ms=debounce_ms)
            time.sleep(0.005)

        # Confirmed bag detection
        return True

    def verify_sensor(self, timeout=5) -> bool:
        """Simple verification: beam should be mostly clear if nothing blocking."""
        print(f"\n  Verifying IR sensor for {timeout} seconds...")
        print("  Make sure beam is CLEAR (nothing blocking)")

        start_time = time.time()
        clear_count = 0
        total = 0

        while (time.time() - start_time) < timeout:
            if self.is_clear():
                clear_count += 1
            total += 1
            time.sleep(0.1)

        pct = (clear_count / max(1, total)) * 100.0
        print(f"  Beam clear: {clear_count}/{total} samples ({pct:.1f}%)")

        if pct > 90:
            print("  ✓ IR sensor looks OK")
            return True

        print("  ⚠ IR sensor may be blocked / misaligned")
        return False

    def cleanup(self):
        try:
            GPIO.cleanup(self.pin)
        except Exception:
            pass


# ====== HSV CLASSIFIER ======
class HSVBagClassifier:
    """HSV-based bag color classifier using your corrected ranges."""

    def __init__(self):
        print("  - HSV Classifier initialized (using corrected ranges)")

        # From your old file (corrected blue)
        self.hsv_ranges = {
            "blue": {
                "lower": np.array([15, 50, 170]),   # H 15-50, S 50-255, V 170-255
                "upper": np.array([50, 255, 255]),
            },
            "green": {
                "lower": np.array([51, 40, 120]),   # H 51-90 (avoid blue overlap)
                "upper": np.array([90, 255, 255]),
            },
            "black": {
                "lower": np.array([0, 0, 0]),
                "upper": np.array([179, 255, 100]),  # V < ~100
            },
        }

        self.categories = {
            "black": "GARBAGE",
            "blue": "RECYCLING",
            "green": "COMPOST",
        }

    def classify_hsv(self, hsv_image):
        # Use center ROI for stability
        h, w = hsv_image.shape[:2]
        roi = hsv_image[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]

        avg_h, avg_s, avg_v = np.mean(roi, axis=(0, 1))
        color_matches = {}

        for color_name, r in self.hsv_ranges.items():
            mask = cv2.inRange(roi, r["lower"], r["upper"])
            match_pct = (np.sum(mask > 0) / mask.size) * 100.0
            color_matches[color_name] = match_pct

        # Decision logic (from your old file idea)
        if color_matches["blue"] > 30:
            color = "blue"
            confidence = min(95.0, color_matches["blue"])
            reason = f"Blue range match: {color_matches['blue']:.1f}%"
        elif avg_v < 120:
            color = "black"
            confidence = float((120.0 - avg_v) / 120.0 * 100.0)
            confidence = max(0.0, min(95.0, confidence))
            reason = f"V={avg_v:.1f} < 120 (low brightness)"
        elif color_matches["green"] > 20:
            color = "green"
            confidence = min(95.0, color_matches["green"])
            reason = f"Green range match: {color_matches['green']:.1f}%"
        else:
            color = max(color_matches, key=color_matches.get)
            confidence = float(color_matches[color])
            reason = f"Best match: {color_matches[color]:.1f}%"

        category = self.categories[color]

        return {
            "color": color,
            "category": category,
            "hsv": {"h": float(avg_h), "s": float(avg_s), "v": float(avg_v)},
            "confidence": float(confidence),  # 0..100
            "reason": reason,
            "color_matches": {k: float(v) for k, v in color_matches.items()},
        }


# ====== AWSS ENGINE ======
class AWSSSystem:
    """
    Engine controlled by Flask:
    - start(): starts camera
    - stop(): stops camera + cleans GPIO
    - process_bag(): capture -> HSV -> result dict + save image/log
    """

    def __init__(self, delay_after_trigger=1.0, ir_pin=IR_PIN_DEFAULT):
        self.delay_after_trigger = float(delay_after_trigger)

        # Required capstone structure
        self.capture_dir = os.path.join("data", "captures")
        self.log_dir = os.path.join("data", "logs")
        os.makedirs(self.capture_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        self.ir_sensor = IRSensor(pin=ir_pin)
        self.classifier = HSVBagClassifier()

        # Camera init (Picamera2)
        print("\n  - Setting up Pi Camera (Picamera2)...")
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (1920, 1080), "format": "RGB888"}
        )
        self.camera.configure(config)

        self.running = False
        self.total_bags = 0
        self.results_log = []

        print("✓ AWSSSystem initialized")

    def start(self):
        """Start camera and mark system running."""
        if self.running:
            return

        print("\nStarting camera...")
        self.camera.start()
        time.sleep(1.5)  # warmup
        self.running = True

        # Optional IR sanity check (don’t hard-exit in dashboard mode)
        try:
            self.ir_sensor.verify_sensor(timeout=2)
        except Exception:
            pass

        print("✓ System started")

    def stop(self):
        """Stop camera and cleanup."""
        self.running = False
        try:
            self.camera.stop()
        except Exception:
            pass
        try:
            self.ir_sensor.cleanup()
        except Exception:
            pass
        print("✓ System stopped")

    def _save_log(self, entry: dict):
        log_file = os.path.join(self.log_dir, f"awss_log_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(log_file, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Time: {entry['timestamp']}\n")
            f.write(f"Color: {entry.get('color','')}\n")
            f.write(f"Category: {entry.get('category','')}\n")
            hsv = entry.get("hsv") or {}
            f.write(f"HSV: H={hsv.get('h','—')}, S={hsv.get('s','—')}, V={hsv.get('v','—')}\n")
            f.write(f"Confidence: {entry.get('confidence',0):.1f}%\n")
            f.write(f"Reason: {entry.get('reason','')}\n")
            f.write(f"Image: {entry.get('image_path','')}\n")

    def process_bag(self):
        """
        Called after IR trigger by Flask worker.
        Captures image, classifies, saves, returns structured dict.
        """
        if not self.running:
            # still allow process_bag in testing, but camera should be started
            pass

        self.total_bags += 1

        # Wait for bag to settle in frame
        time.sleep(self.delay_after_trigger)

        # Capture
        ts_iso = datetime.now().isoformat()
        ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bag_{ts_name}.jpg"
        image_path = os.path.join(self.capture_dir, filename)

        frame_rgb = self.camera.capture_array()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        ok = cv2.imwrite(image_path, frame_bgr)
        if not ok:
            raise RuntimeError(f"Failed to write image to {image_path}")

        # HSV + classify
        frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        c = self.classifier.classify_hsv(frame_hsv)

        result = {
            "timestamp": ts_iso,
            "category": c["category"],
            "color": c["color"],
            "confidence": c["confidence"],   # 0..100
            "reason": c["reason"],
            "hsv": c["hsv"],
            "color_matches": c["color_matches"],
            "image_path": image_path,        # relative path used by Flask
            "image_filename": filename,
        }

        self.results_log.append(result)
        self._save_log(result)
        return result
