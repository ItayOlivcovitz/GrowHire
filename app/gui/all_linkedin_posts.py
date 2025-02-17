import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QEvent, QTimer
from db.job_storage import JobStorage  # Adjust this import if needed

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

class AllLinkedInPostsPopup(QDialog):
    """Window that displays all LinkedIn posts from the database with keywords shown."""

    def __init__(self, db_url=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 All LinkedIn Posts")
        self.resize(1400, 750)  # Initial window size that can be resized
        self.setMinimumSize(400, 300)
        
        # Set window flags to allow minimize, maximize, and close buttons
        self.setWindowFlags(
            self.windowFlags() | Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )
        
        # Initialize JobStorage. If db_url is None, JobStorage will use environment variable/default.
        self.job_storage = JobStorage(db_url=db_url)
        self.current_font_size = 12
        self.expanded_rows = {}
        
        self.initUI()
        self.installEventFilter(self)
        QTimer.singleShot(0, self.updateUI)
        self.refresh_results()

    def initUI(self):
        self.resize(1800, 900)
        layout = QVBoxLayout()

        # Setup table with 7 columns for the key fields (added "Keywords")
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Post ID", "Publisher URL", "Publish Date", "Post Text", "Links", "Emails", "Keywords"
        ])
        self.results_table.setWordWrap(True)
        self.results_table.verticalHeader().setDefaultSectionSize(70)
        self.results_table.setColumnWidth(0, 150)  # Post ID
        self.results_table.setColumnWidth(1, 250)  # Publisher URL
        self.results_table.setColumnWidth(2, 150)  # Publish Date
        self.results_table.setColumnWidth(3, 300)  # Post Text
        self.results_table.setColumnWidth(4, 200)  # Links
        self.results_table.setColumnWidth(5, 200)  # Emails
        self.results_table.setColumnWidth(6, 200)  # Keywords

        header = self.results_table.horizontalHeader()
        # Stretch the Post Text, Links, Emails, and Keywords columns
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        font = QFont("Arial", 12)
        self.results_table.setFont(font)

        layout.addWidget(self.results_table)
        self.setLayout(layout)

    def updateUI(self):
        """Force a UI update after initialization."""
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                self.update_row_heights(expanded=True)
            else:
                self.update_row_heights(expanded=False)
        return super().eventFilter(obj, event)

    def refresh_results(self):
        """Fetch all LinkedIn posts and populate the table."""
        self.results_table.setRowCount(0)

        try:
            posts = self.job_storage.get_all_linkedin_posts()
            # Optionally, sort posts by publish_date descending
            sorted_posts = sorted(posts, key=lambda p: p.publish_date or "", reverse=True)

            for row_index, post in enumerate(sorted_posts):
                self.results_table.insertRow(row_index)

                # Extract details with fallbacks
                post_id = post.post_id or "N/A"
                publisher_url = post.publisher_url or "N/A"
                publish_date = post.publish_date.strftime("%Y-%m-%d %H:%M:%S") if post.publish_date else "N/A"
                post_text = post.post_text or "N/A"
                # For JSON fields, display them as a simple comma-separated string if possible.
                links = ", ".join(post.links) if isinstance(post.links, list) else str(post.links or "N/A")
                emails = ", ".join(post.emails) if isinstance(post.emails, list) else str(post.emails or "N/A")
                # Get the matched keywords from the DB field 'keyword_found'
                keywords = post.keyword_found if hasattr(post, 'keyword_found') and post.keyword_found else "N/A"

                # Create table items
                post_id_item = QTableWidgetItem(post_id)
                publisher_url_item = QTableWidgetItem(publisher_url)
                publish_date_item = QTableWidgetItem(publish_date)
                # Use a QTextEdit for potentially long post text
                post_text_widget = NoPropagateTextEdit()
                post_text_widget.setPlainText(post_text)
                for widget in [post_text_widget]:
                    widget.setReadOnly(True)
                    widget.setFont(QFont("Arial", self.current_font_size))
                    widget.setStyleSheet("border: none; background: transparent;")

                links_item = QTableWidgetItem(links)
                emails_item = QTableWidgetItem(emails)
                keywords_item = QTableWidgetItem(keywords)

                # Insert items into the table
                self.results_table.setItem(row_index, 0, post_id_item)
                self.results_table.setItem(row_index, 1, publisher_url_item)
                self.results_table.setItem(row_index, 2, publish_date_item)
                self.results_table.setCellWidget(row_index, 3, post_text_widget)
                self.results_table.setItem(row_index, 4, links_item)
                self.results_table.setItem(row_index, 5, emails_item)
                self.results_table.setItem(row_index, 6, keywords_item)

                # Set row height based on post text length
                content_length = len(post_text)
                desired_height = min(500, max(120, content_length * 2))
                self.results_table.setRowHeight(row_index, desired_height + 20)
                self.expanded_rows[row_index] = False

            logger.info(f"✅ Loaded {len(sorted_posts)} LinkedIn posts.")
        except Exception as e:
            logger.error(f"❌ Error loading LinkedIn posts: {e}")

    def update_row_heights(self, expanded: bool):
        """Expand or collapse row heights for all rows."""
        for row_index in range(self.results_table.rowCount()):
            if expanded:
                widget = self.results_table.cellWidget(row_index, 3)
                if widget:
                    content_length = len(widget.toPlainText())
                    new_height = min(500, max(120, content_length * 2))
                    self.results_table.setRowHeight(row_index, new_height)
                else:
                    self.results_table.setRowHeight(row_index, 120)
            else:
                self.results_table.setRowHeight(row_index, 40)
