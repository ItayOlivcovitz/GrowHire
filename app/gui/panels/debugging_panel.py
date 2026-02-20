"""Debugging panel: LinkedIn job URL input and Apply test button."""
import os
import logging

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from app.gui.workers.apply_test_worker import ApplyTestWorker

logger = logging.getLogger(__name__)


def _default_api_url() -> str:
    return os.getenv("DEBUG_APPLY_API_URL", "").strip()


class DebuggingPanel(QGroupBox):
    """Panel with job URL input and Apply test to capture popup and POST to API."""

    def __init__(self, growhire_bot):
        super().__init__("Debugging")
        self.growhire_bot = growhire_bot
        self._thread = None
        self._worker = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(QLabel("LinkedIn job URL"))
        self.job_url_edit = QLineEdit()
        self.job_url_edit.setPlaceholderText(
            "Paste job link or leave empty to use current page"
        )
        layout.addWidget(self.job_url_edit)

        layout.addWidget(QLabel("API URL (optional override)"))
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText(
            "Leave empty to use DEBUG_APPLY_API_URL from .env"
        )
        layout.addWidget(self.api_url_edit)

        self.apply_test_button = QPushButton("Apply test")
        self.apply_test_button.clicked.connect(self._on_apply_test)
        layout.addWidget(self.apply_test_button)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _api_url(self) -> str:
        text = self.api_url_edit.text().strip()
        return text if text else _default_api_url()

    def _on_apply_test(self):
        driver = getattr(
            getattr(self.growhire_bot, "linkedin_navigator", None),
            "driver",
            None,
        )
        if not driver:
            self.status_label.setText("Error: No browser driver. Please log in first.")
            return

        if self._thread is not None and self._thread.isRunning():
            self.status_label.setText("Already running…")
            return

        self.status_label.setText("Running…")
        self.apply_test_button.setEnabled(False)

        self._thread = QThread()
        self._worker = ApplyTestWorker(
            self.growhire_bot,
            job_url=self.job_url_edit.text().strip() or None,
            api_url=self._api_url() or None,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error.connect(self._on_error)

        def reenable():
            self.apply_test_button.setEnabled(True)

        self._thread.finished.connect(reenable)
        self._thread.start()

    def _on_result(self, message: str):
        self.status_label.setText(message)

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")
