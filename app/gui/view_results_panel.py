from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton
import logging
from app.gui.all_job_results_popup import AllJobResultsPopup  # Adjust import as needed
from app.gui.all_linkedin_posts import AllLinkedInPostsPopup  # Adjust import as needed

logger = logging.getLogger(__name__)

class ViewResultsPanel(QGroupBox):
    """Panel with two buttons to view all job descriptions and all LinkedIn posts."""

    def __init__(self, growhire_bot):
        super().__init__("📋 View Results")
        self.growhire_bot = growhire_bot
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Button to view all job descriptions
        self.view_jobs_button = QPushButton("View All Job Descriptions")
        self.view_jobs_button.clicked.connect(self.view_all_jobs)
        layout.addWidget(self.view_jobs_button)

        # Button to view all LinkedIn posts
        self.view_linkedin_button = QPushButton("View All LinkedIn Posts")
        self.view_linkedin_button.clicked.connect(self.view_all_linkedin)
        layout.addWidget(self.view_linkedin_button)

        self.setLayout(layout)

    def view_all_jobs(self):
        """Opens a popup that displays all job descriptions from the database."""
        try:
            popup = AllJobResultsPopup()
            popup.exec_()  # Show the popup as a modal dialog
        except Exception as e:
            logger.error(f"Error opening job descriptions popup: {e}")

    def view_all_linkedin(self):
        """Opens a popup that displays all LinkedIn posts from the database."""
        try:
            popup = AllLinkedInPostsPopup()
            popup.exec_()  # Show the popup as a modal dialog
        except Exception as e:
            logger.error(f"Error opening LinkedIn posts popup: {e}")
