import os
import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, 
    QComboBox, QCheckBox, QFileDialog, QGroupBox, QSpacerItem, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt
from dotenv import load_dotenv, find_dotenv
from services.grow_hire_bot import GrowHireBot




# ✅ Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class GrowHireGUI(QWidget):
    def __init__(self,growhire_bot: GrowHireBot):
        super().__init__()

        # ✅ Initialize LinkedIn Bot and GrowHireBot with correct resume path
        self.growhire_bot = growhire_bot

        self.initUI()

   
      
    def handle_login_complete(self, success):
        """Handles LinkedIn login completion."""
        if success:
            logger.info("✅ Successfully logged into LinkedIn.")
        else:
            logger.error("❌ LinkedIn login failed. Please try again.")

        # Re-enable the button after login attempt
        self.login_button.setEnabled(True)  

    def initUI(self):
        """Initialize the UI layout and components for the job automation tool."""
        self.setWindowTitle("GrowHire - LinkedIn Job Automation")
        self.setGeometry(300, 200, 750, 750)
        layout = QVBoxLayout()

        ### 🔹 Job Search Filters Section
        job_filter_box = QGroupBox("🔍 Job Search Filters")
        job_filter_layout = QVBoxLayout()

        # Job Title Input
        self.job_title_field = QLineEdit()
        self.job_title_field.setPlaceholderText("Enter Job Title (Default: 'Software Engineer')")
        job_filter_layout.addWidget(QLabel("🔹 Job Title:"))
        job_filter_layout.addWidget(self.job_title_field)

        # Job Location Input
        self.location_field = QLineEdit()
        self.location_field.setPlaceholderText("Enter Job Location (Default: 'Israel')")
        job_filter_layout.addWidget(QLabel("📍 Job Location:"))
        job_filter_layout.addWidget(self.location_field)

        # Date Posted Dropdown
        self.date_posted_dropdown = QComboBox()
        self.date_posted_dropdown.addItems(["Any Time", "Past 24 hours", "Past Week", "Past Month"])
        job_filter_layout.addWidget(QLabel("📅 Date Posted:"))
        job_filter_layout.addWidget(self.date_posted_dropdown)

        # Experience Level Dropdown
        self.experience_level_dropdown = QComboBox()
        self.experience_level_dropdown.addItems(["Any", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"])
        job_filter_layout.addWidget(QLabel("💼 Experience Level:"))
        job_filter_layout.addWidget(self.experience_level_dropdown)

        # Company Input
        self.company_field = QLineEdit()
        self.company_field.setPlaceholderText("Enter Company Name (Optional)")
        job_filter_layout.addWidget(QLabel("🏢 Company Name (Optional):"))
        job_filter_layout.addWidget(self.company_field)

        job_filter_box.setLayout(job_filter_layout)
        layout.addWidget(job_filter_box)

        ### 🔹 Work Type Section
        work_type_box = QGroupBox("🖥️ Work Type")
        work_type_layout = QHBoxLayout()

        self.remote_hybrid = QCheckBox("Hybrid")
        self.remote_onsite = QCheckBox("On-site")
        self.remote_remote = QCheckBox("Remote")

        work_type_layout.addWidget(self.remote_hybrid)
        work_type_layout.addWidget(self.remote_onsite)
        work_type_layout.addWidget(self.remote_remote)
        work_type_box.setLayout(work_type_layout)
        layout.addWidget(work_type_box)

        ### 🔹 Easy Apply Checkbox
        self.easy_apply_checkbox = QCheckBox("⚡ Easy Apply Only")
        layout.addWidget(self.easy_apply_checkbox)

        ### 🔹 LinkedIn & Resume Actions
        action_box = QGroupBox("🚀 Actions")
        action_layout = QVBoxLayout()

        # Open LinkedIn Button
        self.login_button = QPushButton("🌐 Open LinkedIn Login")
        self.login_button.clicked.connect(self.growhire_bot.linkedin_navigator.open_linkedin)
        action_layout.addWidget(self.login_button)

        # Resume Upload Button
        self.upload_resume_button = QPushButton("📄 Upload Resume (Required)")
        self.upload_resume_button.clicked.connect(self.upload_resume)
        action_layout.addWidget(self.upload_resume_button)

        action_box.setLayout(action_layout)
        layout.addWidget(action_box)

        ### 🔹 Job Search Actions (MAKE SURE THIS IS ADDED TO LAYOUT)
        job_actions_box = QGroupBox("🔍 Job Search Actions")
        job_actions_layout = QVBoxLayout()

        # Search Jobs Button
        self.search_button = QPushButton("🔍 Search Jobs")
        self.search_button.clicked.connect(self.search_jobs)
        self.search_button.setEnabled(True)
        job_actions_layout.addWidget(self.search_button)

        # ✅ Layout for "Start Scan for New Jobs" and Page Selector
        scan_layout = QHBoxLayout()

        # Start Scan for New Jobs Button
        self.start_scan_button = QPushButton("🔎 Start Scan for New Jobs")
        self.start_scan_button.clicked.connect(self.find_best_match)
        self.start_scan_button.setEnabled(True)
        scan_layout.addWidget(self.start_scan_button)

        # ✅ Create a small form layout to keep "Pages:" and dropdown together
        pages_layout = QHBoxLayout()
        pages_label = QLabel("📄 Pages:")
        self.pages_dropdown = QComboBox()
        self.pages_dropdown.addItems([str(i) for i in range(1, 11)])  # Options: 1 to 10
        self.pages_dropdown.setCurrentIndex(0)  # Default: 1 Page

        pages_layout.addWidget(pages_label)
        pages_layout.addWidget(self.pages_dropdown)

        # ✅ Add the small layout next to the button (ensuring minimal spacing)
        scan_layout.addSpacing(20)  # Small spacing
        scan_layout.addLayout(pages_layout)  # Add label and dropdown inline

        # ✅ Add the horizontal layout instead of separate widgets
        job_actions_layout.addLayout(scan_layout)

        job_actions_box.setLayout(job_actions_layout)
        layout.addWidget(job_actions_box)  # 👈 MAKE SURE THIS IS ADDED!

        ### 🔹 Console Output (Log Window)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setPlaceholderText("📜 Console logs will appear here...")
        self.console_output.setMinimumHeight(200)
        layout.addWidget(self.console_output)

        ### 🔹 ChatGPT Output (SECOND CONSOLE)
        chatgpt_box = QGroupBox("🤖 ChatGPT Output")
        chatgpt_layout = QVBoxLayout()

        self.chatgpt_output = QTextEdit()
        self.chatgpt_output.setReadOnly(True)
        self.chatgpt_output.setPlaceholderText("🤖 ChatGPT logs will appear here...")
        self.chatgpt_output.setMinimumHeight(250)

        chatgpt_layout.addWidget(self.chatgpt_output)
        chatgpt_box.setLayout(chatgpt_layout)
        layout.addWidget(chatgpt_box)

        ### 🔹 Log Actions
        log_actions_box = QGroupBox("🛠️ Log Actions")
        log_actions_layout = QVBoxLayout()

        # Clear Logs Button
        self.clear_log_button = QPushButton("🧹 Clear Logs")
        self.clear_log_button.clicked.connect(self.clear_logs)
        log_actions_layout.addWidget(self.clear_log_button)

        log_actions_box.setLayout(log_actions_layout)
        layout.addWidget(log_actions_box)

        ### 🔹 Add Spacing
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)


    def upload_resume(self):
        """Opens a file dialog to select a resume PDF and updates the GrowHireBot with the new path."""
        resume_path, _ = QFileDialog.getOpenFileName(self, "Select Resume", "", "PDF Files (*.pdf)")

        if resume_path:
            logger.info(f"📄 Selected resume: {resume_path}")
            
            # Update environment variable if needed
            os.environ["RESUME_PATH"] = resume_path
            
            # Use the setter method to update the GrowHireBot instance
            self.growhire_bot.set_resume_path(resume_path)
            
     

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
        """Starts looping through job listings, extracting job descriptions, and evaluating matches."""
        logger.info("🔄 Starting job match analysis for all jobs...")

        # Get the number of pages
        num_pages = int(self.pages_dropdown.currentText())  

        


        # Extract job descriptions
        job_descriptions = self.growhire_bot.extract_job_descriptions(num_pages=num_pages)

        if not job_descriptions:
            logger.warning("⚠️ No job descriptions found. Exiting match analysis.")
            return []

        # Evaluate matches
        job_match_results = self.growhire_bot.evaluate_job_matches(job_descriptions)
       
        # Save match results
        self.growhire_bot.save_job_matches_to_db(job_match_results)

        logger.info("✅ Job match analysis completed for all jobs.")
        return job_match_results

    def clear_logs(self):
            """Clears the console output log."""
            self.console_output.clear()
            self.console_output.append("🧹 Logs cleared successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GrowHireGUI()
    window.show()
    sys.exit(app.exec())
