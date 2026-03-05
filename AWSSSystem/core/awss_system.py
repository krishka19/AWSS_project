# core/awss_system.py
"""
AWSSSystem — main engine that wires all components together.

Controlled by the Flask web app (web/app.py):
    system = AWSSSystem()
    system.start()
    result = system.process_bag()
    system.stop()
"""

import cv2
import time
from datetime import datetime

from hardware.ir_sensor import IRSensor, IR_PIN_DEFAULT
from hardware.camera import Camera
from hardware.flap_controller import FlapController
from hardware.bin_level_sensor import BinLevelSensor
from processing.hsv_classifier import HSVBagClassifier
from utilities.storage_manager import StorageManager
from utilities.notification_service import NotificationService


class AWSSSystem:
    def __init__(self, delay_after_trigger=1.0, ir_pin=IR_PIN_DEFAULT):
        self.delay_after_trigger = float(delay_after_trigger)

        print("\nInitializing AWSS components...")

        # Hardware
        self.ir_sensor      = IRSensor(pin=ir_pin)
        self.camera         = Camera(resolution=(1920, 1080))
        self.flap_controller = FlapController(servo_pin=None)  # TODO: set pin

        # One BinLevelSensor per bin (pins TBD — set to None until hardware confirmed)
        self.bin_sensors = [
            BinLevelSensor(pin=None, bin_type="RECYCLING"),
            BinLevelSensor(pin=None, bin_type="COMPOST"),
            BinLevelSensor(pin=None, bin_type="GARBAGE"),
        ]

        # Processing & utilities
        self.classifier   = HSVBagClassifier()
        self.storage      = StorageManager()
        self.notifier     = NotificationService()

        # State
        self.running     = False
        self.total_bags  = 0
        self.results_log = []

        print("✓ AWSSSystem initialized")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start camera and mark system running."""
        if self.running:
            return

        print("\nStarting AWSS system...")
        self.camera.start()
        self.running = True

        try:
            self.ir_sensor.verify_sensor(timeout=2)
        except Exception:
            pass

        self.notifier.notify_system_status("STARTED")
        print("✓ System started")

    def stop(self):
        """Stop camera, release GPIO, notify."""
        self.running = False
        self.camera.stop()
        self.ir_sensor.cleanup()
        self.flap_controller.cleanup()
        self.notifier.notify_system_status("STOPPED")
        print("✓ System stopped")

    # ------------------------------------------------------------------
    # Main processing
    # ------------------------------------------------------------------

    def process_bag(self) -> dict:
        """
        Called by the Flask worker after IR trigger.
        Captures image → classifies → routes flap → saves → returns result dict.
        """
        self.total_bags += 1

        # Let the bag settle in frame
        time.sleep(self.delay_after_trigger)

        # Capture
        ts_iso  = datetime.now().isoformat()
        frame_rgb = self.camera.capture_array()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        image_path, filename = self.storage.save_image(frame_bgr)

        # Classify
        frame_hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        c = self.classifier.classify_hsv(frame_hsv)

        # Route flap (stub logs the action)
        self.flap_controller.direct_bag(c["category"])
        time.sleep(0.5)                      # give flap time to move
        self.flap_controller.reset_position()

        # Check bin levels (stub always returns False)
        self.check_bin_levels()

        result = {
            "timestamp":      ts_iso,
            "category":       c["category"],
            "color":          c["color"],
            "confidence":     c["confidence"],   # 0..100
            "reason":         c["reason"],
            "hsv":            c["hsv"],
            "color_matches":  c["color_matches"],
            "image_path":     image_path,
            "image_filename": filename,
        }

        self.results_log.append(result)
        self.storage.save_log_entry(result)
        return result

    def check_bin_levels(self):
        """
        Check each bin's fill level and notify if full.
        Stub sensors always return False — this becomes active once hardware is wired.
        """
        for sensor in self.bin_sensors:
            if sensor.is_full():
                print(f"  ⚠ Bin full: {sensor.bin_type}")
                self.notifier.notify_bin_full(sensor.bin_type)