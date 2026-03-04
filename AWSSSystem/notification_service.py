# utilities/notification_service.py
"""
NotificationService — alerts operators when a bin is full or the system needs attention.

⚠️  STUB: Notification channel (email, SMS, buzzer, LED, etc.) not yet confirmed.
    All methods log their intended action instead of sending real notifications.

TODO (hardware/software team):
    - Decide notification channel: buzzer GPIO, LED, email (smtplib), SMS (Twilio), etc.
    - Implement notify_bin_full() to trigger the chosen channel
    - Implement notify_system_status() for startup/shutdown alerts
"""


class NotificationService:
    """
    Sends operator alerts for bin-full events and system status changes.
    Currently a log-only stub.
    """

    def __init__(self):
        print("  - NotificationService initialized (STUB — log-only mode)")
        print("    ⚠  Real notifications not yet implemented.")

    def notify_bin_full(self, bin_type: str) -> None:
        """
        Alert the operator that a specific bin is full and needs emptying.

        Args:
            bin_type: One of 'RECYCLING', 'COMPOST', 'GARBAGE'

        TODO: Replace stub body with real notification, e.g.:
            - Trigger a buzzer: GPIO.output(BUZZER_PIN, GPIO.HIGH)
            - Send email via smtplib
            - Send SMS via Twilio API
            - Flash an LED on the corresponding bin
        """
        print(f"  [NotificationService] STUB: notify_bin_full(bin_type='{bin_type}')")
        print(f"    → Would alert operator: '{bin_type}' bin is full and needs emptying")

    def notify_system_status(self, status: str, detail: str = "") -> None:
        """
        Broadcast a system status update (e.g. started, stopped, error).

        Args:
            status: Short status label e.g. 'STARTED', 'STOPPED', 'ERROR'
            detail: Optional extra detail message

        TODO: Replace stub body with real notification channel.
        """
        msg = f"AWSS System — {status}"
        if detail:
            msg += f": {detail}"

        print(f"  [NotificationService] STUB: notify_system_status(status='{status}')")
        print(f"    → Would broadcast: \"{msg}\"")
