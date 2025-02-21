from PySide6.QtCore import QThread
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout
import logging
from app.gui.workers.job_search_worker import JobSearchWorker  # ✅ Import JobSearchWorker
from app.gui.job_results_popup import JobResultsPopup


# ✅ Initialize Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # ✅ Set log level to INFO

class JobActionsPanel(QGroupBox):
    """Panel for job search and evaluation actions."""
    
    def __init__(self, growhire_bot, job_results_table, job_search_panel):
        super().__init__("📌 Job Actions")
        self.growhire_bot = growhire_bot
        self.job_results_table = job_results_table  # ✅ Store reference to JobResultsTable
        self.job_search_panel = job_search_panel

        self.search_thread = None
        self.initUI()

    def initUI(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # ✅ Search Jobs Button
        self.search_button = QPushButton("🔍 Search Jobs")
        self.search_button.clicked.connect(self.start_search_thread)  # ✅ Runs in a separate thread
        layout.addWidget(self.search_button)

        # ✅ Page Selector
        pages_layout = QHBoxLayout()
        pages_label = QLabel("📄 Pages:")
        self.pages_dropdown = QComboBox()
        self.pages_dropdown.addItems([str(i) for i in range(1, 11)])  # Options: 1 to 10
        self.pages_dropdown.setCurrentIndex(0)  # Default: 1 Page
        pages_layout.addWidget(pages_label)
        pages_layout.addWidget(self.pages_dropdown)
        layout.addLayout(pages_layout)

        self.setLayout(layout)  # ✅ Set layout for JobActionsPanel

    def start_search_thread(self):
        """Starts the job search in a separate thread and opens the results popup."""
        if self.search_thread and self.search_thread.isRunning():
            logger.warning("⚠️ Job search is already in progress.")
            return

        logger.info("🚀 Starting job search...")

        # Extract job title, location, and filters from the UI
        job_title = self.job_search_panel.job_title_field.text() or "Software Engineer"
        location = self.job_search_panel.location_field.text() or "Israel"
        filters = self.job_search_panel.get_filters()

        # Log the filter values for debugging
        logger.info(f"🔍 Job search filters: {filters}")

        # Retrieve the number of pages from the dropdown
        num_pages = int(self.pages_dropdown.currentText())
        logger.info(f"📄 Number of pages selected: {num_pages}")

        # Create the QThread and Worker, now passing num_pages to the worker
        self.search_thread = QThread()
        logger.info(f"🔍 Type of growhire_bot: {type(self.growhire_bot)}")

        self.search_worker = JobSearchWorker(self.growhire_bot, job_title, location, filters, num_pages=num_pages)
        self.search_worker.moveToThread(self.search_thread)

        # Connect signals
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)

        # Show popup when results are ready
        self.search_worker.results_ready.connect(self.show_results_popup)

        # Start the thread
        self.search_thread.start()




    def show_results_popup(self, job_results):
        """Opens the job results popup and updates the results."""
        logger.info("📋 Job search completed, displaying results.")

        # ✅ Prevent multiple popups by checking if one is already open
        if hasattr(self, "job_results_popup") and self.job_results_popup.isVisible():
            logger.warning("⚠️ Job results popup is already open.")
            return

        # ✅ Create and show the popup
        self.job_results_popup = JobResultsPopup(self.growhire_bot)
        self.job_results_popup.update_results(job_results)
        self.job_results_popup.exec()  # ✅ Show as modal dialog
