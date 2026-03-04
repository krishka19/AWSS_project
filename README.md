# AWSS — Automatic Waste Sorting System

A Raspberry Pi-based system that uses an IR breakbeam sensor and camera to automatically classify waste bags as **Recycling**, **Compost**, or **Garbage** using HSV colour detection. Results are displayed on a live web dashboard.

---

## How It Works

1. A bag breaks the IR beam → system triggers
2. Pi camera captures an image
3. HSV classifier identifies the bag colour (blue → Recycling, green → Compost, black → Garbage)
4. Result is logged and displayed on the dashboard
5. *(TBD)* Flap controller routes the bag to the correct bin

---

## Project Structure

```
project/
├── final.py                        # Entry point for the web app (re-exports AWSSSystem)
├── web/
│   ├── app.py                      # Flask backend — start/stop API + dashboard serving
│   ├── templates/index.html        # Dashboard UI
│   └── static/
│       ├── app.js                  # Frontend logic (polls /api/status every 1s)
│       └── styles.css              # Dashboard styles
├── hardware/
│   ├── ir_sensor.py                # IR breakbeam sensor (RPi.GPIO)
│   ├── camera.py                   # Pi camera wrapper (Picamera2)
│   ├── flap_controller.py          # ⚠️ TBD — servo-driven flap
│   └── bin_level_sensor.py         # ⚠️ TBD — bin fill detection
├── processing/
│   └── hsv_classifier.py           # HSV-based colour classifier
├── utilities/
│   ├── storage_manager.py          # Image saving + log writing
│   └── notification_service.py     # ⚠️ TBD — operator alerts
└── core/
    └── awss_system.py              # Main engine — wires all components together
```

---

## How to Run

**1. Install dependencies**
```bash
pip install flask opencv-python picamera2
```

**2. Run from the project root**
```bash
python web/app.py
```

**3. Open the dashboard**
```
http://<raspberry-pi-ip>:5050
```

**4. Click Start** in the dashboard to begin scanning.

> ⚠️ Always run from the project root, not from inside the `web/` folder.

---

## TBD Components

Three components are stubbed out pending hardware confirmation. They currently **log their intended actions** instead of actuating real hardware, so the rest of the system runs normally in the meantime.

### `hardware/flap_controller.py` — FlapController
Routes the bag to the correct bin via servo.
- Set `SERVO1_PIN` and `SERVO2_PIN` to the correct BCM GPIO pins
- Implement `move_servo()` with real servo control (RPi.GPIO, pigpio, or adafruit)
- Adjust `CATEGORY_ANGLES` to match your physical gate geometry

### `hardware/bin_level_sensor.py` — BinLevelSensor
Detects when a bin is full.
- Set `pin` for each bin sensor in `core/awss_system.py`
- Implement `is_full()` with real sensor reads (ultrasonic, ToF, weight, etc.)
- Adjust `FULL_THRESHOLD_CM` to match your sensor

### `utilities/notification_service.py` — NotificationService
Alerts the operator when a bin is full or the system changes state.
- Implement `notify_bin_full()` and `notify_system_status()` with your chosen channel (buzzer, LED, email, SMS, etc.)

> Each stub file has `TODO` comments marking exactly where to add the hardware-specific code.