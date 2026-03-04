# utilities/storage_manager.py
"""
StorageManager — handles saving captured images and writing log entries.
"""

import os
import cv2
from datetime import datetime


class StorageManager:
    def __init__(self, capture_dir="data/captures", log_dir="data/logs"):
        self.capture_dir = capture_dir
        self.log_dir = log_dir
        os.makedirs(self.capture_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        print(f"  - StorageManager initialized")
        print(f"    captures → {self.capture_dir}")
        print(f"    logs     → {self.log_dir}")

    def get_capture_path(self) -> tuple[str, str]:
        """
        Generate a timestamped capture filename.
        Returns (full_path, filename).
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bag_{ts}.jpg"
        full_path = os.path.join(self.capture_dir, filename)
        return full_path, filename

    def save_image(self, frame_bgr) -> tuple[str, str]:
        """
        Save a BGR frame to disk. Returns (full_path, filename).
        """
        path, filename = self.get_capture_path()
        ok = cv2.imwrite(path, frame_bgr)
        if not ok:
            raise RuntimeError(f"Failed to write image to {path}")
        return path, filename

    def save_log_entry(self, entry: dict):
        """
        Append a detection result to today's log file.
        """
        log_file = os.path.join(
            self.log_dir,
            f"awss_log_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        with open(log_file, "a") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Time:       {entry.get('timestamp', '—')}\n")
            f.write(f"Color:      {entry.get('color', '—')}\n")
            f.write(f"Category:   {entry.get('category', '—')}\n")
            hsv = entry.get("hsv") or {}
            f.write(
                f"HSV:        H={hsv.get('h', '—')}, "
                f"S={hsv.get('s', '—')}, "
                f"V={hsv.get('v', '—')}\n"
            )
            f.write(f"Confidence: {entry.get('confidence', 0):.1f}%\n")
            f.write(f"Reason:     {entry.get('reason', '—')}\n")
            f.write(f"Image:      {entry.get('image_path', '—')}\n")
