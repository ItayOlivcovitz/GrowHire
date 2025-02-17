import logging
from PySide6.QtCore import QObject, Signal

# ✅ Initialize Logger
logger = logging.getLogger(__name__)

class LoginWorker(QObject):
    """Worker class to handle LinkedIn login in a separate thread."""
    
    finished = Signal(bool)  # ✅ Emits `True` if login succeeds, `False` if it fails

    def __init__(self, linkedin_navigator):
        super().__init__()
        self.linkedin_navigator = linkedin_navigator

    def run(self):
        """Runs the LinkedIn login process."""
        try:
            logger.info("🔄 Opening LinkedIn login...")
            success = self.linkedin_navigator.open_linkedin()  # ✅ Ensure `open_linkedin()` returns success/failure
            
            if success:
                logger.info("✅ LinkedIn opened successfully.")
                self.finished.emit(True)  # ✅ Notify UI that login succeeded
            else:
                logger.warning("⚠️ LinkedIn login failed.")
                self.finished.emit(False)  # ✅ Notify UI that login failed

        except Exception as e:
            logger.error(f"❌ Error while opening LinkedIn: {e}")
            self.finished.emit(False)  # ✅ Emit failure signal if exception occurs
