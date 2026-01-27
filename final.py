# final.py
import cv2
import time
import os
from datetime import datetime
import random
import numpy as np

class DummyIRSensor:
    def wait_for_bag(self):
        time.sleep(3)  # simulate sensor trigger every 3 seconds


class AWSSSystem:
    def __init__(self, delay_after_trigger=1.0):
        self.delay = delay_after_trigger
        self.running = False
        self.results_log = []
        self.capture_dir = "data/captures"
        os.makedirs(self.capture_dir, exist_ok=True)
        self.ir_sensor = DummyIRSensor()

    def start(self):
        self.running = True
        print("System started")

    def stop(self):
        self.running = False
        print("System stopped")

    def _get_frame(self):
        """
        Returns a valid uint8 BGR image (numpy array).
        Uses dummy.jpg if present; otherwise generates a fallback frame.
        """
        if os.path.exists("dummy.jpg"):
            img = cv2.imread("dummy.jpg")
            if img is not None:
                return img

        # Fallback: bright frame with text so you can see updates in dashboard
        img = np.full((480, 640, 3), 30, dtype=np.uint8)  # dark gray background
        cv2.putText(
            img,
            "AWSS CAPTURE",
            (170, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (150, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 200),
            2,
            cv2.LINE_AA,
        )
        return img

    def process_bag(self):
        time.sleep(self.delay)

        # Simulated classification
        category = random.choice(["RECYCLING", "COMPOST", "GARBAGE"])
        confidence = round(random.uniform(0.7, 0.95), 2)

        filename = f"bag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(self.capture_dir, filename)

        # Valid image (dummy.jpg if available, else generated)
        img = self._get_frame()

        # Ensure output directory exists (safe)
        os.makedirs(self.capture_dir, exist_ok=True)

        # Save capture
        ok = cv2.imwrite(image_path, img)
        if not ok:
            raise RuntimeError(f"Failed to write image to {image_path}")

        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "confidence": float(confidence),
            "reason": "HSV color threshold matched",
            "image_path": image_path,
            "image_filename": filename,  # easier for Flask/frontend to serve
        }

        self.results_log.append(result)
        return result
