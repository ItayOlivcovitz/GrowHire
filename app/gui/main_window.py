from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QFont
from app.gui.panels.actions_panel import ActionsPanel
from app.gui.panels.job_search_panel import JobSearchPanel
from app.gui.panels.job_actions_panel import JobActionsPanel
from app.gui.job_results_popup import JobResultsPopup
from app.gui.workers.feed_scroller_worker import FeedScrollWorker
from app.gui.panels.view_results_panel import ViewResultsPanel
from app.gui.panels.debugging_panel import DebuggingPanel
from app.services.grow_hire_bot import GrowHireBot
from app.gui.panels.get_connected_panel import GetConnectedPanel
from app.gui.styles import COLORS, get_header_style

import logging

logger = logging.getLogger(__name__)


class GrowHireGUI(QWidget):
    """Main Window for GrowHire."""

    def __init__(self, growhire_bot: GrowHireBot):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.feed_scraper = self.growhire_bot.feed_scraper
        self.feed_scroller_thread = None
        self.job_results_popup = JobResultsPopup(self)
        self.initUI()

    def initUI(self):
        """Initialize the main UI layout."""
        self.setWindowTitle("GrowHire — LinkedIn Job Automation")
        self.setGeometry(280, 160, 820, 820)
        self.setMinimumSize(520, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel("GrowHire")
        header.setStyleSheet(get_header_style())
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(header)

        subtitle = QLabel("LinkedIn job search with AI-powered match scoring")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; padding-bottom: 8px;")
        main_layout.addWidget(subtitle)

        # Scroll area for panels so everything fits on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 8, 0, 0)

        self.actions_panel = ActionsPanel(self.growhire_bot)
        layout.addWidget(self.actions_panel)

        self.feed_scroller_box = QGroupBox("Feed Scroller")
        feed_scroller_layout = QHBoxLayout()
        self.start_scroller_button = QPushButton("Start Scroller")
        self.start_scroller_button.clicked.connect(self.start_feed_scroller)
        feed_scroller_layout.addWidget(self.start_scroller_button)
        self.stop_scroller_button = QPushButton("Stop Scroller")
        self.stop_scroller_button.clicked.connect(self.stop_feed_scroller)
        self.stop_scroller_button.setEnabled(False)
        feed_scroller_layout.addWidget(self.stop_scroller_button)
        self.feed_scroller_box.setLayout(feed_scroller_layout)
        layout.addWidget(self.feed_scroller_box)

        self.get_connected_panel = GetConnectedPanel(self.growhire_bot)
        layout.addWidget(self.get_connected_panel)

        self.job_search_panel = JobSearchPanel(self.growhire_bot)
        layout.addWidget(self.job_search_panel)

        self.job_actions_panel = JobActionsPanel(
            self.growhire_bot, self.job_results_popup, self.job_search_panel
        )
        layout.addWidget(self.job_actions_panel)

        self.view_results_panel = ViewResultsPanel(self.growhire_bot)
        layout.addWidget(self.view_results_panel)

        self.debugging_panel = DebuggingPanel(self.growhire_bot)
        layout.addWidget(self.debugging_panel)

        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)



    def start_feed_scroller(self):
        """Starts the feed scroller in a separate thread."""
        if self.feed_scroller_thread is not None and self.feed_scroller_thread.isRunning():
            logger.warning("⚠️ Feed Scroller is already running!")
            return

        logger.info("🔄 Starting Feed Scroller in a separate thread...")
        
        self.growhire_bot.linkedin_navigator.open_feed()

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
