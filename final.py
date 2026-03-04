# final.py
"""
AWSS Engine — public import surface.

web/app.py does:
    from final import AWSSSystem

This file stays untouched so the web app never needs to change.
All logic now lives in the modular package structure:

    hardware/
        ir_sensor.py
        camera.py
        flap_controller.py      ← TBD stub
        bin_level_sensor.py     ← TBD stub
    processing/
        hsv_classifier.py
    utilities/
        storage_manager.py
        notification_service.py ← TBD stub
    core/
        awss_system.py          ← AWSSSystem lives here
"""

from core.awss_system import AWSSSystem  # noqa: F401  (re-export for app.py)