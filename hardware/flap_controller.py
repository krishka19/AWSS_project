# hardware/flap_controller.py
"""
FlapController — directs the physical flap/gate to route a bag to the correct bin.

⚠️  STUB: Hardware pins and servo model not yet confirmed by hardware team.
    All methods log their intended action instead of actuating real hardware.

TODO (hardware team):
    - Set servo1_pin, servo2_pin to the correct BCM GPIO pins
    - Confirm servo PWM range (min/max pulse width, frequency)
    - Implement move_servo() with real RPi.GPIO / pigpio / adafruit_servokit calls
    - Test reset_position() returns flap to neutral safely
"""


# ---------------------------------------------------------------------------
# Placeholder pin constants — update when hardware is confirmed
# ---------------------------------------------------------------------------
SERVO1_PIN = None   # TODO: set BCM pin number
SERVO2_PIN = None   # TODO: set BCM pin number

# Angle map: category -> (servo1_angle, servo2_angle)
# Adjust angles to match your physical gate geometry
CATEGORY_ANGLES = {
    "RECYCLING": (90, 0),
    "COMPOST":   (45, 90),
    "GARBAGE":   (0,  45),
}

NEUTRAL_POSITION = "closed"


class FlapController:
    """
    Controls a servo-driven flap to route bags to the correct bin.
    Currently a log-only stub — replace method bodies with real GPIO calls.
    """

    def __init__(self, servo1_pin=SERVO1_PIN, servo2_pin=SERVO2_PIN):
        self.servo1_pin = servo1_pin
        self.servo2_pin = servo2_pin
        self.current_position = NEUTRAL_POSITION

        print("  - FlapController initialized (STUB — log-only mode)")
        print(f"    servo1_pin={servo1_pin}, servo2_pin={servo2_pin}")
        print("    ⚠  Real servo actuation not yet implemented.")

    def move_servo(self, angle: float) -> None:
        """
        Move the flap servo(s) to the given angle (degrees).

        TODO: Replace with real servo control, e.g.:
            import RPi.GPIO as GPIO
            pwm = GPIO.PWM(self.servo1_pin, 50)
            pwm.start(0)
            duty = angle / 18 + 2
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.5)
            pwm.stop()
        """
        print(f"  [FlapController] STUB: move_servo(angle={angle}°) called")
        print(f"    → Would actuate servo on pin {self.servo1_pin}")

    def direct_bag(self, category: str) -> None:
        """
        Route a bag to the correct bin based on its category.
        Called by AWSSSystem after classification.
        """
        angles = CATEGORY_ANGLES.get(category.upper())

        if angles is None:
            print(f"  [FlapController] STUB: Unknown category '{category}' — flap not moved")
            return

        s1_angle, s2_angle = angles
        print(f"  [FlapController] STUB: Routing bag to {category}")
        print(f"    → Would set servo1={s1_angle}°, servo2={s2_angle}°")

        # TODO: call self.move_servo() for each servo once hardware is wired
        self.current_position = category

    def reset_position(self) -> None:
        """
        Return flap to neutral/closed position between bags.

        TODO: Move servos back to their resting angles.
        """
        print("  [FlapController] STUB: reset_position() called")
        print(f"    → Would return flap to '{NEUTRAL_POSITION}' position")
        self.current_position = NEUTRAL_POSITION
