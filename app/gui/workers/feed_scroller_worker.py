# gui/feed_scroller.py
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QThread

import time
import logging

logger = logging.getLogger(__name__)

class FeedScrollWorker(QObject):
    scroll_completed = Signal(object)
    finished = Signal()

    def __init__(self, feed_scraper, max_scrolls=15):
        super().__init__()
        self.feed_scraper = feed_scraper
        self.max_scrolls = max_scrolls
        self._stop_requested = False

    def run(self):
        """Main method that scrolls and extracts posts."""
        try:
            for scroll_count in range(self.max_scrolls):
                if self._stop_requested:
                    logger.info("🛑 Stop requested. Exiting feed scroller loop.")
                    break

                # Use the correct method name from your feed_scraper.
                # For example, if the method is named scroll_and_extract_posts:
                new_posts = self.feed_scraper.scroll_and_extract_posts()
                self.scroll_completed.emit(new_posts)

                # Optionally, add a small delay (in ms) to yield control:
                QThread.msleep(100)

            logger.info("Feed scroller run() completed.")
        except Exception as e:
            logger.error(f"Error during feed scrolling: {e}")
        finally:
            self.finished.emit()

    def stop(self):
        """Sets a flag to stop the feed scroller."""
        logger.info("Stop signal received in FeedScrollWorker.")
        self._stop_requested = True