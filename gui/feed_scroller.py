# gui/feed_scroller.py
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication
import time
import logging

logger = logging.getLogger(__name__)

class FeedScrollWorker(QThread):
    """Background worker thread for running the LinkedIn feed scroller."""
    scroll_completed = Signal(list)

    def __init__(self, scraper, max_scrolls=10):
        super().__init__()
        self.scraper = scraper
        self.max_scrolls = max_scrolls
        self.running = True  

    def run(self):
        """Executes the scroller in a separate thread, continuously fetching posts."""
        all_extracted_posts = []
        while self.running:
            try:
                new_posts = self.scraper.scroll_and_extract_posts(self.max_scrolls)
                if new_posts:
                    all_extracted_posts.extend(new_posts)
                    self.scroll_completed.emit(new_posts)  

                QApplication.processEvents()  
                time.sleep(5)  

            except Exception as e:
                logger.error(f"❌ Error while scrolling: {e}")
                break  

        logger.info("🛑 Feed Scrolling Stopped.")

    def stop(self):
        """Stops the scrolling process safely."""
        self.running = False
        self.wait()  
