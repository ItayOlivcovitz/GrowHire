import os
import openai
import logging
import re


# ✅ Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ChatGPT:
    def __init__(self):
        """Initialize ChatGPT API client with the API key from environment variables."""
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY is missing. Set it in your environment variables.")
            raise ValueError("Missing OpenAI API Key")

        openai.api_key = self.api_key  # ✅ Set the API key

        logger.info("✅ ChatGPT API initialized successfully.")

    def ask(self, prompt, model="gpt-4o-mini", max_tokens=500):
        """
        Sends a prompt to OpenAI's ChatGPT API and returns the response.
        
        Args:
            prompt (str): The text to send to ChatGPT.
            model (str): The GPT model to use (default: "gpt-4o-mini").
            max_tokens (int): Maximum number of tokens to generate (default: 500).

        Returns:
            dict: A dictionary containing either the response text or an error.
                  {"response": "ChatGPT's answer"} or {"error": "Error message"}.
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )

            # ✅ Safely extract the response text
            if "choices" in response and response["choices"]:
                response_text = response["choices"][0].get("message", {}).get("content", "").strip()
                
                if response_text:
                    logger.info("✅ Successfully retrieved ChatGPT response.")
                    return {"response": response_text}  # ✅ Always return a dictionary

            # If we reach here, something went wrong
            logger.error("❌ ChatGPT response was empty or invalid.")
            return {"error": "No response from ChatGPT"}

        except Exception as e:
            logger.error(f"❌ Failed to get response from ChatGPT: {e}")
            return {"error": str(e)}  # ✅ Return errors as dictionary
   
