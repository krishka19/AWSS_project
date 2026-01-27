# final.py
import cv2
import time
import os
from datetime import datetime
import random

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

    def process_bag(self):
        time.sleep(self.delay)

        # Simulated classification
        category = random.choice(["RECYCLING", "COMPOST", "GARBAGE"])
        confidence = round(random.uniform(0.7, 0.95), 2)

        filename = f"bag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(self.capture_dir, filename)

        # Fake image (black frame)
        img = 255 * (cv2.imread("dummy.jpg") if os.path.exists("dummy.jpg") else cv2.UMat(480, 640, cv2.CV_8UC3))
        cv2.imwrite(image_path, img)

        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "confidence": confidence,
            "reason": "HSV color threshold matched",
            "image_path": image_path
        }

        self.results_log.append(result)
        return result
