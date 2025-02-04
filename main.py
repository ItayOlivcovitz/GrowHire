import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from gui.grow_hire_gui import GrowHireGUI  # ✅ Starts the GUI
from db.job_storage import JobStorage  # ✅ Ensure the JobStorage class is imported for DB handling
from utils.env_config import EnvConfigLoader  # ✅ Ensure the EnvConfigLoader class is imported for environment configuration

# ✅ Configure Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    """Main entry point for GrowHire."""

    # ✅ Load environment variables from `.env`
    env_loader = EnvConfigLoader()
    print("🚀 Starting GrowHireBot...")

    job_storage = None  # Define job_storage at the top of the main function

    # ✅ Ensure DB is initialized
    try:
        # Initialize the JobStorage to handle DB connection
        job_storage = JobStorage()  # Automatically connects to DB when initialized
        logger.info("✅ Database connection established.")


    except Exception as e:
        logger.error(f"❌ Error initializing the database: {e}")
        return  # Exit the program if DB connection fails

    app = QApplication(sys.argv)
    window = GrowHireGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()  # ✅ This starts the program
