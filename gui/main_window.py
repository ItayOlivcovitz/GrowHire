from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton
from gui.actions_panel import ActionsPanel
from gui.job_search_panel import JobSearchPanel
from gui.job_actions_panel import JobActionsPanel
from gui.job_results_table import JobResultsTable
from gui.feed_scroller import FeedScrollWorker  # ✅ Import Feed Scroller
from services.grow_hire_bot import GrowHireBot
from PySide6.QtCore import QThread

import logging

logger = logging.getLogger(__name__)

class GrowHireGUI(QWidget):
    """Main Window for GrowHire"""

    def __init__(self, growhire_bot: GrowHireBot):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.feed_scraper = self.growhire_bot.feed_scraper  # ✅ Ensure feed scraper is initialized
        self.feed_scroller_thread = None  # ✅ Thread for feed scrolling
        self.initUI()

    def initUI(self):
        """Initialize the main UI layout."""
        self.setWindowTitle("GrowHire - LinkedIn Job Automation")
        self.setGeometry(300, 200, 750, 750)
        layout = QVBoxLayout()

        # ✅ Actions Section
        self.actions_panel = ActionsPanel(self.growhire_bot)
        layout.addWidget(self.actions_panel)

        # ✅ Feed Scroller Section (New!)
        self.feed_scroller_box = QGroupBox("📜 Feed Scroller")
        feed_scroller_layout = QHBoxLayout()

        # ✅ Start Scroller Button
        self.start_scroller_button = QPushButton("▶ Start Scroller")
        self.start_scroller_button.clicked.connect(self.start_feed_scroller)
        feed_scroller_layout.addWidget(self.start_scroller_button)

        # ✅ Stop Scroller Button
        self.stop_scroller_button = QPushButton("⏹ Stop Scroller")
        self.stop_scroller_button.clicked.connect(self.stop_feed_scroller)
        self.stop_scroller_button.setEnabled(False)  # Initially disabled
        feed_scroller_layout.addWidget(self.stop_scroller_button)

        self.feed_scroller_box.setLayout(feed_scroller_layout)
        layout.addWidget(self.feed_scroller_box)

        # ✅ Job Search Section
        self.job_search_panel = JobSearchPanel(self.growhire_bot)
        layout.addWidget(self.job_search_panel)

        # ✅ Job Actions Section
        self.job_actions_panel = JobActionsPanel(self.growhire_bot)
        layout.addWidget(self.job_actions_panel)

        # ✅ Job Results Table
        self.job_results_table = JobResultsTable()
        layout.addWidget(self.job_results_table)

        self.setLayout(layout)

    def start_feed_scroller(self):
        """Starts the feed scroller on a separate QThread."""
        if self.feed_scroller_thread and self.feed_scroller_thread.isRunning():
            logger.warning("⚠️ Feed Scroller is already running!")
            return  # Prevent multiple executions

        logger.info("🔄 Starting Feed Scroller...")

        # ✅ Create a new thread
        self.feed_scroller_thread = QThread()

        # ✅ Create the worker
        self.feed_scroller_worker = FeedScrollWorker(self.feed_scraper, max_scrolls=15)

        # ✅ Move the worker to the separate thread
        self.feed_scroller_worker.moveToThread(self.feed_scroller_thread)

        # ✅ Connect signals
        self.feed_scroller_thread.started.connect(self.feed_scroller_worker.run)
        self.feed_scroller_worker.scroll_completed.connect(self.on_scrolling_complete)
        self.feed_scroller_worker.finished.connect(self.feed_scroller_thread.quit)
        self.feed_scroller_worker.finished.connect(self.feed_scroller_worker.deleteLater)
        self.feed_scroller_thread.finished.connect(self.feed_scroller_thread.deleteLater)

        # ✅ Start the thread
        self.feed_scroller_thread.start()

        # ✅ Update button states
        self.start_scroller_button.setEnabled(False)
        self.stop_scroller_button.setEnabled(True)

    def stop_feed_scroller(self):
        """Stops the feed scroller thread safely."""
        if not self.feed_scroller_worker or not self.feed_scroller_thread.isRunning():
            logger.warning("⚠️ Feed Scroller is not running!")
            return

        logger.info("🚨 Stopping Feed Scroller...")

        # ✅ Stop the worker
        self.feed_scroller_worker.stop()

        # ✅ Ensure the thread stops safely
        self.feed_scroller_thread.quit()
        self.feed_scroller_thread.wait()

        # ✅ Cleanup
        self.feed_scroller_thread = None
        self.feed_scroller_worker = None

        # ✅ Update button states
        self.start_scroller_button.setEnabled(True)
        self.stop_scroller_button.setEnabled(False)


    def on_scrolling_complete(self, extracted_posts):
        """Handles new posts extracted from the feed scroller."""
        if extracted_posts:
            logger.info(f"✅ Extracted {len(extracted_posts)} new posts from the LinkedIn feed.")
        else:
            logger.info("ℹ️ No new posts found in the latest scrolling session.")
