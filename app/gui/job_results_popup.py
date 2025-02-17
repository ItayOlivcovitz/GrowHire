
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QPushButton, QTextEdit
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QEvent, QTimer

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

class JobResultsPopup(QDialog):
    """Popup Window for Job Search Results with synchronized sizes and clickable job URL."""

    def __init__(self, growhire_bot, parent=None):

        self.growhire_bot = growhire_bot


        super().__init__(parent)
        self.setWindowTitle("📋 Job Search Results")
        self.setGeometry(200, 100, 1400, 750)  # Popup size
        self.setMinimumSize(400, 300)  # Prevent negative sizes
        
        # Make the dialog act like a normal window:
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.Window)
        
        self.expanded_rows = {}  # Store row expansion states (if needed later)
        self.current_font_size = 12  # Default font size
        self.initUI()

        # Detect window state changes (maximize/restore)
        self.installEventFilter(self)

        # Ensure UI updates happen after full initialization
        QTimer.singleShot(0, self.updateUI)

    def initUI(self):
        # Make the window bigger by default
        self.resize(1800, 900)  # (width, height) in pixels

        layout = QVBoxLayout()

        # Table Setup
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Job Title", "Company", "Score", "Job URL", "Job Description", "ChatGPT Response"
        ])
        self.results_table.setWordWrap(True)
        # Removed cellClicked connection

        # 1) Increase default row height
        self.results_table.verticalHeader().setDefaultSectionSize(70)

        # 2) Fixed widths for columns 0,1,2,3
        self.results_table.setColumnWidth(0, 150)  # Job Title
        self.results_table.setColumnWidth(1, 150)  # Company
        self.results_table.setColumnWidth(2, 80)   # Score
        self.results_table.setColumnWidth(3, 150)  # Job URL

        # 3) Set the same initial width for columns 4 & 5, then stretch them
        self.results_table.setColumnWidth(4, 1)
        self.results_table.setColumnWidth(5, 1)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        # 4) Increase the font size used by the table
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

    def update_results(self, job_results):
        """Updates the job search results in the table with synchronized sizes."""
        self.results_table.setRowCount(0)

        # Sort jobs by score (highest first); ensure score defaults to 0 if missing or None.
        sorted_results = sorted(job_results, key=lambda x: int(x.get("score") or 0), reverse=True)

        for row_index, job in enumerate(sorted_results):
            self.results_table.insertRow(row_index)

            # Extract job details
            job_title = job.get("job_title", "N/A")
            company_name = job.get("company_name", "N/A")
            score = job.get("score", "N/A")
            job_url = job.get("job_url", "N/A")
            job_description = job.get("job_description", "N/A")
            chat_gpt_response = job.get("chat_gpt_response", "No response available.")

            # Format the job description to insert newlines before headings
            job_description = self.format_job_description(job_description)

            # Convert score to int safely
            try:
                score_int = int(score)
            except (ValueError, TypeError):
                score_int = 0

            # Set color based on score
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

            # Compute a desired height based on the job description's text length
            content_length = len(job_description)
            desired_height = min(500, max(120, content_length * 2))

            # Set both widgets to the same fixed height
            job_description_widget.setFixedHeight(desired_height)
            chat_gpt_widget.setFixedHeight(desired_height)

            # Insert items into table
            self.results_table.setItem(row_index, 0, job_title_item)
            self.results_table.setItem(row_index, 1, company_name_item)
            self.results_table.setItem(row_index, 2, score_item)
            self.results_table.setCellWidget(row_index, 3, job_url_button)
            self.results_table.setCellWidget(row_index, 4, job_description_widget)
            self.results_table.setCellWidget(row_index, 5, chat_gpt_widget)

            # Set the row height to match the widget heights (with extra padding if needed)
            self.results_table.setRowHeight(row_index, desired_height + 20)
            self.expanded_rows[row_index] = False  # Tracking expansion state if needed later

    def open_job(self, url):
        print("open_job called with:", url)  # Debug print

        # Validate URL
        if not url or not url.startswith("http"):
            print("Invalid URL provided:", url)
            return

        try:
            # Reuse the existing Selenium driver from the logged-in connection.
            driver = self.growhire_bot.linkedin_navigator.driver

            if driver is None:
                print("Selenium driver not available. Please complete the login process first.")
                return

            print("Using existing Selenium connection to open URL in a new window...")

            # Open a new window (or tab)
            driver.execute_script("window.open('');")
            # Switch focus to the new window
            driver.switch_to.window(driver.window_handles[-1])
            # Load the desired URL
            driver.get(url)
        except Exception as e:
            print("Error opening URL with existing Selenium driver:", e)



    def format_job_description(self, text):
        """Inserts newlines before known headings to separate the text into paragraphs."""
        headings = [
            "About the job",
            "Who we are",
            "About The Role",
            "What you will be doing",
            "Your Skills And Experience"
        ]
        for heading in headings:
            # Insert two newlines before each heading occurrence.
            text = text.replace(heading, "\n\n" + heading)
        return text.strip()

    def update_row_heights(self, expanded: bool):
        """
        Expand or collapse row heights for all rows, 
        depending on the 'expanded' boolean.
        """
        for row_index in range(self.results_table.rowCount()):
            if expanded:
                text_edit = self.results_table.cellWidget(row_index, 4)  # Job Description
                if text_edit:
                    content_length = len(text_edit.toPlainText())
                    new_height = min(500, max(120, content_length * 2))
                    self.results_table.setRowHeight(row_index, new_height)
                else:
                    self.results_table.setRowHeight(row_index, 120)
            else:
                self.results_table.setRowHeight(row_index, 40)
