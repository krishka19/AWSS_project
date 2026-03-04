# hardware/ir_sensor.py
"""
IR Breakbeam Sensor using RPi.GPIO.
Logic: HIGH = clear, LOW = broken (bag detected).
"""

import time
import RPi.GPIO as GPIO

IR_PIN_DEFAULT = 23
IR_CLEAR_LEVEL = GPIO.HIGH
IR_BROKEN_LEVEL = GPIO.LOW


class IRSensor:
    def __init__(self, pin=IR_PIN_DEFAULT):
        self.pin = pin

        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"  - IR sensor initialized on GPIO {self.pin}")
        print("    Logic: HIGH=clear, LOW=broken")

    def is_clear(self) -> bool:
        return GPIO.input(self.pin) == IR_CLEAR_LEVEL

    def is_broken(self) -> bool:
        return GPIO.input(self.pin) == IR_BROKEN_LEVEL

    def wait_for_bag(self, debounce_ms=80):
        """Block until beam is broken (bag detected). Includes debounce."""
        while self.is_clear():
            time.sleep(0.01)

        t0 = time.time()
        while (time.time() - t0) < (debounce_ms / 1000.0):
            if self.is_clear():
                return self.wait_for_bag(debounce_ms=debounce_ms)
            time.sleep(0.005)

        return True

    def verify_sensor(self, timeout=5) -> bool:
        """Verify beam is mostly clear — sanity check on startup."""
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
