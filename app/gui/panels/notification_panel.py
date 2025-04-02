from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox, QLabel
import logging
from app.services.notifications.send_notifications import SendNotifications

logger = logging.getLogger(__name__)

class NotificationPanel(QGroupBox):
    """
    NotificationPanel integrated with SendNotifications.
    
    When notifications are enabled, the bot starts sending scheduled events;
    when disabled, the bot stops.
    """
    def __init__(self, bot: SendNotifications, parent=None):
        """
        :param bot: An instance of SendNotifications used for scheduled events.
        :param parent: Optional parent widget.
        """
        super().__init__("🔔 Notifications", parent)
        self.bot = bot
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Checkbox to enable or disable notifications (unchecked by default)
        self.enable_checkbox = QCheckBox("Enable Notifications")
        self.enable_checkbox.setChecked(False)
        self.enable_checkbox.toggled.connect(self.on_toggle_notifications)
        layout.addWidget(self.enable_checkbox)
        
        # Label to show current status.
        self.status_label = QLabel("Notifications are disabled")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def on_toggle_notifications(self, checked):
        status = "enabled" if checked else "disabled"
        logger.info(f"Notifications have been {status}.")
        self.status_label.setText(f"Notifications are {status}.")
        
        # Start or stop the bot based on the checkbox state.
        if checked:
            self.bot.start()
        else:
            self.bot.stop()
