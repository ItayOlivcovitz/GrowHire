import os
import logging
from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class EnvConfigLoader:
    def __init__(self):
        """
        Initialize EnvConfigLoader and load environment variables from GrowHire/.env.
        """
        self.load_environment_variables()

    def load_environment_variables(self):
        """Loads environment variables from the GrowHire/.env file."""
        env_path = find_dotenv()  # Automatically finds .env in project root

        if not env_path:
            logging.critical("🚨 .env file not found in project root. Make sure it exists.")
            return

        load_dotenv(env_path)  # Load the .env file

        # Load individual environment variables
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        resume_path = os.getenv("RESUME_PATH")
        database_url = os.getenv("DATABASE_URL")
        ai_chat_service_url = os.getenv("AI_CHAT_SERVICE_URL")
        notifications_config_file = os.getenv("NOTIFICATIONS_CONFIG_FILE")
        notifications_api = os.getenv("NOTIFICATIONS_API")

        # Validate and log
        if linkedin_email and linkedin_password:
            logging.info("✅ LinkedIn credentials loaded from .env.")
        else:
            logging.critical("🚨 Failed to load LinkedIn credentials. Check your .env file.")

        if openai_api_key:
            logging.info("✅ OpenAI API Key loaded from .env.")
        else:
            logging.critical("🚨 Failed to load OpenAI API Key. Check your .env file.")

        if resume_path:
            logging.info(f"✅ Resume path loaded: {resume_path}")
        else:
            logging.warning("⚠️ RESUME_PATH not found in .env file. Default resume path will be used.")

        if database_url:
            logging.info("✅ DATABASE_URL loaded from .env.")
        else:
            logging.warning("⚠️ DATABASE_URL not found in .env file.")

        if ai_chat_service_url:
            logging.info("✅ AI_CHAT_SERVICE_URL loaded from .env.")
        else:
            logging.warning("⚠️ AI_CHAT_SERVICE_URL not found in .env file.")

        if notifications_config_file:
            logging.info(f"✅ Notifications config file path loaded: {notifications_config_file}")
        else:
            logging.warning("⚠️ NOTIFICATIONS_CONFIG_FILE not found in .env file.")

        if notifications_api:
            logging.info(f"✅ Notifications API loaded: {notifications_api}")
        else:
            logging.warning("⚠️ NOTIFICATIONS_API not found in .env file.")
