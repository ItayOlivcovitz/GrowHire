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

    def read_prompt_template(self, file_path, resume_text, job_description):
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
        """Extracts job descriptions dynamically from LinkedIn by visiting every job component."""
        
        job_list = []
        total_jobs_added = 0  # ✅ Track number of successfully extracted jobs

        for page in range(num_pages):
            time.sleep(2)  # Reduce initial wait time
            logger.info(f"📄 Scraping Page {page + 1}/{num_pages}...")

            # ✅ Locate the job list container
            job_list_xpath = "//*[@id='main']/div/div[2]/div[1]/div"
            try:
                job_list_container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, job_list_xpath))
                )
            except Exception as e:
                logger.error(f"❌ Error: Could not locate job list container. {e}")
                return []

            logger.info("🔄 Scrolling inside the job list container to load more jobs...")

            # ✅ Scroll multiple times to ensure jobs load efficiently
            for _ in range(5):  
                self.driver.execute_script("arguments[0].scrollTop += 500;", job_list_container)
                time.sleep(0.3)  # Allow time for new jobs to load

            # ✅ Wait for all job elements to be fully loaded
            try:
                jobs = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-job-id]"))
                )
            except Exception as e:
                logger.error(f"❌ Error: Could not locate job elements on page {page + 1}. {e}")
                return job_list

            logger.info(f"✅ Found {len(jobs)} total jobs on Page {page + 1}.")

            # ✅ Extract job descriptions sequentially
            for index, job in enumerate(jobs):
                job_data = self.extract_single_job(job, index, set())  # ✅ FIXED: Pass a set instead of a dict
                if job_data:
                    job_list.append(job_data)
                    total_jobs_added += 1
                    logger.info(f"✅ Successfully extracted job: {job_data['job_title']} at {job_data['company_name']}")

            logger.info(f"✅ Extracted {total_jobs_added} jobs so far.")

            # ✅ Move to the next page
            next_page_button = self.driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button.jobs-search-pagination__button--next")

            if next_page_button and page < num_pages - 1:
                logger.info(f"➡️ Moving to Next Page ({page + 2})...")
                self.driver.execute_script("arguments[0].click();", next_page_button[0])

                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@data-job-id]"))
                    )  # ✅ Wait for the next page to load properly
                except Exception as e:
                    logger.error(f"❌ Error while navigating to the next page. {e}")
                    break  # Stop pagination if next page is unreachable

        logger.info(f"✅ Job descriptions extraction completed. Total jobs added: {total_jobs_added}")
        
        if not job_list:
            logger.warning("⚠️ No job descriptions were extracted. There may be an issue with LinkedIn loading or scrolling.")
        
        return job_list


        

    def extract_single_job(self, job, index, seen_jobs):
        """Extracts a single job description dynamically using Selenium."""
        
        job_description = "Not Found"  # Ensure it's initialized

        try:
            job_id = job.get_attribute("data-job-id")
            if not job_id:
                logger.warning(f"⚠️ Job {index}: Missing job ID, skipping.")
                return None  # Skip if job ID is not available

            if job_id in seen_jobs:  # 🚨 Avoid extracting the same job twice
                logger.info(f"🔄 Job {index}: Skipping duplicate job (ID: {job_id})")
                return None
            seen_jobs.add(job_id)  # Mark this job as processed

            # ✅ Scroll and click job
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
            job.click()
            time.sleep(1)  # Allow UI to update

            # ✅ Wait for job details panel to load (Max 5 seconds)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-details__main-content"))
            )

            # ✅ Extract Job Title
            job_title = self.driver.execute_script("""
                let titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                return titleElement ? titleElement.innerText.trim() : "Unknown Title";
            """) or "Unknown Title"

            # ✅ Extract Company Name
            company_name = self.driver.execute_script(f"""
                let jobCards = document.querySelectorAll('.job-card-container--clickable');
                if (jobCards.length >= {index}) {{
                    let selectedJob = jobCards[{index - 1}];  
                    let companyElement = selectedJob.querySelector('.topcard__flavor, .artdeco-entity-lockup__subtitle');
                    return companyElement ? companyElement.innerText.trim() : "Unknown Company";
                }} else {{
                    return "Unknown Company";
                }}
            """) or "Unknown Company"

            # ✅ Extract Job Location
            job_location = self.driver.execute_script("""
                let locationElement = document.querySelector('.job-card-container__metadata-wrapper li span[dir="ltr"]');
                return locationElement ? locationElement.innerText.trim() : "Unknown Location";
            """) or "Unknown Location"

            # ✅ Extract Job URL
            job_full_url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else "Unknown URL"

            # ✅ Extract Number of Connections
            connections_text = self.driver.execute_script("""
                let connectionsElement = document.querySelector(
                    ".job-card-container__job-insight-text, .job-details-jobs-unified-top-card__connections"
                );
                return connectionsElement ? connectionsElement.innerText.trim() : "0 connections";
            """) or "0 connections"

            # Convert connections to an integer
            connections = 0
            try:
                match = re.search(r"(\d+)", connections_text)
                if match:
                    connections = int(match.group(1))
            except Exception:
                logger.warning(f"⚠️ Job {index}: Could not extract number of connections")

            # ✅ Extract Job Description - Wait until it changes from the previous job
            try:
                previous_description = job_description  # Save previous description

                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("""
                        let descElement = document.querySelector("#job-details");
                        return descElement ? descElement.innerText.trim() !== arguments[0] : false;
                    """, previous_description)
                )

                job_description = self.driver.execute_script("""
                    let descriptionElement = document.querySelector("#job-details");
                    return descriptionElement ? descriptionElement.innerText.trim() : "Not Found";
                """)
            except Exception:
                logger.warning(f"⚠️ Job {index}: Failed to extract job description, retrying...")
                
                # ✅ Retry extraction after a short delay
                time.sleep(2)  # Let the page fully load
                job_description = self.driver.execute_script("""
                    let descriptionElement = document.querySelector("#job-details");
                    return descriptionElement ? descriptionElement.innerText.trim() : "Not Found";
                """)

            # ✅ Ensure everything is a string and return the result
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
            return None  # Prevent crashing the entire script

        finally:
            logger.info(f"✅ Job {index}: Extraction complete.")


    def evaluate_single_job(self, index, job_description):
            """Evaluates a single job description using ChatGPT and returns results."""
            
            if not job_description:
                logger.warning(f"⚠️ Job {index}: No description available. Skipping.")
                return {"index": index, "description": None, "score": None}

            # ✅ Load prompt template from file and format with resume & job description
            prompt_template_path = "utils\prompt_template.txt"  # Change this if needed
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

   