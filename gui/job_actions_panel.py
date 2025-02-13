from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel
from PySide6.QtCore import QThread, QObject, Signal
import logging

logger = logging.getLogger(__name__)

class JobSearchWorker(QObject):
    """Worker class to handle job searching in a separate thread."""
    finished = Signal()

    def __init__(self, growhire_bot, job_title, location, filters):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.job_title = job_title
        self.location = location
        self.filters = filters

    def run(self):
        """Runs the job search process."""
        try:
            logger.info("🔄 Searching for jobs...")
            self.growhire_bot.linkedin_navigator.search_jobs(self.job_title, self.location, self.filters)
        except Exception as e:
            logger.error(f"❌ Error during job search: {e}")
        finally:
            self.finished.emit()


class JobMatchWorker(QObject):
    """Worker class to handle job matching in a separate thread."""
    finished = Signal()

    def __init__(self, growhire_bot, num_pages):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.num_pages = num_pages

    def run(self):
        """Runs the job matching process."""
        try:
            logger.info("🔄 Extracting job descriptions...")
            job_descriptions = self.growhire_bot.extract_job_descriptions(num_pages=self.num_pages)

            if not job_descriptions:
                logger.warning("⚠️ No job descriptions found. Exiting match analysis.")
                return
            
            logger.info("🔄 Evaluating job matches...")
            job_match_results = self.growhire_bot.evaluate_job_matches(job_descriptions)

            if not job_match_results:
                logger.warning("⚠️ No job matches found. Exiting display update.")
                return
            
            self.growhire_bot.save_job_matches_to_db(job_match_results)

        except Exception as e:
            logger.error(f"❌ Error during job match evaluation: {e}")
        finally:
            self.finished.emit()


class JobActionsPanel(QGroupBox):
    """Panel for job search and evaluation actions."""

    def __init__(self, growhire_bot):
        super().__init__("📌 Job Actions")
        self.growhire_bot = growhire_bot
        self.search_thread = None
        self.match_thread = None
        self.initUI()

    def initUI(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # ✅ Search Jobs Button
        self.search_button = QPushButton("🔍 Search Jobs")
        self.search_button.clicked.connect(self.start_search_thread)  # ✅ Runs on separate thread
        layout.addWidget(self.search_button)

        # ✅ Find Best Match Button
        self.find_match_button = QPushButton("🔎 Find Best Match")
        self.find_match_button.clicked.connect(self.start_match_thread)  # ✅ Runs on separate thread
        layout.addWidget(self.find_match_button)

        # ✅ Page Selector
        pages_layout = QHBoxLayout()
        pages_label = QLabel("📄 Pages:")
        self.pages_dropdown = QComboBox()
        self.pages_dropdown.addItems([str(i) for i in range(1, 11)])  # Options: 1 to 10
        self.pages_dropdown.setCurrentIndex(0)  # Default: 1 Page
        pages_layout.addWidget(pages_label)
        pages_layout.addWidget(self.pages_dropdown)
        layout.addLayout(pages_layout)

        self.setLayout(layout)

    def start_search_thread(self):
        """Starts the job search process in a separate QThread."""
        if self.search_thread and self.search_thread.isRunning():
            logger.warning("⚠️ Job search is already in progress.")
            return

        logger.info("🚀 Starting job search...")

        # ✅ Extract filter values
        job_title = "Software Engineer"  # Replace with UI input if needed
        location = "Israel"  # Replace with UI input if needed
        filters = {}  # Pass relevant filters from UI inputs

        # ✅ Create the QThread and Worker
        self.search_thread = QThread()
        self.search_worker = JobSearchWorker(self.growhire_bot, job_title, location, filters)

        # ✅ Move worker to thread
        self.search_worker.moveToThread(self.search_thread)

        # ✅ Connect signals
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)

        # ✅ Start the thread
        self.search_thread.start()

    def start_match_thread(self):
        """Starts the job match evaluation process in a separate QThread."""
        if self.match_thread and self.match_thread.isRunning():
            logger.warning("⚠️ Job match evaluation is already in progress.")
            return

        logger.info("🚀 Starting job match evaluation...")

        # ✅ Extract number of pages from UI
        num_pages = int(self.pages_dropdown.currentText())

        # ✅ Create the QThread and Worker
        self.match_thread = QThread()
        self.match_worker = JobMatchWorker(self.growhire_bot, num_pages)

        # ✅ Move worker to thread
        self.match_worker.moveToThread(self.match_thread)

        # ✅ Connect signals
        self.match_thread.started.connect(self.match_worker.run)
        self.match_worker.finished.connect(self.match_thread.quit)
        self.match_worker.finished.connect(self.match_worker.deleteLater)
        self.match_thread.finished.connect(self.match_thread.deleteLater)

        # ✅ Start the thread
        self.match_thread.start()
