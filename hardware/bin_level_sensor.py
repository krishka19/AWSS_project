# hardware/bin_level_sensor.py
"""
BinLevelSensor — detects when a bin is full (e.g. ultrasonic, IR distance, weight).

⚠️  STUB: Sensor type and GPIO pins not yet confirmed by hardware team.
    All methods log their intended action and return safe default values.

TODO (hardware team):
    - Confirm sensor type (HC-SR04 ultrasonic, VL53L0X ToF, load cell, etc.)
    - Set pin and bin_type values
    - Implement is_full() with real sensor reads
    - Define a "full" threshold for your chosen sensor
"""

import random  # used only for simulated stub readings


# ---------------------------------------------------------------------------
# Placeholder config — update when hardware is confirmed
# ---------------------------------------------------------------------------
FULL_THRESHOLD_CM = 5    # TODO: distance (cm) at which bin is considered full
BIN_TYPES = ["RECYCLING", "COMPOST", "GARBAGE"]


class BinLevelSensor:
    """
    Reads a single bin's fill level and reports whether the bin is full.
    One instance per bin. Currently a log-only stub.
    """

    def __init__(self, pin: int = None, bin_type: str = "UNKNOWN"):
        self.pin = pin
        self.bin_type = bin_type

        print(f"  - BinLevelSensor initialized for '{bin_type}' bin (STUB — log-only mode)")
        print(f"    pin={pin}")
        print("    ⚠  Real sensor reads not yet implemented.")

    def is_full(self) -> bool:
        """
        Returns True if the bin is full.

        TODO: Replace stub body with real sensor read, e.g. for HC-SR04:
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, True)
            time.sleep(0.00001)
            GPIO.output(self.pin, False)
            # ... measure echo pulse width -> distance_cm
            return distance_cm < FULL_THRESHOLD_CM

        Stub currently returns False (never full) so system keeps running.
        """
        print(f"  [BinLevelSensor:{self.bin_type}] STUB: is_full() called")
        print(f"    → Would read sensor on pin {self.pin}")
        print(f"    → Returning False (stub default — bin assumed not full)")
        return False

    def get_status(self) -> str:
        """
        Returns a human-readable status string: 'OK', 'FULL', or 'UNKNOWN'.

        TODO: Use real is_full() once hardware is implemented.
        """
        print(f"  [BinLevelSensor:{self.bin_type}] STUB: get_status() called")
        # Stub: always report OK
        status = "OK"
        print(f"    → Returning status='{status}' (stub default)")
        return status
