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

        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        resume_path = os.getenv("RESUME_PATH")  # ✅ Load resume path

        if linkedin_email and linkedin_password:
            logging.info("✅ LinkedIn credentials loaded from .env.")
        else:
            logging.critical("🚨 Failed to load LinkedIn credentials. Check your .env file.")

        if openai_api_key:
            logging.info("✅ OpenAI API Key loaded from .env.")
        else:
            logging.critical("🚨 Failed to load OpenAI API Key. Check your .env file.")

        if gemini_api_key:
            logging.info("✅ Gemini API Key loaded from .env.")
        else:
            logging.warning("⚠️ GEMINI_API_KEY not found in .env file. Gemini API will not be available.")

        if resume_path:
            logging.info(f"✅ Resume path loaded: {resume_path} from env.")
        else:
            logging.warning("⚠️ RESUME_PATH not found in .env file. Default resume path will be used.")

# ✅ Example usage
if __name__ == "__main__":
    config_loader = EnvConfigLoader()
