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
    def get_match_score(self, prompt):
        """
        Sends a job-resume comparison prompt to ChatGPT and extracts the match score.

        Args:
            prompt (str): The prompt containing resume & job description for analysis.

        Returns:
            int or None: Match score (0-100) if found, otherwise None.
        """
      

        # ✅ Extract match score using regex
        score = re.search(r"(?i)\*\*\s*Match Score:\s*(\d+)%", prompt)  # ✅ More flexible regex
        if score:
            match_score = int(score.group(1))
            logger.info(f"🎯 Extracted Match Score: {match_score}%")
            return match_score

        logger.error("❌ Failed to extract match score from response.")
        return None


# ✅ Example usage
if __name__ == "__main__":
    chat_gpt = ChatGPT()

    # ✅ Example job-resume prompt
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
