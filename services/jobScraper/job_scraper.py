import time
import logging
import re
import os
import concurrent.futures
import threading

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from services.chatGpt import chat_gpt
from services.chatService import chat_service

from services.pdfReader.pdf_reader import PDFReader


logger = logging.getLogger(__name__)

class JobScraper:
    """Extracts job details from LinkedIn."""
    def __init__(self, driver): 
            self.driver = driver
            self.resume_path = os.getenv("RESUME_PATH", "/Resume.pdf")

            # Check if CHAT_SERVICE is set and not empty
            chat_service_env = os.getenv("AI_CHAT_SERVICE_URL", "").strip()

            if chat_service_env:
                self.chat_gpt =  chat_service.ChatService()

            else:
                self.chat_gpt = chat_gpt.ChatGPT()

            self.pdf_reader = PDFReader(self.resume_path)
            self.resume_text = self.pdf_reader.get_text()

    def read_prompt_template(file_path, resume_text, job_description):
        """Reads the prompt template from a file and formats it with resume and job description."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                template = file.read()
                return template.format(resume_text=resume_text, job_description=job_description)
        except FileNotFoundError:
            logger.error(f"❌ Prompt file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"❌ Error reading prompt file: {e}")
            return None
    
    def extract_job_descriptions(self, num_pages=1):
        """Extracts job descriptions dynamically from LinkedIn in parallel using ThreadPoolExecutor."""
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
            for _ in range(5):
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
            logger.info(f"🔍 [DEBUG] Active Threads Before Extraction: {threading.active_count()}")

            # ✅ Extract job descriptions in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
                results = executor.map(self.extract_single_job, jobs, range(1, len(jobs) + 1))

            # ✅ Collect results from threads
            for job_data in results:
                if job_data:
                    job_list.append(job_data)

            logger.info(f"🔍 [DEBUG] Active Threads After Extraction: {threading.active_count()}")

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



        # ✅ Define a function to evaluate a single job description
   
    def evaluate_single_job(self, index, job_description):
        """Evaluates a single job description using ChatGPT and returns results."""
        
        if not job_description:
            logger.warning(f"⚠️ Job {index}: No description available. Skipping.")
            return {"index": index, "description": None, "score": None}

        # ✅ Load prompt template from file and format with resume & job description
        prompt_template_path = "prompt_template.txt"  # Change this if needed
        prompt = self.read_prompt_template(prompt_template_path, self.resume_text, job_description)

        if not prompt:
            logger.error(f"❌ Job {index}: Failed to load prompt template. Skipping job.")
            return {"index": index, "description": job_description, "score": None}

        # ✅ Send request to ChatGPT **without retries**
        try:
            logger.info(f"🔄 Job {index}: Sending request to AI-Chat-Service.")
            response = self.chat_gpt.ask(prompt)

            if not response or "response" not in response:
                logger.error(f"❌ Job {index}: Received empty or invalid response from AI-Chat-Service.")
                return {"index": index, "description": job_description, "score": None}

            # ✅ Extract match score
            response_text = response["response"].strip()
            match_score = JobScraper.extract_match_score(response_text)

            logger.info(f"✅ Job {index}: Processed successfully. Match Score: {match_score}%")
            return {
                "index": index,
                **job_description,
                "chat_gpt_response": response_text,
                "score": match_score
            }

        except Exception as e:
            logger.error(f"❌ Job {index}: Error while processing ChatGPT request - {e}")
            return {"index": index, "description": job_description, "score": None}


    def extract_single_job(self, job, index):
        """Extracts a single job description dynamically using Selenium."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
            job.click()

            # ✅ Wait for job title to appear (Max 5 seconds)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title"))
            )

            # ✅ Extract Job Title
            job_title = self.driver.execute_script("""
                let titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                return titleElement ? titleElement.innerText.trim() : "Unknown Title";
            """)
            if not job_title:
                logger.warning(f"⚠️ Job {index}: Title missing, setting as 'Unknown Title'")
                job_title = "Unknown Title"

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
            if not company_name:
                logger.warning(f"⚠️ Job {index}: Company name missing, setting as 'Unknown Company'")
                company_name = "Unknown Company"

            # ✅ Extract Job Location
            job_location = self.driver.execute_script("""
                let locationElement = document.querySelector('.job-card-container__metadata-wrapper li span[dir="ltr"]');
                return locationElement ? locationElement.innerText.trim() : null;
            """)
            if not job_location:
                logger.warning(f"⚠️ Job {index}: Location missing, setting as 'Unknown Location'")
                job_location = "Unknown Location"

            # ✅ Extract Job URL
            job_id = job.get_attribute("data-job-id")
            job_full_url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else "Unknown URL"

            # ✅ Extract Number of Connections
            connections_text = self.driver.execute_script("""
                let connectionsElement = document.querySelector(
                    ".job-card-container__job-insight-text, .job-details-jobs-unified-top-card__connections"
                );
                return connectionsElement ? connectionsElement.innerText.trim() : "0 connections";
            """)
            connections = 0  # Default if parsing fails
            try:
                match = re.search(r"(\d+)", connections_text)
                if match:
                    connections = int(match.group(1))
            except Exception:
                logger.warning(f"⚠️ Job {index}: Could not extract number of connections")

            # ✅ Extract Job Description
            job_description = self.driver.execute_script("""
                let descriptionElement = document.querySelector("#job-details");
                return descriptionElement ? descriptionElement.innerText.trim() : null;
            """)
            if not job_description:
                logger.warning(f"⚠️ Job {index}: Job description missing, setting as 'Not Found'")
                job_description = "Not Found"

            # ✅ Ensure everything is a string
            return {
                "job_title": str(job_title),
                "company_name": str(company_name),
                "job_location": str(job_location),
                "job_url": str(job_full_url),
                "connections": connections,  # Keep this as an integer for sorting
                "job_description": str(job_description)
            }

        except Exception as e:
            logger.error(f"❌ Error extracting job {index}: {e}")
            return None

        finally:
            logger.info(f"✅ Job {index}: Extraction complete.")
    
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
            """Evaluates multiple job descriptions in parallel using ThreadPoolExecutor."""
            if not self.resume_text:
                logger.error("❌ Resume text is missing. Please provide a valid resume before evaluating jobs.")
                return []

            job_match_results = []
            max_threads = min(5, len(job_descriptions))  # Prevent overloading

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = {executor.submit(self.evaluate_single_job, index, job_desc): index for index, job_desc in enumerate(job_descriptions, start=1)}
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        job_match_results.append(future.result())
                    except Exception as e:
                        logger.error(f"❌ Error processing job: {e}")

            logger.info("✅ All jobs evaluated in parallel.")
            return job_match_results

    @staticmethod
    def extract_match_score(response_text):
        """Extracts the match score from the AI-generated response."""
        logger.info("🔍 Parsing AI Response for Match Score...")

        patterns = [
            r"-\s*\*\*Match Score:\s*(\d+)%\*\*",  # **Match Score:** XX%
            r"Match Score:\s*(\d+)%",  # Match Score: XX%
            r"-\s*Match Score:\s*(\d+)%",  # - Match Score: XX%
            r"\*\*Match Score:\s*(\d+)%\*\*",  # **Match Score: XX%**
            r"\bMatch Score\s*[:\-]?\s*(\d+)%\b",  # Match Score - XX%
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text)
            if match:
                return int(match.group(1))

        logger.error("❌ Match Score not found in response.")
        return None