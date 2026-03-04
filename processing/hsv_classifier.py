# processing/hsv_classifier.py
"""
HSV-based bag colour classifier.
Uses corrected HSV ranges to classify bags as RECYCLING, COMPOST, or GARBAGE.
"""

import cv2
import numpy as np


class HSVBagClassifier:
    def __init__(self):
        print("  - HSV Classifier initialized (using corrected ranges)")

        self.hsv_ranges = {
            "blue": {
                "lower": np.array([15, 50, 170]),
                "upper": np.array([50, 255, 255]),
            },
            "green": {
                "lower": np.array([51, 40, 120]),
                "upper": np.array([90, 255, 255]),
            },
            "black": {
                "lower": np.array([0, 0, 0]),
                "upper": np.array([179, 255, 100]),
            },
        }

        self.categories = {
            "black": "GARBAGE",
            "blue":  "RECYCLING",
            "green": "COMPOST",
        }

    def classify_hsv(self, hsv_image) -> dict:
        """
        Classify a bag from an HSV image.

        Returns a dict with keys:
            color, category, hsv, confidence, reason, color_matches
        """
        h, w = hsv_image.shape[:2]
        roi = hsv_image[h // 4: 3 * h // 4, w // 4: 3 * w // 4]

        avg_h, avg_s, avg_v = np.mean(roi, axis=(0, 1))
        color_matches = {}

        for color_name, r in self.hsv_ranges.items():
            mask = cv2.inRange(roi, r["lower"], r["upper"])
            match_pct = (np.sum(mask > 0) / mask.size) * 100.0
            color_matches[color_name] = match_pct

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

        return {
            "color": color,
            "category": self.categories[color],
            "hsv": {"h": float(avg_h), "s": float(avg_s), "v": float(avg_v)},
            "confidence": float(confidence),
            "reason": reason,
            "color_matches": {k: float(v) for k, v in color_matches.items()},
        }
