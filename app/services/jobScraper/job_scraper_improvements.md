# JobScraper Improvements and Fixes

## Summary of Issues Found

### Critical Bugs (Must Fix)
1. **Duplicate detection broken** - `seen_jobs` set is recreated for each job
2. **Missing @staticmethod decorator** - `extract_match_score` should be static
3. **Company name extraction logic** - Uses incorrect index calculation

### Code Quality Issues
4. **Misleading variable name** - `self.chat_gpt` used for all AI services
5. **Magic numbers** - Hard-coded delays and timeouts throughout
6. **Inconsistent error handling** - Too broad exception catching
7. **Missing type hints** - No type annotations

### Performance Issues
8. **Inefficient job description extraction** - Unreliable wait logic
9. **No retry mechanism** - API failures are lost
10. **Sequential processing** - Could be optimized

## Recommended Fixes

### Fix 1: Duplicate Detection
```python
def extract_job_descriptions(self, num_pages=1):
    job_list = []
    total_jobs_added = 0
    seen_jobs = set()  # Create ONCE before the loop
    
    for page in range(num_pages):
        # ... existing code ...
        for index, job in enumerate(jobs):
            job_data = self.extract_single_job(job, index, seen_jobs)  # Pass the same set
            if job_data:
                job_list.append(job_data)
                total_jobs_added += 1
```

### Fix 2: Add @staticmethod Decorator
```python
@staticmethod
def extract_match_score(response_text):
    """Extracts the Match Score from the given AI-generated response."""
    # ... existing code ...
```

### Fix 3: Rename Variable
```python
# In __init__:
if ai_provider_lower == "openai":
    self.ai_service = chat_gpt.ChatGPT()
elif ai_provider_lower == "gemini":
    self.ai_service = gemini_service.GeminiService()
elif ai_provider_lower == "chatservice":
    self.ai_service = chat_service.ChatService()

# Then update all references from self.chat_gpt to self.ai_service
```

### Fix 4: Extract Constants
```python
class JobScraper:
    # Configuration constants
    SCROLL_DELAY = 0.3
    PAGE_LOAD_DELAY = 2
    JOB_CLICK_DELAY = 1
    JOB_DETAILS_TIMEOUT = 5
    JOB_LIST_TIMEOUT = 3
    MAX_RETRIES = 3
    API_RETRY_DELAY = 2
```

### Fix 5: Improve Error Handling
```python
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from requests.exceptions import RequestException

try:
    job_list_container = WebDriverWait(self.driver, self.JOB_LIST_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, job_list_xpath))
    )
except TimeoutException:
    logger.error(f"Timeout: Could not locate job list container after {self.JOB_LIST_TIMEOUT}s")
    return []
except Exception as e:
    logger.error(f"Unexpected error locating job list container: {e}", exc_info=True)
    return []
```

### Fix 6: Add Type Hints
```python
from typing import List, Dict, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver

def extract_job_descriptions(self, num_pages: int = 1) -> List[Dict[str, Any]]:
    """Extracts job descriptions dynamically from LinkedIn."""
    
def extract_single_job(self, job: Any, index: int, seen_jobs: set) -> Optional[Dict[str, Any]]:
    """Extracts a single job description dynamically using Selenium."""
```

### Fix 7: Add Retry Mechanism for API Calls
```python
def evaluate_single_job(self, index: int, job_description: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    """Evaluates a single job description with retry logic."""
    for attempt in range(max_retries):
        try:
            response = self.ai_service.ask(prompt)
            if response and "response" in response:
                # Success - process response
                return processed_result
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Job {index}: API call failed (attempt {attempt + 1}/{max_retries}), retrying...")
                time.sleep(self.API_RETRY_DELAY)
            else:
                logger.error(f"Job {index}: API call failed after {max_retries} attempts: {e}")
                return error_result
```

### Fix 8: Improve Job Description Extraction
```python
# Better approach: Wait for element to be visible and contain actual content
try:
    WebDriverWait(self.driver, self.JOB_DETAILS_TIMEOUT).until(
        lambda driver: driver.execute_script("""
            let descElement = document.querySelector("#job-details");
            return descElement && descElement.innerText.trim().length > 100;
        """)
    )
    job_description = self.driver.execute_script("""
        let descElement = document.querySelector("#job-details");
        return descElement ? descElement.innerText.trim() : "Not Found";
    """)
except TimeoutException:
    logger.warning(f"Job {index}: Job description did not load in time")
    job_description = "Not Found"
```

### Fix 9: Better Company Name Extraction
```python
# Extract company name from the clicked job card, not by index
company_name = self.driver.execute_script("""
    // Find the clicked job card by finding the one with matching job-id
    let jobId = arguments[0];
    let jobCards = document.querySelectorAll('.job-card-container--clickable');
    for (let card of jobCards) {
        if (card.getAttribute('data-job-id') === jobId) {
            let companyElement = card.querySelector('.topcard__flavor, .artdeco-entity-lockup__subtitle');
            if (companyElement) return companyElement.innerText.trim();
        }
    }
    // Fallback: try to get from details panel
    let detailCompany = document.querySelector('.job-details-jobs-unified-top-card__company-name');
    return detailCompany ? detailCompany.innerText.trim() : "Unknown Company";
""", job_id) or "Unknown Company"
```

### Fix 10: Add Progress Tracking
```python
def extract_job_descriptions(self, num_pages: int = 1, progress_callback=None) -> List[Dict[str, Any]]:
    """Extracts job descriptions with optional progress callback."""
    total_jobs = 0
    for page in range(num_pages):
        # ... extraction logic ...
        if progress_callback:
            progress_callback(page + 1, num_pages, total_jobs)
```

## Additional Recommendations

1. **Add validation** for extracted data before returning
2. **Implement rate limiting** for API calls to avoid quota issues
3. **Add caching** for prompt template reading
4. **Use context managers** for better resource management
5. **Add unit tests** for critical methods
6. **Implement logging levels** properly (debug vs info vs warning)
7. **Add docstrings** with parameter and return type documentation
8. **Consider using dataclasses** for job data structure
9. **Add timeout configuration** as class attributes
10. **Implement graceful degradation** when AI service fails
