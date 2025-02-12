import os
import requests
import logging

# ✅ Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ChatService:
    def __init__(self):
        """Initialize the AI-Chat-Service API client."""
        self.api_url = os.getenv("AI_CHAT_SERVICE_URL", "")  # Default to localhost
        logger.info(f"✅ Chat Service initialized. API URL: {self.api_url}")

    def ask(self, prompt):
        try:
            response = requests.post(self.api_url, json={"prompt": prompt}, timeout=100)

            # ✅ Log full raw response for debugging
            #logger.info(f"🔄 Raw Response from AI-Chat-Service: {response.status_code} - {response.text}")

            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response")  # ✅ Use .get() to avoid KeyError

                if response_text:
                    logger.info("✅ Successfully retrieved response from AI-Chat-Service.")
                    return {"response": response_text}

                logger.error(f"❌ Invalid response format from AI-Chat-Service: {data}")
                return {"error": "Invalid response format: Missing 'response' key"}

            else:
                logger.error(f"❌ AI-Chat-Service returned error: {response.status_code} - {response.text}")
                return {"error": f"Server error {response.status_code}: {response.text}"}

        except requests.RequestException as e:
            logger.error(f"❌ Failed to connect to AI-Chat-Service: {e}")
            return {"error": f"Connection error: {str(e)}"}


def main():
    """Test the ChatService class."""
    chat_service = ChatService()
    
    prompt = input("Enter your message: ")  # ✅ Get user input
    response = chat_service.ask(prompt)  # ✅ Send prompt to AI-Chat-Service
    
    print("\n💬 Response from AI-Chat-Service:")
    print(response)


if __name__ == "__main__":
    main()  # ✅ Run the main function when the script is executed
