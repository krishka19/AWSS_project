# hardware/flap_controller.py
"""
FlapController — directs the physical flap/gate to route a bag to the correct bin.

Based on the CAD design:
    - Single servo mounted inside the sorting chamber (connected via Freenove GPIO breakout board)
    - Flap pivots to one of three positions: left (green ramp), right (yellow ramp), center (straight down)
    - One bin per direction

Uses RPi.GPIO software PWM at 50 Hz (standard servo frequency).
Duty cycle formula: duty = angle / 18 + 2  (maps 0-180 deg to 2-12% duty cycle)

TODO:
    - Set SERVO_PIN to the correct BCM GPIO pin once wiring is confirmed
    - Calibrate CATEGORY_ANGLES against the real physical build
    - Verify MIN_DUTY and MAX_DUTY match your specific servo model
      (most standard servos: 2.5 at 0 deg, 12.5 at 180 deg — adjust if movement is off)
"""

import time
import RPi.GPIO as GPIO


# ---------------------------------------------------------------------------
# Pin and PWM config — update when hardware is confirmed
# ---------------------------------------------------------------------------
SERVO_PIN = None   # TODO: set BCM GPIO pin number (e.g. 18)

PWM_FREQUENCY = 50   # Hz — standard for most hobby servos

# Duty cycle bounds — adjust if servo doesn't reach full range
MIN_DUTY = 2.0    # corresponds to ~0 degrees
MAX_DUTY = 12.0   # corresponds to ~180 degrees

# Angle map: category -> servo angle (degrees)
# Based on CAD: green ramp (left), yellow ramp (right), straight down (center)
# TODO: calibrate these angles against the real physical build
CATEGORY_ANGLES = {
    "RECYCLING": 180,   # flap diverts to yellow ramp (right)
    "COMPOST":   0,     # flap diverts to green ramp (left)
    "GARBAGE":   90,    # flap neutral — bag falls straight down
}

NEUTRAL_ANGLE    = 90        # resting angle between bags
NEUTRAL_POSITION = "closed"
MOVE_DELAY       = 0.5       # seconds to allow servo to reach position


class FlapController:
    """
    Controls a single servo-driven flap to route bags to the correct bin.
    Uses RPi.GPIO software PWM via the Freenove GPIO breakout board.
    """

    def __init__(self, servo_pin=SERVO_PIN):
        self.servo_pin = servo_pin
        self.current_position = NEUTRAL_POSITION
        self._pwm = None

        if self.servo_pin is not None:
            self._setup_gpio()
            print(f"  - FlapController initialized on GPIO {self.servo_pin}")
        else:
            print("  - FlapController initialized (servo_pin=None — log-only until pin is set)")

    def _setup_gpio(self):
        """Configure GPIO pin and start PWM."""
        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.servo_pin, GPIO.OUT)
        self._pwm = GPIO.PWM(self.servo_pin, PWM_FREQUENCY)
        self._pwm.start(0)  # start with no signal

    def _angle_to_duty(self, angle: float) -> float:
        """
        Convert an angle (0-180 degrees) to a PWM duty cycle percentage.
        Linear map: 0 deg -> MIN_DUTY, 180 deg -> MAX_DUTY
        """
        angle = max(0.0, min(180.0, angle))  # clamp to valid range
        return MIN_DUTY + (angle / 180.0) * (MAX_DUTY - MIN_DUTY)

    def move_servo(self, angle: float) -> None:
        """
        Move the flap servo to the given angle (0-180 degrees).
        Logs the action regardless of whether pin is set.
        """
        print(f"  [FlapController] move_servo({angle} deg)")

        if self._pwm is None:
            print(f"    servo_pin not set — skipping actuation")
            return

        duty = self._angle_to_duty(angle)
        print(f"    duty cycle = {duty:.2f}%  (pin {self.servo_pin})")

        self._pwm.ChangeDutyCycle(duty)
        time.sleep(MOVE_DELAY)
        self._pwm.ChangeDutyCycle(0)  # stop signal to prevent servo jitter

    def direct_bag(self, category: str) -> None:
        """
        Route a bag to the correct bin based on its category.
        Called by AWSSSystem after classification.
        """
        angle = CATEGORY_ANGLES.get(category.upper())

        if angle is None:
            print(f"  [FlapController] Unknown category '{category}' — flap not moved")
            return

        print(f"  [FlapController] Routing bag to {category} ({angle} deg)")
        self.move_servo(angle)
        self.current_position = category

    def reset_position(self) -> None:
        """Return flap to neutral/center position between bags."""
        print(f"  [FlapController] Resetting to neutral ({NEUTRAL_ANGLE} deg)")
        self.move_servo(NEUTRAL_ANGLE)
        self.current_position = NEUTRAL_POSITION

    def cleanup(self):
        """Stop PWM and release GPIO pin."""
        try:
            if self._pwm is not None:
                self._pwm.stop()
            if self.servo_pin is not None:
                GPIO.cleanup(self.servo_pin)
        except Exception:
            pass