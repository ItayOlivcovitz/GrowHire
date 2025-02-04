import os
import logging
import re
import ollama

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class OllamaClient:
    def __init__(self):
        """Initialize Ollama API client (no API key needed)."""
        logger.info("✅ Ollama API initialized successfully.")

    def ask(self, prompt, model="mistral", max_tokens=500):
        """
        Sends a prompt to Ollama and returns the response.

        Args:
            prompt (str): The text to send to Ollama.
            model (str): The Ollama model to use (default: "mistral").
            max_tokens (int): Maximum number of tokens to generate (default: 500).

        Returns:
            dict: A dictionary containing either the response text or an error.
                  {"response": "Ollama's answer"} or {"error": "Error message"}.
        """
        try:
            response = ollama.chat(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )

            if "message" in response and response["message"]:
                response_text = response["message"]["content"].strip()

                if response_text:
                    logger.info("✅ Successfully retrieved Ollama response.")
                    return {"response": response_text}

            logger.error("❌ Ollama response was empty or invalid.")
            return {"error": "No response from Ollama"}

        except Exception as e:
            logger.error(f"❌ Failed to get response from Ollama: {e}")
            return {"error": str(e)}

    def get_match_score(self, prompt, model="deepseek-r1:8b"):
        response = self.ask(prompt, model=model)
        
        if "response" not in response:
            logger.error("❌ No valid response received from Ollama.")
            return None

        response_text = response["response"]

        match = re.search(r"(?i)\bmatch score:\s*(\d+)%", response_text)
        if match:
            match_score = int(match.group(1))
            logger.info(f"🎯 Extracted Match Score: {match_score}%")
            return match_score

        logger.error("❌ Failed to extract match score from response.")
        return None


if __name__ == "__main__":
    chat_gpt = OllamaClient()

    example_prompt = """
    You are an AI recruiter. Compare this resume with the job description.
    Provide a match score (0-100%) and list missing skills.

    ### Resume:
    Experienced software engineer skilled in Python, Java, and SQL. 
    Worked with RESTful APIs, Flask, and database management.

    ### Job Description:
    Looking for a senior backend engineer with strong knowledge of Django, 
    PostgreSQL, and real-time streaming using Kafka.

    ### Output Format:
    - Match Score: XX%
    - Missing Skills: (List)
    - Strengths: (List)
    - Recommendations: (How to improve)
    """

    match_score = chat_gpt.get_match_score(example_prompt)

    if match_score is not None:
        print(f"🎯 Job Match Score: {match_score}%")
    else:
        print("❌ Error: Could not retrieve match score.")
