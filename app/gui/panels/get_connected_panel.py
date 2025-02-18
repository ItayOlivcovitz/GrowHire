from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PySide6.QtCore import QThread
import logging
from app.services.getConnected.get_connected import GetConnectedService  # For reference; the service is already in growhire_bot
from app.gui.workers.people_search_worker import PeopleSearchWorker  # Ensure correct import path

logger = logging.getLogger(__name__)

class GetConnectedPanel(QGroupBox):
    """
    Panel to get connected with people.
    
    This panel includes:
      - A text box to search for team leaders or other people.
      - A drop-down to select the number of pages (1–10, default: 1).
      - A 'Find & Connect' button.
      - A 'Pause Bot' button.
      - A search query field.
      - A status label.
    """

    def __init__(self, growhire_bot):
        """
        Expects 'growhire_bot' to be an instance of GrowHireBot,
        which has a 'get_connected' attribute (an instance of GetConnectedService).
        """
        super().__init__("🤝 Get Connected")
        self.growhire_bot = growhire_bot
        self.paused = False  # Initial pause state
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Search field for team leaders or other people
        self.people_search_field = QLineEdit()
        self.people_search_field.setPlaceholderText("Search for team leaders or people...")
        layout.addWidget(QLabel("🔎 Search People:"))
        layout.addWidget(self.people_search_field)

        # Drop-down for Number of Pages (1-10, default: 1)
        self.pages_dropdown = QComboBox()
        self.pages_dropdown.addItems([str(i) for i in range(1, 11)])
        self.pages_dropdown.setCurrentIndex(0)
        layout.addWidget(QLabel("Select Number of Pages:"))
        layout.addWidget(self.pages_dropdown)

        # Find & Connect Button
        self.search_button = QPushButton("Find & Connect")
        self.search_button.clicked.connect(self.on_search_clicked)
        layout.addWidget(self.search_button)

        # Pause/Resume Button
        self.pause_button = QPushButton("Pause Bot")
        self.pause_button.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_button)

        # Search Query Field
        self.query_field = QLineEdit()
        self.query_field.setPlaceholderText("Enter Search Query")
        layout.addWidget(QLabel("Search Query:"))
        layout.addWidget(self.query_field)

        # Status Label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
    def on_search_clicked(self):
        """Start LinkedIn people search and connection attempts in a separate thread."""
        # Check if the driver is available via the get_connected service.
        if not self.growhire_bot.get_connected.driver:
            QMessageBox.warning(self, "Warning", "You must log in to LinkedIn first!")
            return

        try:
            num_pages = int(self.pages_dropdown.currentText())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please select a valid number of pages.")
            return

        # Use query_field text; if empty, fallback to people_search_field text.
        search_query = self.query_field.text().strip() or self.people_search_field.text().strip()
        if not search_query:
            QMessageBox.warning(self, "Missing Query", "You must set a search query before searching!")
            return

        self.status_label.setText("Status: Searching and Connecting...")
        self.log_message(f"🔍 [INFO] Searching and connecting for '{search_query}' on {num_pages} pages.")

        # Ensure LinkedIn is open and logged in.
        if not self.growhire_bot.get_connected.driver:
            self.growhire_bot.open_linkedin()

        # Create the worker and thread.
        self.search_thread = QThread()  # Make sure to store a reference to avoid garbage collection.
        self.worker = PeopleSearchWorker(self.growhire_bot.get_connected, search_query, num_pages)
        self.worker.moveToThread(self.search_thread)

        # Connect signals and slots.
        self.search_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.search_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)

        # Optionally, handle any errors or progress signals.
        # self.worker.error.connect(self.handle_error)
        # self.worker.progress.connect(self.update_progress)

        self.search_thread.start()

    def handle_search_results(self, results):
        """Handles results returned from the people search worker."""
        self.log_message(f"🔍 Search completed. Found {len(results)} profiles.")
        # Optionally, update the UI with results here.

    def toggle_pause(self):
        """Toggle Pause/Resume for the bot."""
        self.paused = not self.paused
        self.pause_button.setText("Resume Bot" if self.paused else "Pause Bot")
        self.log_message("[INFO] 🛑 Bot is paused." if self.paused else "[INFO] ▶ Bot is resuming.")

    def log_message(self, message):
        """Log a message and update the status label."""
        logger.info(message)
        self.status_label.setText(message)
