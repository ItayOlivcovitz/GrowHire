import os
import google.generativeai as genai
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class GeminiService:
    def __init__(self):
        """Initialize Gemini API client with the API key from environment variables."""
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logger.error("GEMINI_API_KEY is missing. Set it in your environment variables.")
            raise ValueError("Missing Gemini API Key")

        genai.configure(api_key=self.api_key)
        logger.info("Gemini API initialized successfully.")

    def ask(self, prompt, model=None, max_tokens=500):
        """
        Sends a prompt to Google's Gemini API and returns the response.
        
        Args:
            prompt (str): The text to send to Gemini.
            model (str): The Gemini model to use. If None, will auto-detect available model.
            max_tokens (int): Maximum number of tokens to generate (default: 500).

        Returns:
            dict: A dictionary containing either the response text or an error.
                  {"response": "Gemini's answer"} or {"error": "Error message"}.
        """
        try:
            # If no model specified, try to find an available one
            if model is None:
                try:
                    models = genai.list_models()
                    available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
                    if available_models:
                        model = available_models[0].split('/')[-1]  # Extract just the model name
                        logger.info(f"Using auto-detected model: {model}")
                    else:
                        model = "gemini-2.5-flash"  # Fallback to a known working model
                except Exception:
                    model = "gemini-2.5-flash"  # Fallback if listing fails
            
            # Create the model instance
            model_instance = genai.GenerativeModel(model)
            
            # Generate content with the prompt
            response = model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens
                )
            )

            # Extract the response text
            if response and response.text:
                response_text = response.text.strip()
                logger.info("Successfully retrieved Gemini response.")
                return {"response": response_text}

            # If we reach here, something went wrong
            logger.error("Gemini response was empty or invalid.")
            return {"error": "No response from Gemini"}

        except Exception as e:
            logger.error(f"Failed to get response from Gemini: {e}")
            return {"error": str(e)}
