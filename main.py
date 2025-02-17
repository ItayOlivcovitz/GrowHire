import sys
import logging
from PySide6.QtWidgets import QApplication
from app.gui.main_window import GrowHireGUI  # ✅ Updated to match modularized GUI structure
from db.job_storage import JobStorage  # ✅ Ensures JobStorage is initialized before GUI
from app.utils.env_config import EnvConfigLoader  # ✅ Ensures environment variables are loaded
from app.services.grow_hire_bot import GrowHireBot


def setup_logger():
    """Configures the logger for GrowHire."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logger


def main():
    """Main entry point for GrowHire."""
    logger = setup_logger()

    try:
        # ✅ Load environment variables
        env_loader = EnvConfigLoader()
        logger.info("✅ Environment variables loaded successfully.")

        # ✅ Initialize database storage
        job_storage = JobStorage()
        logger.info("✅ Database initialized successfully.")

        # ✅ Initialize GrowHireBot
        logger.info("🚀 Starting GrowHireBot...")
        growhire_bot = GrowHireBot()

        # ✅ Start the GUI application
        app = QApplication(sys.argv)
        window = GrowHireGUI(growhire_bot)
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"❌ Fatal error occurred: {e}", exc_info=True)
        sys.exit(1)  # Ensures a clean exit on failure


if __name__ == "__main__":
    main()  # ✅ Start the program
