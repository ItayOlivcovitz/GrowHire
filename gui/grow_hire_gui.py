import os
import sys
import logging
import webbrowser  # Required for opening job URLs
import time
from PySide6.QtWidgets import QApplication  # ✅ Import QApplication for processEvents()
import threading



# ✅ PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit,
    QComboBox, QCheckBox, QFileDialog, QGroupBox, QSpacerItem, QSizePolicy, QSplitter,
    QTableWidget, QTableWidgetItem
)

from PySide6.QtGui import QColor, QFont, QTextOption  # GUI Styling & Text Formatting
from PySide6.QtCore import Qt  # Core Functionality

# ✅ Environment Variables
from dotenv import load_dotenv

# ✅ Services
from services.grow_hire_bot import GrowHireBot
from services.grow_hire_bot import FeedScraper  # ✅ Added Feed Scraper Import

# ✅ Multithreading for UI Responsiveness
from PySide6.QtCore import QThread, Signal    # ✅ Needed for Background Scrolling






# ✅ Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FeedScrollWorker(QThread):
    """Background worker thread for running the LinkedIn feed scroller."""
    scroll_completed = Signal(list) 

    def __init__(self, scraper, max_scrolls=10):
        super().__init__()
        self.scraper = scraper
        self.max_scrolls = max_scrolls
        self.running = True  # Flag to control scrolling

    def run(self):
        """Executes the scroller in a separate thread."""
        extracted_posts = self.scraper.scroll_and_extract_posts(self.max_scrolls) if self.running else []
        self.scroll_completed.emit(extracted_posts)

    def stop(self):
        """Stops the scrolling process."""
        self.running = False
class GrowHireGUI(QWidget):
    def __init__(self, growhire_bot: GrowHireBot):
        super().__init__()

        # ✅ Initialize GrowHireBot
        self.growhire_bot = growhire_bot

        # ✅ Initialize Feed Scraper
        self.feed_scraper = growhire_bot.feed_scraper

        # ✅ Initialize Scrolling Variables
        self.scrolling_active = False  # 🔹 Prevents AttributeError
        self.scroller_thread = None  # 🔹 Prevents NoneType errors

        self.initUI()  # ✅ Initialize UI components
   
    def initUI(self):
            """Initialize the UI layout and components for the job automation tool."""
            self.setWindowTitle("GrowHire - LinkedIn Job Automation")
            self.setGeometry(300, 200, 750, 750)
            layout = QVBoxLayout()

            ### 🔹 Actions Section (FIRST SECTION - OPEN LINKEDIN)
            actions_box = QGroupBox("🚀 Actions")
            actions_layout = QVBoxLayout()

            # Open LinkedIn Button (First Button in the GUI)
            self.login_button = QPushButton("🌐 Open LinkedIn Login")
            self.login_button.clicked.connect(self.growhire_bot.linkedin_navigator.open_linkedin)
            actions_layout.addWidget(self.login_button)

            actions_box.setLayout(actions_layout)
            layout.addWidget(actions_box)  # First section added

            ### 🔹 Feed Scroller Section (New!)
            feed_scroller_box = QGroupBox("📜 Feed Scroller")
            feed_scroller_layout = QHBoxLayout()

            # ✅ Start Scroller Button
            self.start_scroller_button = QPushButton("▶ Start Scroller")
            self.start_scroller_button.clicked.connect(self.start_scroller)
            feed_scroller_layout.addWidget(self.start_scroller_button)

            # ✅ Stop Scroller Button
            self.stop_scroller_button = QPushButton("⏹ Stop Scroller")
            self.stop_scroller_button.clicked.connect(self.stop_scroller)
            self.stop_scroller_button.setEnabled(False)  # Initially disabled
            feed_scroller_layout.addWidget(self.stop_scroller_button)

            feed_scroller_box.setLayout(feed_scroller_layout)
            layout.addWidget(feed_scroller_box)  # ✅ Add to UI

            ### 🔹 Job Search Section
            job_search_box = QGroupBox("🔍 Job Search")
            job_search_layout = QVBoxLayout()

            # Job Title Input
            self.job_title_field = QLineEdit()
            self.job_title_field.setPlaceholderText("Enter Job Title (Default: 'Software Engineer')")
            job_search_layout.addWidget(QLabel("🔹 Job Title:"))
            job_search_layout.addWidget(self.job_title_field)

            # Job Location Input
            self.location_field = QLineEdit()
            self.location_field.setPlaceholderText("Enter Job Location (Default: 'Israel')")
            job_search_layout.addWidget(QLabel("📍 Job Location:"))
            job_search_layout.addWidget(self.location_field)

            # Date Posted Dropdown
            self.date_posted_dropdown = QComboBox()
            self.date_posted_dropdown.addItems(["Any Time", "Past 24 hours", "Past Week", "Past Month"])
            job_search_layout.addWidget(QLabel("📅 Date Posted:"))
            job_search_layout.addWidget(self.date_posted_dropdown)

            # Experience Level Dropdown
            self.experience_level_dropdown = QComboBox()
            self.experience_level_dropdown.addItems(["Any", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"])
            job_search_layout.addWidget(QLabel("💼 Experience Level:"))
            job_search_layout.addWidget(self.experience_level_dropdown)

            # Company Input
            self.company_field = QLineEdit()
            self.company_field.setPlaceholderText("Enter Company Name (Optional)")
            job_search_layout.addWidget(QLabel("🏢 Company Name (Optional):"))
            job_search_layout.addWidget(self.company_field)

            # Work Type
            work_type_box = QGroupBox("🖥️ Work Type")
            work_type_layout = QHBoxLayout()

            self.remote_hybrid = QCheckBox("Hybrid")
            self.remote_onsite = QCheckBox("On-site")
            self.remote_remote = QCheckBox("Remote")

            work_type_layout.addWidget(self.remote_hybrid)
            work_type_layout.addWidget(self.remote_onsite)
            work_type_layout.addWidget(self.remote_remote)
            work_type_box.setLayout(work_type_layout)
            job_search_layout.addWidget(work_type_box)

            # Easy Apply Checkbox
            self.easy_apply_checkbox = QCheckBox("⚡ Easy Apply Only")
            job_search_layout.addWidget(self.easy_apply_checkbox)

            job_search_box.setLayout(job_search_layout)
            layout.addWidget(job_search_box)

            ### 🔹 Job Actions Section
            job_actions_box = QGroupBox("📌 Job Actions")
            job_actions_layout = QVBoxLayout()

            # Search Jobs Button
            self.search_button = QPushButton("🔍 Search Jobs")
            self.search_button.clicked.connect(self.search_jobs)
            self.search_button.setEnabled(True)
            job_actions_layout.addWidget(self.search_button)

            # Start Scan for New Jobs Button
            self.start_scan_button = QPushButton("🔎 Start Scan for New Jobs")
            self.start_scan_button.clicked.connect(self.find_best_match)
            self.start_scan_button.setEnabled(True)
            job_actions_layout.addWidget(self.start_scan_button)

            # Page Selector
            pages_layout = QHBoxLayout()
            pages_label = QLabel("📄 Pages:")
            self.pages_dropdown = QComboBox()
            self.pages_dropdown.addItems([str(i) for i in range(1, 11)])  # Options: 1 to 10
            self.pages_dropdown.setCurrentIndex(0)  # Default: 1 Page
            pages_layout.addWidget(pages_label)
            pages_layout.addWidget(self.pages_dropdown)
            job_actions_layout.addLayout(pages_layout)

            job_actions_box.setLayout(job_actions_layout)
            layout.addWidget(job_actions_box)

        # Job Search Results Table
            results_box = QGroupBox("📋 Job Search Results")
            results_layout = QVBoxLayout()

            self.results_table = QTableWidget()
            self.results_table.setColumnCount(7)  # ✅ Updated to 7 columns
            self.results_table.setHorizontalHeaderLabels([
                "Job Title", "Company", "Score", "Job URL", "Job Description", "ChatGPT Response", "Connections"
            ])
            self.results_table.horizontalHeader().setStretchLastSection(True)
            self.results_table.setMinimumHeight(300)

            results_layout.addWidget(self.results_table)
            results_box.setLayout(results_layout)
            layout.addWidget(results_box)

            self.setLayout(layout)


    def handle_login_complete(self, success):
        """Handles LinkedIn login completion."""
        if success:
            logger.info("✅ Successfully logged into LinkedIn.")
        else:
            logger.error("❌ LinkedIn login failed. Please try again.")

        # Re-enable the button after login attempt
        self.login_button.setEnabled(True)  

    def start_scroller(self):
        """Starts the LinkedIn feed scroller and continuously extracts & saves posts."""
        if self.scrolling_active:
            logger.warning("⚠️ Scroller is already running!")
            return  # Prevent multiple executions

        self.scrolling_active = True
        self.start_scroller_button.setEnabled(False)
        self.stop_scroller_button.setEnabled(True)
        self.extracted_posts = []  # ✅ Store extracted posts to save later
        self.seen_posts = set()  # ✅ Track already saved posts

        logger.info("🔄 Scroller started. Running continuously until stopped...")

        def scroll_loop():
            """Runs the scrolling loop, extracts posts, and saves them continuously."""
            while self.scrolling_active:
                try:
                    new_posts = self.feed_scraper.scroll_and_extract_posts(max_scrolls=15)

                    if new_posts:
                        # ✅ Filter out duplicates before saving
                        unique_posts = [post for post in new_posts if post["post_id"] not in self.seen_posts]
                        for post in unique_posts:
                            self.seen_posts.add(post["post_id"])  # ✅ Mark as seen

                        if unique_posts:
                            self.growhire_bot.save_job_posts_to_db(unique_posts)  # ✅ Save to database
                            self.extracted_posts.extend(unique_posts)  # ✅ Store posts in memory
                            logger.info(f"✅ Saved {len(unique_posts)} new posts. Total extracted: {len(self.extracted_posts)}")

                    QApplication.processEvents()  # ✅ Prevent UI freezing
                    time.sleep(10)  # ✅ Adjust delay if needed

                except Exception as e:
                    logger.error(f"❌ Error while scrolling: {e}")

            logger.info("🛑 Scrolling stopped. Preparing to save remaining posts...")

        # ✅ Run scrolling in a separate thread to avoid blocking the UI
        self.scrolling_thread = threading.Thread(target=scroll_loop, daemon=True)
        self.scrolling_thread.start()

    def stop_scroller(self):
        """Stops scrolling and ensures all extracted posts are saved to the database."""
        if not self.scrolling_active:
            logger.warning("⚠️ Scroller is already stopped!")
            return  # Already stopped

        logger.info("🚨 Stopping the scroller...")

        self.scrolling_active = False
        self.start_scroller_button.setEnabled(True)
        self.stop_scroller_button.setEnabled(False)

        # ✅ Wait for the scrolling thread to finish
        if self.scrolling_thread and self.scrolling_thread.is_alive():
            self.scrolling_thread.join()

        # ✅ Save remaining extracted posts to the database
        try:
            remaining_posts = [post for post in self.extracted_posts if post["post_id"] not in self.seen_posts]
            if remaining_posts:
                self.growhire_bot.save_job_posts_to_db(remaining_posts)
                logger.info(f"✅ Saved {len(remaining_posts)} remaining posts to the database.")
            else:
                logger.info("ℹ️ No remaining posts to save.")
        except Exception as e:
            logger.error(f"❌ Error saving posts to database: {e}")

        logger.info("🛑 Scroller fully stopped.")
        
    def search_jobs(self):
        """Extracts selected filters and performs a job search."""

        job_title = self.job_title_field.text().strip() or "Software Engineer"
        location = self.location_field.text().strip() or "Israel"

        # ✅ Construct filters dictionary
        filters = {
            "date_posted": self.date_posted_dropdown.currentText(),  # Get selected date filter
            "experience_level": self.experience_level_dropdown.currentText(),  # Get selected experience level
            "company": self.company_field.text().strip(),  # Get entered company name
            "remote_options": [
                option.text() for option in [self.remote_hybrid, self.remote_onsite, self.remote_remote] if option.isChecked()
            ],
            "easy_apply": self.easy_apply_checkbox.isChecked()
        }

        # ✅ Pass selected filters to the bot
        self.growhire_bot.linkedin_navigator.search_jobs(job_title, location, filters)

    def find_best_match(self):
        """Starts looping through job listings, extracting job descriptions, and evaluating matches, then displays results."""
        logger.info("🔄 Starting job match analysis for all jobs...")

        # Get the number of pages
        num_pages = int(self.pages_dropdown.currentText())  

        # Extract job descriptions
        job_descriptions = self.growhire_bot.extract_job_descriptions(num_pages=num_pages)

        if not job_descriptions:
            logger.warning("⚠️ No job descriptions found. Exiting match analysis.")
            return

        # Evaluate matches
        job_match_results = self.growhire_bot.evaluate_job_matches(job_descriptions)

        if not job_match_results:
            logger.warning("⚠️ No job matches found. Exiting display update.")
            return

        # Save match results to DB
        self.growhire_bot.save_job_matches_to_db(job_match_results)

        # ✅ Display results in the GUI
        self.display_search_results(job_match_results)

        logger.info("✅ Job match analysis completed and displayed successfully.")

    def display_search_results(self, job_match_results):
        """Displays job search results in the QTableWidget with scrollable descriptions without affecting the table scroll."""
        self.results_table.setSortingEnabled(False)  # ✅ Disable sorting while inserting data
        self.results_table.setRowCount(0)  # ✅ Clear previous results

        # ✅ Update column headers
        self.results_table.setHorizontalHeaderLabels([
            "Job Title", "Company", "Score", "Job URL", "Job Description", "ChatGPT Response", "Connections"
        ])

        # ✅ Remove duplicate jobs using a dictionary with job URLs as keys
        unique_jobs = {}
        for job in job_match_results:
            job_url = job.get("job_url", "N/A")
            if job_url not in unique_jobs:
                unique_jobs[job_url] = job  # ✅ Keep only the first occurrence

        # ✅ Sort jobs by Score
        sorted_results = sorted(
            unique_jobs.values(),
            key=lambda x: int(x.get("score", 0) if str(x.get("score")).isdigit() else 0), 
            reverse=True
        )

        for row_index, job in enumerate(sorted_results):
            job_title = job.get("job_title", "N/A")
            company_name = job.get("company_name", "N/A")
            score = job.get("score", "N/A")
            score_str = str(score) if str(score).isdigit() else "N/A"
            score_int = int(score) if score_str.isdigit() else 0
            job_url = job.get("job_url", "N/A")
            job_description = str(job.get("job_description", "N/A"))
            chat_gpt_response = str(job.get("chat_gpt_response", "N/A"))
            connections = job.get("connections", "N/A")
            connections_str = str(connections)

            self.results_table.insertRow(row_index)

            # ✅ Job Title (Centered)
            title_item = QTableWidgetItem(job_title)
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row_index, 0, title_item)

            # ✅ Company Name (Centered)
            company_item = QTableWidgetItem(company_name)
            company_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row_index, 1, company_item)

            # ✅ Score with Color Coding (Centered)
            score_item = QTableWidgetItem(score_str)
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if score_int >= 80:
                score_item.setBackground(QColor(144, 238, 144))  # ✅ Green for High Scores
            elif 50 <= score_int < 80:
                score_item.setBackground(QColor(255, 255, 153))  # ✅ Yellow for Medium Scores
            else:
                score_item.setBackground(QColor(255, 102, 102))  # ✅ Red for Low Scores
            self.results_table.setItem(row_index, 2, score_item)

            # ✅ Job URL as Clickable Link
            url_item = QTableWidgetItem("🔗 Open Job")
            url_item.setForeground(QColor(0, 0, 255))  # ✅ Blue clickable text
            url_item.setToolTip(f"Click to open: {job_url}")
            url_item.setData(Qt.UserRole, job_url)
            url_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row_index, 3, url_item)

            # ✅ Job Description with Scrollable TextEdit (with Scroll Lock)
            description_widget = ScrollLockTextEdit()
            description_widget = ScrollLockTextEdit(job_description)
            self.results_table.setCellWidget(row_index, 4, description_widget)

            # ✅ ChatGPT Response with Scrollable TextEdit (with Scroll Lock)
            chatgpt_widget = ScrollLockTextEdit()
            chatgpt_widget = ScrollLockTextEdit(chat_gpt_response)
            self.results_table.setCellWidget(row_index, 5, chatgpt_widget)

            # ✅ Connections (Centered)
            connections_item = QTableWidgetItem(connections_str)
            connections_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row_index, 6, connections_item)

        # ✅ Adjust Column Widths
        self.results_table.setColumnWidth(0, 150)  # Job Title
        self.results_table.setColumnWidth(1, 150)  # Company
        self.results_table.setColumnWidth(2, 80)   # Score
        self.results_table.setColumnWidth(3, 120)  # Job URL
        self.results_table.setColumnWidth(4, 400)  # Job Description
        self.results_table.setColumnWidth(5, 400)  # ChatGPT Response
        self.results_table.setColumnWidth(6, 100)  # Connections

        # ✅ Auto-resize row heights to fit descriptions
        self.results_table.resizeRowsToContents()

        # ✅ Re-enable sorting after inserting data
        self.results_table.setSortingEnabled(True)

        print("✅ All job data added and displayed correctly.")

        # ✅ Make Job URL Clickable
        self.results_table.cellClicked.connect(self.open_url)

    def open_url(self, row, column):
        """Opens job URL when clicked."""
        if column == 3:  # ✅ Column index for Job URL
            url_item = self.results_table.item(row, column)
            if url_item:
                url = url_item.data(Qt.UserRole)
                if url and url.startswith("http"):
                    webbrowser.open(url)

class ScrollLockTextEdit(QTextEdit):
    """A QTextEdit with independent scrolling that prevents table scrolling."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # ✅ Ensure text is properly displayed
        self.setPlainText(text)

        # ✅ Fix visibility issue
        self.setMinimumHeight(100)  # Ensures visible area for job description
        self.setMaximumHeight(200)  # Prevents overly large descriptions

    def wheelEvent(self, event):
        """Handles scroll to prevent affecting the table."""
        if self.verticalScrollBar().isVisible() and self.verticalScrollBar().maximum() > 0:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + event.angleDelta().y() / 120)
            event.accept()
        else:
            event.ignore()


  


