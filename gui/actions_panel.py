from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton
from PySide6.QtCore import QThread, QObject, Signal
import logging

logger = logging.getLogger(__name__)

class LinkedInWorker(QObject):
    """Worker class to handle LinkedIn login in a separate thread."""
    finished = Signal()

    def __init__(self, linkedin_navigator):
        super().__init__()
        self.linkedin_navigator = linkedin_navigator

    def run(self):
        """Runs the LinkedIn login process."""
        try:
            logger.info("🔄 Opening LinkedIn login...")
            self.linkedin_navigator.open_linkedin()
            logger.info("✅ LinkedIn opened successfully.")
        except Exception as e:
            logger.error(f"❌ Error while opening LinkedIn: {e}")
        finally:
            self.finished.emit()  # Notify that the task is completed


class ActionsPanel(QGroupBox):
    """Panel for LinkedIn actions like opening LinkedIn and logging in."""

    def __init__(self, growhire_bot):
        super().__init__("🚀 Actions")
        self.growhire_bot = growhire_bot
        self.thread = None  # ✅ Store thread reference
        self.worker = None  # ✅ Store worker reference
        self.initUI()

    def initUI(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # ✅ Open LinkedIn Button
        self.login_button = QPushButton("🌐 Open LinkedIn Login")
        self.login_button.clicked.connect(self.start_open_linkedin_thread)  # ✅ Runs on a separate thread
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def start_open_linkedin_thread(self):
        """Starts LinkedIn login process in a background QThread."""
        if self.thread and self.thread.isRunning():
            logger.warning("⚠️ LinkedIn login is already in progress.")
            return

        logger.info("🚀 Starting LinkedIn login process...")

        # ✅ Create the QThread and Worker
        self.thread = QThread()
        self.worker = LinkedInWorker(self.growhire_bot.linkedin_navigator)

        # ✅ Move worker to thread
        self.worker.moveToThread(self.thread)

        # ✅ Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # ✅ Start the thread
        self.thread.start()
