import os
import time
import logging


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait  # ✅ Import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # ✅ Import EC
import urllib.parse




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Suppress WebDriver Manager logs
logging.getLogger("WDM").setLevel(logging.WARNING)
logging.getLogger("webdriver_manager").setLevel(logging.WARNING)

class LinkedInNavigator:
    """Handles LinkedIn login and navigation."""

    def __init__(self):
        """Automatically starts the WebDriver when an instance is created."""
        self.driver = self.start_driver()  # ✅ Calls the method correctly
        if not self.driver:
            logger.error("🚫 Unable to start WebDriver. Exiting.")
            exit(1)

    def start_driver(self):
        """Starts Chrome WebDriver and returns the driver instance."""
        try:
            logger.info("🚀 Starting Chrome WebDriver...")
            options = webdriver.ChromeOptions()

            # Suppress DevTools logs and other unwanted messages
            options.add_argument("--log-level=3")  # Suppress most Chrome logs (INFO=1, WARNING=2, ERROR=3)
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # Suppress automation logs
            options.add_experimental_option("useAutomationExtension", False)

            # Avoid bot detection
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--incognito")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

            # Detect if running in Docker
            is_docker = os.path.exists("/.dockerenv")

            if is_docker:
                logger.info("🛠️ Running inside Docker. Applying Docker-specific Chrome settings...")
                print("🚢 Running inside Docker!")
                options.add_argument("--no-sandbox")  # Bypass OS security model
                options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in low-memory environments
                options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
                options.add_argument("--start-maximized")  # Ensure the window is visible
                options.add_argument("--window-size=1920,1080")  # Set a fixed window size
                options.add_argument("--display=:99")  # ✅ Run Chrome inside Xvfb virtual display
                
                # 🛠️ Fix "session not created" issue by using a unique user data directory
                unique_data_dir = f"/tmp/chrome-user-data-{os.getpid()}"
                options.add_argument(f"--user-data-dir={unique_data_dir}")

                # Ensure /tmp directory has proper permissions
                os.makedirs(unique_data_dir, exist_ok=True)
                os.chmod(unique_data_dir, 0o777)  # Ensure it is writable

            else:
                print("🖥️ Running locally!")

            # ✅ Use WebDriver Manager to automatically download the correct driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            logger.info("✅ Chrome WebDriver initialized successfully.")
            return driver

        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome WebDriver: {e}", exc_info=True)
            return None



    def search_people(self, search_query, num_pages=1):
        """
        Opens LinkedIn search for people using the provided search query and number of pages.
        This function constructs the search URL and navigates to it.
        """
        logger.info(f"🔍 Searching for people with query: '{search_query}' on {num_pages} page(s)")
        # Construct the base URL for people search on LinkedIn
        base_url = "https://www.linkedin.com/search/results/people/"
        # Encode the search query
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"{base_url}?keywords={encoded_query}"
        # Optionally, append additional filters if required (e.g., location, industry)
        
        self.driver.get(search_url)
        time.sleep(3)
        logger.info("✅ People search page loaded.")
        
        # Pagination logic can be added here if needed.

    def stop_driver(self):
        """Stops the Chrome WebDriver."""
        if self.driver:
            logger.info("🛑 Stopping WebDriver...")
            self.driver.quit()
            self.driver = None

    def search_jobs(self, job_title, location, filters):
            """Search for jobs on LinkedIn with selected filters."""
            logger.info(f"🔍 Searching for jobs: {job_title} in {location}")
            
            # Construct search URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={urllib.parse.quote(job_title)}&location={urllib.parse.quote(location)}"
            
            date_posted_map = {
                "Past 24 hours": "r86400",
                "Past Week": "r604800",
                "Past Month": "r2592000"
            }
            if filters.get("date_posted") in date_posted_map:
                search_url += f"&f_TPR={date_posted_map[filters['date_posted']]}"
            
            experience_map = {
                "Internship": "1",
                "Entry level": "2",
                "Associate": "3",
                "Mid-Senior level": "4",
                "Director": "5",
                "Executive": "6"
            }
            if filters.get("experience_level") in experience_map:
                search_url += f"&f_E={experience_map[filters['experience_level']]}"
            
            if filters.get("company"):
                search_url += f"&f_C={urllib.parse.quote(filters['company'])}"
            
            remote_map = {
                "Hybrid": "1",
                "On-site": "2",
                "Remote": "3"
            }
            for option in filters.get("remote_options", []):
                if option in remote_map:
                    search_url += f"&f_WT={remote_map[option]}"
            
            if filters.get("easy_apply"):
                search_url += "&f_AL=true"
            
            # Navigate to the search page
            self.driver.get(search_url)
            time.sleep(3)
            logger.info("✅ Job search page loaded.")

    def open_feed(self):
        """Open the LinkedIn feed page."""
        logger.info("Opening LinkedIn feed.")
        feed_url = "https://www.linkedin.com/feed/"
        self.driver.get(feed_url)
        time.sleep(3)
        logger.info("✅ LinkedIn feed page loaded.")

            
    def open_linkedin(self):
        """Opens LinkedIn, logs in, and handles the verification step."""
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            logger.error("❌ Missing LinkedIn credentials. Exiting.")
            return False

        try:
            logger.info("🔍 Navigating to LinkedIn login page...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            # Locate and input email
            email_field = self.driver.find_element(By.ID, "username")
            email_field.clear()
            email_field.send_keys(email)

            # Locate and input password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)

            # Submit login form
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)  # Wait for LinkedIn to process login

            logger.info("✅ Login successful.")
            return True
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            self.stop_driver()  # Ensure WebDriver is properly closed on failure
            return False
        
    