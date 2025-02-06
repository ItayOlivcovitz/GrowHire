import time
import logging
import urllib.parse
import re
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from services.chatGpt import chat_gpt


from services.linkedinNavigator.linkedin_navigator import LinkedInNavigator
from services.pdfReader.pdf_reader import PDFReader

logger = logging.getLogger(__name__)

class JobScraper:
    """Extracts job details from LinkedIn."""
    def __init__(self, driver):
        self.driver = driver
        self.chat_gpt = chat_gpt.ChatGPT()
        self.resume_path = os.getenv("RESUME_PATH", "/Resume.pdf")
        

        self.pdf_reader = PDFReader(self.resume_path)
        self.resume_text = self.pdf_reader.get_text()

    def extract_job_descriptions(self, num_pages=1):
        """Extracts job descriptions dynamically from LinkedIn and moves through multiple pages."""
        job_list = []
        seen_jobs = set()

        for page in range(num_pages):
            time.sleep(2)  # Reduce initial wait time
            logger.info(f"📄 Scraping Page {page + 1}/{num_pages}...")

            # ✅ Locate the job list container
            job_list_xpath = "//*[@id='main']/div/div[2]/div[1]/div"
            job_list_container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, job_list_xpath))
            )

            logger.info("🔄 Scrolling inside the job list container...")

            # ✅ Scroll multiple times to ensure jobs load efficiently
            for _ in range(5):  # Reduced iterations
                jobs = self.driver.find_elements(By.XPATH, "//div[@data-job-id]")
                new_jobs = [job for job in jobs if job.get_attribute("data-job-id") not in seen_jobs]

                for job in new_jobs:
                    job_id = job.get_attribute("data-job-id")
                    seen_jobs.add(job_id)
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", job)
                    time.sleep(0.1)  # Reduced sleep

                self.driver.execute_script("arguments[0].scrollTop += 500;", job_list_container)
                time.sleep(0.1)  # Faster scrolling

            jobs = WebDriverWait(self.driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@data-job-id]"))
            )

            logger.info(f"✅ Found {len(jobs)} jobs on Page {page + 1}.")

            for index, job in enumerate(jobs, start=1):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
                    job.click()

                    # ✅ Wait for the job title to appear instead of using sleep
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title"))
                    )

                    # ✅ Extract Job Title
                    job_title = self.driver.execute_script("""
                        let titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                        return titleElement ? titleElement.innerText.trim() : "Unknown Title";
                    """)

                    # ✅ Extract Company Name Using Index (Original Code)
                    company_name = self.driver.execute_script(f"""
                        let jobCards = document.querySelectorAll('.job-card-container--clickable');
                        if (jobCards.length >= {index}) {{
                            let selectedJob = jobCards[{index - 1}];  
                            let companyElement = selectedJob.querySelector('.topcard__flavor, .artdeco-entity-lockup__subtitle');
                            return companyElement ? companyElement.innerText.trim() : "Unknown Company";
                        }} else {{
                            return "Unknown Company";
                        }}
                    """)

                    # ✅ Extract Job Location Using Index (Original Code)
                    job_location = self.driver.execute_script(f"""
                        let jobCards = document.querySelectorAll('.job-card-container--clickable');
                        if (jobCards.length >= {index}) {{
                            let selectedJob = jobCards[{index - 1}];
                            let locationElement = selectedJob.querySelector('.job-card-container__metadata-wrapper li span[dir="ltr"]');
                            return locationElement ? locationElement.innerText.trim() : "Unknown Location";
                        }} else {{
                            return "Unknown Location";
                        }}
                    """)

                    # ✅ Extract job URL using `data-job-id`
                    job_id = job.get_attribute("data-job-id")
                    job_full_url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else "Unknown URL"

                    # ✅ Extract number of connections
                    connections_text = self.driver.execute_script("""
                        let connectionsElement = document.querySelector(
                            ".job-card-container__job-insight-text, .job-details-jobs-unified-top-card__connections"
                        );
                        return connectionsElement ? connectionsElement.innerText.trim() : "0 connections";
                    """)

                    connections = int(re.search(r"(\d+)", connections_text).group(1)) if "connection" in connections_text.lower() else 0

                    # ✅ Extract Job Description
                    job_description = self.driver.execute_script("""
                        let descriptionElement = document.querySelector("#job-details");
                        return descriptionElement ? descriptionElement.innerText.trim() : "Not Found";
                    """)

                    job_list.append({
                        "job_title": job_title,
                        "company_name": company_name,
                        "job_location": job_location,
                        "job_url": job_full_url,
                        "connections": connections,
                        "job_description": job_description
                    })

                except Exception as e:
                    logger.error(f"❌ Error extracting job {index}: {e}")

            # ✅ Move to the next page
            next_page_button = self.driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button.jobs-search-pagination__button--next")
            
            if next_page_button and page < num_pages - 1:
                logger.info(f"➡️ Moving to Next Page ({page + 2})...")
                self.driver.execute_script("arguments[0].click();", next_page_button[0])
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-job-id]"))
                )  # ✅ Wait for the next page to load properly

        logger.info("✅ Job descriptions extraction completed.")
        return job_list



    def extract_match_score(response_text):
        """
        Extracts the Match Score from the given AI-generated response.

        Args:
            response_text (str): The AI-generated response containing a Match Score.

        Returns:
            int or None: The extracted Match Score if found, otherwise None.
        """
        logger.info("🔍 Parsing AI Response for Match Score...")

        # ✅ Approach 1: Line-by-Line Processing (More Flexible)
        lines = response_text.split("\n")
        for line in lines:
            if "Match Score" in line:
                words = line.split()
                for word in words:
                    if word.strip("%").isdigit():  # Ignore % symbol and extract number
                        match_score = int(word.strip("%"))
                       # logger.info(f"🎯 Extracted Match Score: {match_score}%")
                        return match_score

        # ✅ Approach 2: Regex Matching (Backup)
        regex_patterns = [
            r"-\s*\*\*Match Score:\s*(\d+)%\*\*",  # **Match Score:** XX%
            r"Match Score:\s*(\d+)%",  # Match Score: XX%
            r"-\s*Match Score:\s*(\d+)%",  # - Match Score: XX%
            r"\*\*Match Score:\s*(\d+)%\*\*",  # **Match Score: XX%**
            r"\bMatch Score\s*[:\-]?\s*(\d+)%\b",  # Match Score - XX%
        ]
        
        for pattern in regex_patterns:
            match = re.search(pattern, response_text)
            if match:
                match_score = int(match.group(1))
                #logger.info(f"🎯 Extracted Match Score using Regex: {match_score}%")
                return match_score

        # ❌ If nothing was found, log error
        logger.error("❌ Match Score not found in response.")
        return None
    
    def evaluate_job_matches(self, job_descriptions):
        """Evaluates job matches using ChatGPT for a list of job descriptions and saves scores to each description.

        Args:
            job_descriptions (list): List of job descriptions to evaluate.

        Returns:
            list: List of dictionaries containing job descriptions and extracted match scores.
        """
        if not self.resume_text:
            logger.error("❌ Resume text is missing. Please provide a valid resume before evaluating jobs.")
            return []

        job_match_results = []
        
        for index, job_description in enumerate(job_descriptions, start=1):
            if not job_description:
                logger.warning(f"⚠️ Skipping job {index}: No description available.")
                job_match_results.append({"index": index, "description": None, "score": None})
                continue

            #logger.info(f"🔍 Evaluating job {index}/{len(job_descriptions)}...")

            # ✅ Prepare prompt
            prompt = f"""
            You are an AI recruiter evaluating a resume against a job description.
            Compare the resume with the job description and provide insights on compatibility.

            ### Evaluation Criteria:
            - Provide a match score (0-100%) based on relevant skills, experience, and qualifications.
            - Identify missing skills or requirements.
            - Highlight key strengths from the resume that align with the job description.
            - Offer recommendations for improvement.

            ### Special Considerations:
            - If the job description mentions "Junior," **increase the match score** and consider it highly relevant for me.
            - If the job description does not specify required years of experience, **increase the match score** and consider it relevant for me.
            - Prioritize opportunities that align with my skills and background.

            ### Resume:
            {self.resume_text}

            ### Job Description:
            {job_description}

            ### Output Format:
            - **Match Score:** XX% (Boosted if criteria met)
            - **Missing Skills:** (List)
            - **Strengths:** (List)
            - **Recommendations:** (How to improve)
            - **Interest Level:** High/Moderate/Low (Based on the conditions)
"""


            # ✅ Send prompt to ChatGPT using GPT-4o-mini
            response = self.chat_gpt.ask(prompt, model="gpt-4o-mini")

            # ✅ Check response validity
            response_text = None

            if isinstance(response, dict) and "response" in response:
                response_text = response["response"].strip()
            elif isinstance(response, str):
                response_text = response.strip()
            else:
                logger.error(f"❌ Invalid response format from ChatGPT: {response}")
                job_match_results.append({"index": index, "description": job_description, "score": None})
                continue

           # logger.info(f"✅ ChatGPT Response:\n{response_text}")

            # ✅ Use extract_match_score function for match score extraction
            match_score = JobScraper.extract_match_score(response_text)  # ✅ Use static method

            # ✅ Store the match result
            job_match_results.append({
                "index": index,
                **job_description,  
                "chat_gpt_response": response_text,
                "score": match_score
            })
            
            logger.info(f"✅ evaluated job {index}")


           

        logger.info("✅ Job matching completed!")
        return job_match_results

