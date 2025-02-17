import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QPushButton, QTextEdit
)

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QEvent, QTimer
from db.job_storage import JobStorage  # Ensure this import path matches your project

logger = logging.getLogger(__name__)

class NoPropagateTextEdit(QTextEdit):
    def wheelEvent(self, event):
        # Get the vertical scrollbar
        scrollbar = self.verticalScrollBar()
        atTop = scrollbar.value() == scrollbar.minimum()
        atBottom = scrollbar.value() == scrollbar.maximum()

        # If scrolling up and at top, or scrolling down and at bottom, consume event.
        if event.angleDelta().y() > 0 and atTop:
            event.accept()
            return
        elif event.angleDelta().y() < 0 and atBottom:
            event.accept()
            return

        # Otherwise, process the event normally.
        super().wheelEvent(event)

class AllJobResultsPopup(QDialog):
    """Popup window that displays all JobDescription records from JobStorage."""

    def __init__(self, db_url=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 All Job Descriptions")
        self.resize(1400, 750)  # Initial window size that can be resized
        self.setMinimumSize(400, 300)  # Prevent too-small sizes

        # Set window flags to behave as a normal window with minimize/maximize/close buttons
        self.setWindowFlags(self.windowFlags() | Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # Initialize JobStorage. If db_url is None, JobStorage will use environment variable or default.
        self.job_storage = JobStorage(db_url=db_url)
        self.current_font_size = 12  # Default font size for text widgets
        self.expanded_rows = {}  # To track row expansion states, if needed

        self.initUI()

        # Detect window state changes (maximize/restore)
        self.installEventFilter(self)
        QTimer.singleShot(0, self.updateUI)

        # Load job descriptions from the database immediately
        self.refresh_results()


    def initUI(self):
        # Make the window larger by default
        self.resize(1800, 900)  # (width, height) in pixels
        layout = QVBoxLayout()

        # Table Setup
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Job Title", "Company", "Score", "Job URL", "Job Description", "ChatGPT Response"
        ])
        self.results_table.setWordWrap(True)
        self.results_table.verticalHeader().setDefaultSectionSize(70)
        self.results_table.setColumnWidth(0, 150)  # Job Title
        self.results_table.setColumnWidth(1, 150)  # Company
        self.results_table.setColumnWidth(2, 80)   # Score
        self.results_table.setColumnWidth(3, 150)  # Job URL
        self.results_table.setColumnWidth(4, 1)
        self.results_table.setColumnWidth(5, 1)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        font = QFont("Arial", 12)
        self.results_table.setFont(font)

        layout.addWidget(self.results_table)
        self.setLayout(layout)

    def updateUI(self):
        """Ensures UI updates happen after full initialization."""
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                self.update_row_heights(expanded=True)
            else:
                self.update_row_heights(expanded=False)
        return super().eventFilter(obj, event)

    def refresh_results(self):
        """Fetches all job description records and updates the table."""
        self.results_table.setRowCount(0)

        try:
            # Fetch all JobDescription records from the database.
            job_records = self.job_storage.get_all_job_descriptions()
            
            # Sort jobs by score (highest first); default to 0 if score is missing.
            sorted_jobs = sorted(job_records, key=lambda j: int(j.score or 0), reverse=True)

            for row_index, job in enumerate(sorted_jobs):
                self.results_table.insertRow(row_index)

                # Extract job details with default fallback
                job_title = job.job_title or "N/A"
                company_name = job.company_name or "N/A"
                score = str(job.score) if job.score is not None else "N/A"
                job_url = job.job_url or "N/A"
                job_description = job.job_description or "N/A"
                chat_gpt_response = job.chat_gpt_response or "No response available."

                # Format job description to add newlines before known headings.
                job_description = self.format_job_description(job_description)

                # Safely convert score to int
                try:
                    score_int = int(score)
                except (ValueError, TypeError):
                    score_int = 0

                # Set background color based on score
                if score_int >= 85:
                    color = QColor(144, 238, 144)
                elif score_int > 50:
                    color = QColor(255, 255, 153)
                else:
                    color = QColor(255, 102, 102)

                # Create table items for Job Title, Company, Score
                job_title_item = QTableWidgetItem(job_title)
                company_name_item = QTableWidgetItem(company_name)
                score_item = QTableWidgetItem(str(score_int))
                score_item.setBackground(color)

                # Create a button for job URL
                job_url_button = QPushButton("🔗 Open Job")
                job_url_button.setStyleSheet("color: blue; text-decoration: underline; background: transparent; border: none;")
                job_url_button.setCursor(Qt.PointingHandCursor)
                job_url_button.clicked.connect(lambda checked, url=job_url: self.open_job(url))

                # Create text edit widgets for job description and ChatGPT response
                job_description_widget = NoPropagateTextEdit()
                job_description_widget.setPlainText(job_description)
                chat_gpt_widget = NoPropagateTextEdit()
                chat_gpt_widget.setPlainText(chat_gpt_response)
                for widget in [job_description_widget, chat_gpt_widget]:
                    widget.setReadOnly(True)
                    widget.setFont(QFont("Arial", self.current_font_size))
                    widget.setStyleSheet("border: none; background: transparent;")

                # Determine a desired height based on job description length
                content_length = len(job_description)
                desired_height = min(500, max(120, content_length * 2))
                job_description_widget.setFixedHeight(desired_height)
                chat_gpt_widget.setFixedHeight(desired_height)

                # Insert items into the table
                self.results_table.setItem(row_index, 0, job_title_item)
                self.results_table.setItem(row_index, 1, company_name_item)
                self.results_table.setItem(row_index, 2, score_item)
                self.results_table.setCellWidget(row_index, 3, job_url_button)
                self.results_table.setCellWidget(row_index, 4, job_description_widget)
                self.results_table.setCellWidget(row_index, 5, chat_gpt_widget)

                # Set row height (with some extra padding)
                self.results_table.setRowHeight(row_index, desired_height + 20)
                self.expanded_rows[row_index] = False

            logger.info(f"✅ Loaded {len(sorted_jobs)} job descriptions.")
        except Exception as e:
            logger.error(f"❌ Error loading job descriptions: {e}")

    def open_job(self, url):
        """Placeholder for opening a job URL."""
        print("open_job called with:", url)
        # Here you can integrate Selenium or other methods to open the job URL.

    def format_job_description(self, text):
        """Inserts newlines before known headings to break text into paragraphs."""
        headings = [
            "About the job",
            "Who we are",
            "About The Role",
            "What you will be doing",
            "Your Skills And Experience"
        ]
        for heading in headings:
            text = text.replace(heading, "\n\n" + heading)
        return text.strip()

    def update_row_heights(self, expanded: bool):
        """Expands or collapses row heights based on the 'expanded' flag."""
        for row_index in range(self.results_table.rowCount()):
            if expanded:
                text_edit = self.results_table.cellWidget(row_index, 4)
                if text_edit:
                    content_length = len(text_edit.toPlainText())
                    new_height = min(500, max(120, content_length * 2))
                    self.results_table.setRowHeight(row_index, new_height)
                else:
                    self.results_table.setRowHeight(row_index, 120)
            else:
                self.results_table.setRowHeight(row_index, 40)
