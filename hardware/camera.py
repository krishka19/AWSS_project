# hardware/camera.py
"""
Pi Camera wrapper using Picamera2.
Encapsulates configuration, start/stop, and frame capture.
"""

import time
from picamera2 import Picamera2


class Camera:
    def __init__(self, resolution=(1920, 1080)):
        self.resolution = resolution
        self.is_running = False

        print("  - Setting up Pi Camera (Picamera2)...")
        self._camera = Picamera2()
        config = self._camera.create_still_configuration(
            main={"size": self.resolution, "format": "RGB888"}
        )
        self._camera.configure(config)
        print(f"  - Camera configured at {resolution[0]}x{resolution[1]}")

    def start(self):
        if self.is_running:
            return
        self._camera.start()
        time.sleep(1.5)  # warmup
        self.is_running = True
        print("  ✓ Camera started")

    def stop(self):
        if not self.is_running:
            return
        try:
            self._camera.stop()
        except Exception:
            pass
        self.is_running = False
        print("  ✓ Camera stopped")

    def capture_array(self):
        """Capture a frame and return as RGB numpy array."""
        if not self.is_running:
            raise RuntimeError("Camera is not running. Call start() first.")
        return self._camera.capture_array()
