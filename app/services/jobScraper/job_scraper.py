import concurrent.futures
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from app.services.chatGpt import chat_gpt
from app.services.chatService import chat_service
from app.services.gemini import gemini_service
from app.services.pdfReader.pdf_reader import PDFReader

logger = logging.getLogger(__name__)


class JobScraper:
    """Extracts job details from LinkedIn."""

    # Configuration constants (avoids magic numbers)
    PAGE_LOAD_DELAY = 2
    SCROLL_DELAY = 0.3
    JOB_CLICK_DELAY = 1
    JOB_DETAILS_TIMEOUT = 5
    JOB_LIST_TIMEOUT = 5
    JOB_ELEMENTS_TIMEOUT = 3
    SCROLL_ITERATIONS = 5
    API_MAX_RETRIES = 3
    API_RETRY_DELAY = 2

    def __init__(self, driver: Any, ai_provider: Optional[str] = None) -> None:
        self.driver = driver
        self.resume_path = os.getenv("RESUME_PATH", "/resume.pdf")

        # Initialize AI service based on provider parameter or env vars
        if ai_provider:
            ai_provider_lower = ai_provider.lower()
            if ai_provider_lower == "openai":
                self.ai_service = chat_gpt.ChatGPT()
            elif ai_provider_lower == "gemini":
                self.ai_service = gemini_service.GeminiService()
            elif ai_provider_lower == "chatservice":
                self.ai_service = chat_service.ChatService()
            else:
                logger.warning(f"Unknown AI provider '{ai_provider}', falling back to env-based logic.")
                self._init_ai_from_env()
        else:
            self._init_ai_from_env()

        self.pdf_reader = PDFReader(self.resume_path)
        self.resume_text = self.pdf_reader.get_text()

    def _init_ai_from_env(self) -> None:
        """Initialize AI service based on environment variables (backward compatibility)."""
        chat_service_env = os.getenv("AI_CHAT_SERVICE_URL", "").strip()
        if chat_service_env:
            self.ai_service = chat_service.ChatService()
        else:
            self.ai_service = chat_gpt.ChatGPT()

    def read_prompt_template(
        self, file_path: str, resume_text: str, job_description: Any
    ) -> Optional[str]:
        """Reads the prompt template from a file and formats it with resume and job description."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                template = file.read()
                return template.format(resume_text=resume_text, job_description=job_description)
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {file_path}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error formatting prompt template: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            return None

    def extract_job_descriptions(self, num_pages: int = 1) -> List[Dict[str, Any]]:
        """Extracts job descriptions dynamically from LinkedIn by visiting every job component."""
        job_list: List[Dict[str, Any]] = []
        total_jobs_added = 0
        seen_jobs: set = set()  # Single set across all pages to avoid duplicate extractions

        for page in range(num_pages):
            time.sleep(self.PAGE_LOAD_DELAY)
            logger.debug(f"Processing page {page + 1} of {num_pages}")
            logger.info(f"Scraping Page {page + 1}/{num_pages}...")

            job_list_xpath = "//*[@id='main']/div/div[2]/div[1]/div"
            try:
                job_list_container = WebDriverWait(
                    self.driver, self.JOB_LIST_TIMEOUT
                ).until(EC.presence_of_element_located((By.XPATH, job_list_xpath)))
            except TimeoutException:
                logger.error(
                    f"Timeout: Could not locate job list container after {self.JOB_LIST_TIMEOUT}s"
                )
                return job_list
            except Exception as e:
                logger.error(f"Error locating job list container: {e}")
                return job_list

            logger.info("Scrolling inside the job list container to load more jobs...")
            for _ in range(self.SCROLL_ITERATIONS):
                self.driver.execute_script("arguments[0].scrollTop += 500;", job_list_container)
                time.sleep(self.SCROLL_DELAY)

            try:
                jobs = WebDriverWait(self.driver, self.JOB_ELEMENTS_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-job-id]"))
                )
            except TimeoutException:
                logger.error(f"Timeout: Could not locate job elements on page {page + 1}")
                return job_list
            except Exception as e:
                logger.error(f"Error locating job elements on page {page + 1}: {e}")
                return job_list

            logger.info(f"Found {len(jobs)} total jobs on Page {page + 1}.")

            for index, job in enumerate(jobs):
                job_data = self.extract_single_job(job, index, seen_jobs)
                if job_data:
                    job_list.append(job_data)
                    total_jobs_added += 1
                    logger.info(
                        f"Extracted job from Page {page + 1} - Job {index}: "
                        f"{job_data['job_title']} at {job_data['company_name']}"
                    )

            logger.info(f"Extracted {total_jobs_added} jobs so far.")

            next_page_button = self.driver.find_elements(
                By.CSS_SELECTOR, "button.artdeco-button.jobs-search-pagination__button--next"
            )
            if next_page_button and page < num_pages - 1:
                logger.info(f"Moving to Next Page ({page + 2})...")
                self.driver.execute_script("arguments[0].click();", next_page_button[0])
                try:
                    WebDriverWait(self.driver, self.JOB_LIST_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@data-job-id]"))
                    )
                except TimeoutException:
                    logger.error("Timeout while navigating to the next page.")
                    break
                except Exception as e:
                    logger.error(f"Error while navigating to the next page: {e}")
                    break

        logger.info(f"Job descriptions extraction completed. Total jobs added: {total_jobs_added}")
        if not job_list:
            logger.warning(
                "No job descriptions were extracted. Check LinkedIn loading or scrolling."
            )
        return job_list


        

    def extract_single_job(
        self, job: Any, index: int, seen_jobs: set
    ) -> Optional[Dict[str, Any]]:
        """Extracts a single job description dynamically using Selenium."""
        try:
            job_id = job.get_attribute("data-job-id")
            if not job_id:
                logger.warning(f"Job {index}: Missing job ID, skipping.")
                return None

            if job_id in seen_jobs:
                logger.debug(f"Job {index}: Skipping duplicate job (ID: {job_id})")
                return None
            seen_jobs.add(job_id)

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", job
            )
            job.click()
            time.sleep(self.JOB_CLICK_DELAY)

            try:
                WebDriverWait(self.driver, self.JOB_DETAILS_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".jobs-details__main-content")
                    )
                )
            except TimeoutException:
                logger.warning(f"Job {index}: Job details panel did not load in time.")
                return None

            job_title = self.driver.execute_script("""
                let titleElement = document.querySelector('.job-details-jobs-unified-top-card__job-title');
                return titleElement ? titleElement.innerText.trim() : "Unknown Title";
            """) or "Unknown Title"

            # Extract company name by matching job_id (more reliable than index)
            company_name = self.driver.execute_script("""
                var jobId = arguments[0];
                var jobCards = document.querySelectorAll('.job-card-container--clickable');
                for (var i = 0; i < jobCards.length; i++) {
                    if (jobCards[i].getAttribute('data-job-id') === jobId) {
                        var companyElement = jobCards[i].querySelector('.topcard__flavor, .artdeco-entity-lockup__subtitle');
                        if (companyElement) return companyElement.innerText.trim();
                    }
                }
                var detailCompany = document.querySelector('.job-details-jobs-unified-top-card__company-name');
                return detailCompany ? detailCompany.innerText.trim() : "Unknown Company";
            """, job_id) or "Unknown Company"

            job_location = self.driver.execute_script("""
                let locationElement = document.querySelector('.job-card-container__metadata-wrapper li span[dir="ltr"]');
                return locationElement ? locationElement.innerText.trim() : "Unknown Location";
            """) or "Unknown Location"

            job_full_url = (
                f"https://www.linkedin.com/jobs/view/{job_id}/"
                if job_id
                else "Unknown URL"
            )

            connections_text = self.driver.execute_script("""
                let connectionsElement = document.querySelector(
                    ".job-card-container__job-insight-text, .job-details-jobs-unified-top-card__connections"
                );
                return connectionsElement ? connectionsElement.innerText.trim() : "0 connections";
            """) or "0 connections"

            connections = 0
            conn_match = re.search(r"(\d+)", connections_text)
            if conn_match:
                try:
                    connections = int(conn_match.group(1))
                except ValueError:
                    pass

            # Wait for job description to load (content length > 100 chars)
            job_description = "Not Found"
            try:
                WebDriverWait(self.driver, self.JOB_DETAILS_TIMEOUT).until(
                    lambda d: d.execute_script("""
                        var el = document.querySelector("#job-details");
                        return el && el.innerText && el.innerText.trim().length > 100;
                    """)
                )
                job_description = self.driver.execute_script("""
                    let descElement = document.querySelector("#job-details");
                    return descElement ? descElement.innerText.trim() : "Not Found";
                """) or "Not Found"
            except TimeoutException:
                logger.warning(f"Job {index}: Job description did not load in time, retrying...")
                time.sleep(self.PAGE_LOAD_DELAY)
                job_description = self.driver.execute_script("""
                    let descElement = document.querySelector("#job-details");
                    return descElement ? descElement.innerText.trim() : "Not Found";
                """) or "Not Found"

            return {
                "job_title": str(job_title),
                "company_name": str(company_name),
                "job_location": str(job_location),
                "job_url": str(job_full_url),
                "connections": connections,
                "job_description": str(job_description),
            }

        except TimeoutException as e:
            logger.warning(f"Job {index}: Timeout during extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting job {index}: {e}")
            return None
        finally:
            logger.debug(f"Job {index}: Extraction complete.")


    def evaluate_single_job(
        self, index: int, job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluates a single job description using the configured AI service (with retries)."""
        if not job_description:
            logger.warning(f"Job {index}: No description available. Skipping.")
            return {"index": index, "description": None, "score": None}

        prompt_template_path = "app/utils/prompt_template.txt"
        desc_text = (
            job_description.get("job_description")
            if isinstance(job_description, dict)
            else job_description
        )
        prompt = self.read_prompt_template(
            prompt_template_path, self.resume_text, desc_text
        )
        if not prompt:
            logger.error(f"Job {index}: Failed to load prompt template. Skipping job.")
            return {"index": index, "description": job_description, "score": None}

        for attempt in range(1, self.API_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Job {index}: Sending request to AI service (attempt {attempt}/{self.API_MAX_RETRIES})."
                )
                response = self.ai_service.ask(prompt)

                if not response or "response" not in response:
                    error_msg = response.get("error", "Empty or invalid response") if response else "No response"
                    logger.warning(f"Job {index}: {error_msg}")
                    if attempt < self.API_MAX_RETRIES:
                        time.sleep(self.API_RETRY_DELAY)
                        continue
                    return {"index": index, "description": job_description, "score": None}

                response_text = response["response"].strip()
                match_score = JobScraper.extract_match_score(response_text)
                logger.info(f"Job {index}: Processed successfully. Match Score: {match_score}%")
                result = {"index": index, **job_description, "chat_gpt_response": response_text, "score": match_score}
                return result

            except Exception as e:
                logger.warning(f"Job {index}: API error (attempt {attempt}/{self.API_MAX_RETRIES}): {e}")
                if attempt < self.API_MAX_RETRIES:
                    time.sleep(self.API_RETRY_DELAY)
                else:
                    logger.error(f"Job {index}: Failed after {self.API_MAX_RETRIES} attempts.")
                    return {"index": index, "description": job_description, "score": None}

        return {"index": index, "description": job_description, "score": None}

    @staticmethod
    def extract_match_score(response_text: str) -> Optional[int]:
        """
        Extracts the Match Score from the given AI-generated response.

        Args:
            response_text: The AI-generated response containing a Match Score.

        Returns:
            The extracted Match Score if found, otherwise None.
        """
        logger.debug("Parsing AI response for Match Score.")

        lines = response_text.split("\n")
        for line in lines:
            if "Match Score" in line:
                for word in line.split():
                    cleaned = word.strip("%")
                    if cleaned.isdigit():
                        return int(cleaned)

        regex_patterns = [
            r"-\s*\*\*Match Score:\s*(\d+)%\*\*",
            r"Match Score:\s*(\d+)%",
            r"-\s*Match Score:\s*(\d+)%",
            r"\*\*Match Score:\s*(\d+)%\*\*",
            r"\bMatch Score\s*[:\-]?\s*(\d+)%\b",
        ]
        for pattern in regex_patterns:
            match = re.search(pattern, response_text)
            if match:
                return int(match.group(1))

        logger.warning("Match Score not found in response.")
        return None

    def evaluate_job_matches(
        self, job_descriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluates multiple job descriptions in parallel using ThreadPoolExecutor."""
        if not self.resume_text:
            logger.error("Resume text is missing. Provide a valid resume before evaluating jobs.")
            return []

        max_workers = min(5, max(1, len(job_descriptions)))
        job_match_results: List[Dict[str, Any]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.evaluate_single_job, index, job_desc): index
                for index, job_desc in enumerate(job_descriptions, start=1)
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        job_match_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing job: {e}")

        logger.info(f"All jobs evaluated. Total: {len(job_match_results)}")
        return job_match_results