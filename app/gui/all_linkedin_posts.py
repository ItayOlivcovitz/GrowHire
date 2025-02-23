from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QLabel, QPushButton, QWidget, QScrollArea
)
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import Qt, QEvent, QTimer, QUrl
from datetime import datetime
from urllib.parse import urlparse
import json
import logging
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 All LinkedIn Posts")
        self.resize(1400, 750)  # Initial window size that can be resized
        self.setMinimumSize(400, 300)
        
        # Set window flags to allow minimize, maximize, and close buttons
        self.setWindowFlags(
            self.windowFlags() | Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )
        
        self.job_storage = JobStorage()
        self.current_font_size = 12
        self.expanded_rows = {}
        
        self.initUI()
        self.installEventFilter(self)
        QTimer.singleShot(0, self.updateUI)
        self.refresh_results()

    def initUI(self):
        self.resize(1800, 900)
        layout = QVBoxLayout()

        # Setup table with 6 columns (Emails column removed)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Post ID", "Publisher URL", "Publish Date", "Post Text", "Links", "Keywords"
        ])
        self.results_table.setWordWrap(True)
        self.results_table.verticalHeader().setDefaultSectionSize(70)
        self.results_table.setColumnWidth(0, 150)  # Post ID
        self.results_table.setColumnWidth(1, 250)  # Publisher URL
        self.results_table.setColumnWidth(2, 150)  # Publish Date
        self.results_table.setColumnWidth(3, 300)  # Post Text
        self.results_table.setColumnWidth(4, 200)  # Links
        self.results_table.setColumnWidth(5, 200)  # Keywords

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

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
            # Sort posts by publish_date descending.
            sorted_posts = sorted(
                posts,
                key=lambda p: p.publish_date if isinstance(p.publish_date, datetime)
                                else datetime.min,
                reverse=True
            )

            for row_index, post in enumerate(sorted_posts):
                self.results_table.insertRow(row_index)

                # Extract details with fallbacks.
                post_id = post.post_id or "N/A"
                publisher_url = post.publisher_url or "N/A"

                # Convert publish_date if it's a string.
                dt = None
                if post.publish_date:
                    if isinstance(post.publish_date, str):
                        try:
                            dt = datetime.strptime(post.publish_date, "%Y-%m-%d %H:%M:%S")
                        except Exception as e:
                            logger.error(f"Error parsing publish_date '{post.publish_date}': {e}")
                            dt = None
                    else:
                        dt = post.publish_date
                publish_date = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"

                post_text = post.post_text or "N/A"

                # --- Process Links ---
                links_widget = QLabel("N/A")
                if post.links:
                    # Determine links_list from various formats.
                    if isinstance(post.links, list):
                        links_list = post.links
                    elif isinstance(post.links, str) and post.links.startswith("[") and post.links.endswith("]"):
                        try:
                            links_list = json.loads(post.links)
                        except Exception:
                            links_list = [post.links]
                    else:
                        links_list = [post.links]

                    valid_links = []
                    for link in links_list:
                        link = link.strip(" []\"'")
                        if link and link != "N/A":
                            valid_links.append(link)

                    # Build clickable buttons for each link.
                    if valid_links:
                        # If only one link, create a single button.
                        if len(valid_links) == 1:
                            link = valid_links[0]
                            parsed = urlparse(link)
                            domain = parsed.netloc.lower() if parsed.netloc else link
                            if "linkedin" in domain:
                                button_text = "LinkedIn"
                            else:
                                if domain.startswith("www."):
                                    domain = domain[4:]
                                button_text = domain.capitalize()
                            btn = QPushButton(button_text)
                            btn.setStyleSheet("color: blue; text-decoration: underline; background: transparent; border: none;")
                            btn.setCursor(Qt.PointingHandCursor)
                            btn.clicked.connect(lambda checked, url=link: self.open_link(url))
                            links_widget = btn
                        else:
                            # Create a container widget to hold all buttons.
                            container = QWidget()
                            layout_btn = QVBoxLayout()
                            layout_btn.setContentsMargins(0, 0, 0, 0)
                            for i, link in enumerate(valid_links):
                                parsed = urlparse(link)
                                domain = parsed.netloc.lower() if parsed.netloc else link
                                if "linkedin" in domain:
                                    base_text = "LinkedIn"
                                else:
                                    if domain.startswith("www."):
                                        domain = domain[4:]
                                    base_text = domain.capitalize()
                                btn = QPushButton(f"{base_text} {i+1}")
                                btn.setStyleSheet("color: blue; text-decoration: underline; background: transparent; border: none;")
                                btn.setCursor(Qt.PointingHandCursor)
                                btn.clicked.connect(lambda checked, url=link: self.open_link(url))
                                layout_btn.addWidget(btn)
                            container.setLayout(layout_btn)
                            # Wrap the container in a scroll area to add a scrollbar.
                            scroll_area = QScrollArea()
                            scroll_area.setWidget(container)
                            scroll_area.setWidgetResizable(True)
                            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                            scroll_area.setMinimumHeight(50)  # Adjust the height as needed
                            links_widget = scroll_area

                # Get the matched keywords from the DB field 'keyword_found'
                keywords = post.keyword_found if hasattr(post, 'keyword_found') and post.keyword_found else "N/A"

                # Create table items for columns that don't require clickable links.
                post_id_item = QTableWidgetItem(post_id)
                publisher_url_item = QTableWidgetItem(publisher_url)
                publish_date_item = QTableWidgetItem(publish_date)

                # Use a QTextEdit for potentially long post text.
                post_text_widget = NoPropagateTextEdit()
                post_text_widget.setPlainText(post_text)
                post_text_widget.setReadOnly(True)
                post_text_widget.setFont(QFont("Arial", self.current_font_size))
                post_text_widget.setStyleSheet("border: none; background: transparent;")

                keywords_item = QTableWidgetItem(keywords)

                # Insert items into the table.
                # Column mapping: 0: Post ID, 1: Publisher URL, 2: Publish Date, 3: Post Text, 4: Links, 5: Keywords
                self.results_table.setItem(row_index, 0, post_id_item)
                self.results_table.setItem(row_index, 1, publisher_url_item)
                self.results_table.setItem(row_index, 2, publish_date_item)
                self.results_table.setCellWidget(row_index, 3, post_text_widget)
                self.results_table.setCellWidget(row_index, 4, links_widget)
                self.results_table.setItem(row_index, 5, keywords_item)

                # Set row height based on post text length.
                content_length = len(post_text)
                desired_height = min(500, max(120, content_length * 2))
                self.results_table.setRowHeight(row_index, desired_height + 20)
                self.expanded_rows[row_index] = False

            logger.info(f"✅ Loaded {len(sorted_posts)} LinkedIn posts.")
        except Exception as e:
            logger.error(f"❌ Error loading LinkedIn posts: {e}")

    def open_link(self, url):
        QDesktopServices.openUrl(QUrl(url))

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
