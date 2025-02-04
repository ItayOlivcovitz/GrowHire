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
        try:
            job_list = []
            seen_jobs = set()

            for page in range(num_pages):  # ✅ Iterate over the number of pages
                time.sleep(3)
                logger.info(f"📄 Scraping Page {page + 1}/{num_pages}...")

                # ✅ Locate the job list container
                job_list_xpath = "//*[@id='main']/div/div[2]/div[1]/div"
                job_list_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, job_list_xpath))
                )

                if not job_list_container:
                    logger.error("❌ Job list container not found.")
                    return []

                logger.info("🔄 Scrolling inside the job list container...")

                # ✅ Scroll multiple times to ensure jobs load
                for _ in range(10):
                    jobs = self.driver.find_elements(By.XPATH, "//div[@data-job-id]")
                    for job in jobs:
                        job_id = job.get_attribute("data-job-id")
                        if job_id and job_id not in seen_jobs:
                            seen_jobs.add(job_id)
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", job)
                            time.sleep(0.5)

                    self.driver.execute_script("arguments[0].scrollTop += 500;", job_list_container)
                    time.sleep(0.5)

                # ✅ Collect job descriptions
                jobs = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-job-id]"))
                )

                logger.info(f"✅ Found {len(jobs)} jobs on Page {page + 1}.")

                for index, job in enumerate(jobs, start=1):
                    try:
                        # ✅ Click the job to ensure details are loaded
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
                        job.click()
                        time.sleep(1)  # ✅ Wait for job details to load

                        # ✅ Extract Job Title
                        job_title = self.driver.execute_script("""
                            let titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                            return titleElement ? titleElement.innerText.trim() : "Unknown Title";
                        """)

                        # ✅ Extract Company Name Using Index
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

                        # ✅ Extract Job Location Using Index
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

                        # ✅ Extract job URL
                        job_full_url = self.driver.current_url

                        # ✅ Extract number of connections
                        connections_text = self.driver.execute_script("""
                            let connectionsElement = document.querySelector(
                                ".job-card-container__job-insight-text, .job-details-jobs-unified-top-card__connections"
                            );
                            return connectionsElement ? connectionsElement.innerText.trim() : "0 connections";
                        """)

                        connections = 0
                        if "connection" in connections_text.lower():
                            match = re.search(r"(\d+)", connections_text)
                            connections = int(match.group(1)) if match else 0

                        # ✅ Extract Job Description
                        job_description = self.driver.execute_script("""
                            let descriptionElement = document.querySelector("#job-details");
                            return descriptionElement ? descriptionElement.innerText.trim() : "Not Found";
                        """)

                        # ✅ Store extracted job details
                        job_data = {
                            "job_title": job_title,
                            "company_name": company_name,
                            "job_location": job_location,
                            "job_url": job_full_url,
                            "connections": connections,
                            "job_description": job_description
                        }

                        job_list.append(job_data)

                    except Exception as e:
                        logger.error(f"❌ Error extracting job {index}: {e}")

                # ✅ Find and click the Next Page button
                try:

                    logger.info(f"📄 Checking for Next Page Button (Page {page + 1}/{num_pages})...")

                    # ✅ Use CSS Selector to Find "Next" Button
                    try:
                        next_page_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-button.jobs-search-pagination__button--next"))
                        )
                    except TimeoutException:
                        next_page_button = None

                    if next_page_button and page < num_pages - 1:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_button)
                        time.sleep(1)  # ✅ Ensure button is interactable

                        if next_page_button.is_displayed() and next_page_button.is_enabled():
                            logger.info(f"➡️ Moving to Next Page ({page + 2})...")
                            self.driver.execute_script("arguments[0].click();", next_page_button)

                            # ✅ Wait for new page to load
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@data-job-id]"))
                            )
                            time.sleep(3)

                        else:
                            logger.warning("⚠️ Next Page button found but not clickable.")
                            break

                    else:
                        logger.info("✅ No more pages available or reached the selected limit.")
                        break  # ✅ Exit loop if no more pages

                except TimeoutException:
                    logger.error("❌ Timeout: Next Page button not found.")
                    break

                except StaleElementReferenceException:
                    logger.warning("⚠️ Stale Element Exception: Retrying next page button search...")
                    time.sleep(2)
                    continue  # ✅ Retry loop in case of stale reference

                except NoSuchElementException:
                    logger.error("❌ NoSuchElementException: Next Page button not found.")
                    break

                except Exception as e:
                    logger.error(f"❌ Error clicking Next Page: {e}")
                    break  # ✅ Exit loop if error occurs

            logger.info("✅ Job descriptions extraction completed.")
            return job_list

        except Exception as e:
            logger.error(f"❌ Error scrolling job list: {e}")
            return []

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

