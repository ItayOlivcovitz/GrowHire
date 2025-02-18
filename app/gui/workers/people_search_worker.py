from PySide6.QtCore import QObject, Signal
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PeopleSearchWorker(QObject):
    """
    Worker class to handle LinkedIn people search in a separate thread.
    
    Signals:
      finished: Emitted when the search process is complete.
      results_ready: Emits a list of extracted profile information.
    """
    
    finished = Signal()
    results_ready = Signal(list)
    
    def __init__(self, connected_service, search_query, num_pages=1):
        """
        :param connected_service: Instance of GetConnectedService
        :param search_query: The search query to use.
        :param num_pages: Number of pages to process.
        """
        super().__init__()
        self.connected_service = connected_service
        self.search_query = search_query
        self.num_pages = num_pages

    def run(self):
        """Runs the people search process in the background."""
        try:
            logger.info(f"🔍 Searching for people with query: '{self.search_query}' on {self.num_pages} page(s)")
            
            # Ensure the connected service has a search_and_connect method.
            if not hasattr(self.connected_service, 'search_and_connect'):
                logger.error("Connected service does not have a 'search_and_connect' method. Please pass an instance of GetConnectedService.")
                self.results_ready.emit([])
                return

            # Perform search and connect using the connected service.
            self.connected_service.search_and_connect(self.search_query, self.num_pages)
            time.sleep(3)  # Allow time for the page to update

            # Extract profile information from the current page.
            all_profiles = []
            try:
                WebDriverWait(self.connected_service.driver, 2).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-result__info"))
                )
            except Exception as e:
                logger.error(f"Error waiting for profile elements: {e}")

            profiles = self.connected_service.driver.find_elements(By.CSS_SELECTOR, "div.search-result__info")
            logger.info(f"Found {len(profiles)} profiles on the current page.")
            for profile in profiles:
                try:
                    profile_text = profile.text
                    all_profiles.append(profile_text)
                except Exception as e:
                    logger.error(f"Error extracting profile text: {e}")

            logger.info(f"✅ Completed people search. Extracted {len(all_profiles)} profiles.")
            self.results_ready.emit(all_profiles)
        except Exception as e:
            logger.error(f"❌ Error during people search: {e}")
        finally:
            self.finished.emit()
