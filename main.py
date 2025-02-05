import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from gui.grow_hire_gui import GrowHireGUI  # ✅ Starts the GUI
from db.job_storage import JobStorage  # ✅ Ensure the JobStorage class is imported for DB handling
from utils.env_config import EnvConfigLoader  # ✅ Ensure the EnvConfigLoader class is imported for environment configuration
from services.grow_hire_bot import GrowHireBot
# ✅ Configure Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    """Main entry point for GrowHire."""

    # ✅ Load environment variables from `.env`
    env_loader = EnvConfigLoader()
    print("🚀 Starting GrowHireBot...")

    # ✅ Initialize LinkedIn Bot and GrowHireBot with correct resume path
    growhire_bot = GrowHireBot()

    # ✅ Start the GUI
    app = QApplication(sys.argv)
    window = GrowHireGUI(growhire_bot)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()  # ✅ This starts the program