
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton
from app.gui.panels.actions_panel import ActionsPanel
from app.gui.panels.job_search_panel import JobSearchPanel
from app.gui.panels.job_actions_panel import JobActionsPanel
from app.gui.job_results_popup import JobResultsPopup  # ✅ Import JobResultsPopup
from app.gui.workers.feed_scroller_worker import FeedScrollWorker
from app.gui.panels.view_results_panel import ViewResultsPanel
from app.services.grow_hire_bot import GrowHireBot
from app.gui.panels.get_connected_panel import GetConnectedPanel
from PySide6.QtCore import QThread

import logging

logger = logging.getLogger(__name__)

class GrowHireGUI(QWidget):
    """Main Window for GrowHire"""

    def __init__(self, growhire_bot: GrowHireBot):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.feed_scraper = self.growhire_bot.feed_scraper
        self.feed_scroller_thread = None  # ✅ Thread for feed scrolling

        # ✅ Define job results pop-up BEFORE calling initUI
        self.job_results_popup = JobResultsPopup(self)

        self.initUI()

    def initUI(self):
        """Initialize the main UI layout."""
        self.setWindowTitle("GrowHire - LinkedIn Job Automation")
        self.setGeometry(300, 200, 750, 750)
        layout = QVBoxLayout()

        # ✅ Actions Section
        self.actions_panel = ActionsPanel(self.growhire_bot)
        layout.addWidget(self.actions_panel)

        # ✅ Feed Scroller Section
        self.feed_scroller_box = QGroupBox("📜 Feed Scroller")
        feed_scroller_layout = QHBoxLayout()
        self.start_scroller_button = QPushButton("▶ Start Scroller")
        self.start_scroller_button.clicked.connect(self.start_feed_scroller)
        feed_scroller_layout.addWidget(self.start_scroller_button)
        self.stop_scroller_button = QPushButton("⏹ Stop Scroller")
        self.stop_scroller_button.clicked.connect(self.stop_feed_scroller)
        self.stop_scroller_button.setEnabled(False)
        feed_scroller_layout.addWidget(self.stop_scroller_button)
        self.feed_scroller_box.setLayout(feed_scroller_layout)
        layout.addWidget(self.feed_scroller_box)

        # ✅ Get Connected Section (new panel)
        self.get_connected_panel = GetConnectedPanel(self.growhire_bot)
        layout.addWidget(self.get_connected_panel)

        # ✅ Job Search Section
        self.job_search_panel = JobSearchPanel(self.growhire_bot)
        layout.addWidget(self.job_search_panel)

        # ✅ Job Actions Section (Pass JobResultsPopup and JobSearchPanel)
        self.job_actions_panel = JobActionsPanel(self.growhire_bot, self.job_results_popup, self.job_search_panel)
        layout.addWidget(self.job_actions_panel)

        # ✅ View Results Section
        self.view_results_panel = ViewResultsPanel(self.growhire_bot)
        layout.addWidget(self.view_results_panel)

        self.setLayout(layout)



    def start_feed_scroller(self):
        """Starts the feed scroller in a separate thread."""
        if self.feed_scroller_thread is not None and self.feed_scroller_thread.isRunning():
            logger.warning("⚠️ Feed Scroller is already running!")
            return

        logger.info("🔄 Starting Feed Scroller in a separate thread...")

        # Create a new QThread
        self.feed_scroller_thread = QThread()
        # Create the worker instance
        self.feed_scroller_worker = FeedScrollWorker(self.feed_scraper, max_scrolls=15)
        # Move the worker to the new thread
        self.feed_scroller_worker.moveToThread(self.feed_scroller_thread)
        
        # Connect thread's started signal to the worker's run method
        self.feed_scroller_thread.started.connect(self.feed_scroller_worker.run)
        # Connect worker signals
        self.feed_scroller_worker.scroll_completed.connect(self.on_scrolling_complete)
        self.feed_scroller_worker.finished.connect(self.on_scroller_finished)
        # Optionally, clean up the worker and thread when done:
        self.feed_scroller_thread.finished.connect(self.feed_scroller_thread.deleteLater)
        self.feed_scroller_worker.finished.connect(self.feed_scroller_worker.deleteLater)

        # Start the thread
        self.feed_scroller_thread.start()

        # Update UI buttons
        self.start_scroller_button.setEnabled(False)
        self.stop_scroller_button.setEnabled(True)



    def on_scroller_finished(self):
        """Slot called when the feed scroller thread has finished."""
        logger.info("✅ Feed Scroller has finished.")
        # Reset the thread reference
        self.feed_scroller_thread = None
        # Update UI buttons: enable the start button and disable the stop button
        self.start_scroller_button.setEnabled(True)
        self.stop_scroller_button.setEnabled(False)



    def stop_feed_scroller(self):
        """Stops the feed scroller thread safely."""
        if self.feed_scroller_thread is None or not self.feed_scroller_thread.isRunning():
            logger.warning("⚠️ Feed Scroller is not running!")
            return

        logger.info("🚨 Stopping Feed Scroller...")
        # Call the worker's stop method to set the flag.
        if hasattr(self, 'feed_scroller_worker') and self.feed_scroller_worker is not None:
            self.feed_scroller_worker.stop()

        self.feed_scroller_thread.quit()
        self.feed_scroller_thread.wait()

        # Reset references
        self.feed_scroller_thread = None
        self.feed_scroller_worker = None

        self.start_scroller_button.setEnabled(True)
        self.stop_scroller_button.setEnabled(False)


    def on_scrolling_complete(self, extracted_posts):
        """Handles new posts extracted from the feed scroller."""
        if extracted_posts:
            logger.info(f"✅ Extracted {len(extracted_posts)} new posts from the LinkedIn feed.")
        else:
            logger.info("ℹ️ No new posts found in the latest scrolling session.")
