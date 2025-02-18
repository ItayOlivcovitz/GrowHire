import os
import time
import logging
import urllib.parse
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class GetConnectedService:
    """
    Service to handle backend operations for getting connected on LinkedIn.
    Uses the provided WebDriver to:
      1. Navigate to the LinkedIn people search page.
      2. Scroll the page (with debug logging).
      3. Find and click 'Connect' buttons (handling pop-ups).
      4. Paginate through search results up to a given number of pages.
    """

    def __init__(self, driver):
        self.driver = driver
        if not self.driver:
            logger.error("🚫 WebDriver is not initialized in GetConnectedService. Exiting.")
            exit(1)

    def scroll_down(self):
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)

    def find_and_click_connect_buttons(self):
        """
        Finds and clicks all 'Connect' buttons on the current page, handling pop-ups.
        Returns the number of connect buttons clicked.
        """
        try:
            wait = WebDriverWait(self.driver, 2)  # Increased timeout for reliability
            connect_count = 0

            # Wait until connect buttons are present.
            while True:
                try:
                    connect_buttons = wait.until(
                        EC.presence_of_all_elements_located((
                            By.XPATH, 
                            "//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]"
                        ))
                    )
                    if connect_buttons:
                        logger.info(f"[INFO] Found {len(connect_buttons)} 'Connect' buttons.")
                        break
                except StaleElementReferenceException:
                    logger.warning("[WARNING] Retrying button detection due to stale elements...")

            for index, button in enumerate(connect_buttons):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    ActionChains(self.driver).move_to_element(button).perform()
                    wait.until(EC.element_to_be_clickable(button)).click()
                    time.sleep(2)  # Allow time for any popup to appear.
                    
                    try:
                        send_without_note_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((
                                By.XPATH, 
                                "//button[contains(@class, 'artdeco-button') and contains(@class, 'artdeco-button--primary')]"
                            ))
                        )
                        send_without_note_button.click()
                        logger.info("[INFO] Clicked 'Send without a note' button.")
                    except (NoSuchElementException, TimeoutException):
                        logger.info("[INFO] No 'Add a note' popup appeared, continuing.")
                    
                    connect_count += 1
                    logger.info(f"[INFO] Clicked 'Connect' button ({connect_count}).")
                except (ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException) as e:
                    logger.error(f"[ERROR] Failed to click 'Connect' button #{index + 1}: {e}")
            
            logger.info(f"[INFO] Finished! Total 'Connect' buttons clicked: {connect_count}")
            return connect_count

        except Exception as e:
            logger.error(f"[ERROR] Failed to find 'Connect' buttons: {e}")
            return 0

    def search_and_connect(self, query, num_pages):
        """
        Searches for people on LinkedIn using the provided query and attempts to connect.
        Steps:
        1. Constructs the search URL with a page parameter.
        2. Iterates through pages, scrolling down and clicking all 'Connect' buttons.
        3. Accumulates and logs the total number of Connect buttons clicked.
        4. Updates the GUI status if available.
        """
        if not self.driver:
            logger.error("❌ LinkedIn session not open.")
            return

        # Construct the URL with page parameter.
        search_query = urllib.parse.quote(query)
        base_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}&page="
        
        total_connect_buttons = 0  # Accumulate total clicks

        for page in range(1, num_pages + 1):
            try:
                logger.info(f"\n[DEBUG] Fetching page {page}/{num_pages} ...")
                self.driver.get(f"{base_url}{page}")
                time.sleep(4)  # Allow page to load
                self.scroll_down()
                
                # Optionally, call debug_search_page_buttons() for additional logging:
                # self.debug_search_page_buttons()

                connect_count = self.find_and_click_connect_buttons()
                total_connect_buttons += connect_count
            except Exception as e:
                logger.error(f"[ERROR] ❌ Failed during search pagination on page {page}: {e}")

        logger.info(f"\n✅ [INFO] Total 'Connect' buttons clicked across {num_pages} pages: {total_connect_buttons}")

        # Attempt to update GUI status if self.gui is available.
        try:
            self.gui.update_status(f"Total 'Connect' buttons found: {total_connect_buttons}")
        except AttributeError:
            logger.info(f"Total 'Connect' buttons found: {total_connect_buttons}")


    def stop_service(self):
        """Stops the underlying WebDriver."""
        logger.info("Stopping WebDriver via GetConnectedService...")
        self.driver.quit()
        self.driver = None

