"""Background worker for Apply test: capture apply popup and POST to API."""
import logging
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal

from app.services.applyPopupCapture.apply_popup_capture import capture_apply_popup

logger = logging.getLogger(__name__)

POST_TIMEOUT = 30


class ApplyTestWorker(QObject):
    """Runs apply-and-capture in a QThread; optionally POSTs JSON to API."""

    finished = Signal()
    result_ready = Signal(str)  # success message or response summary
    error = Signal(str)

    def __init__(
        self,
        growhire_bot,
        job_url: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.job_url = (job_url or "").strip() or None
        self.api_url = (api_url or "").strip() or None

    def run(self):
        """Navigate (if URL), click Apply, capture modal, POST to API if configured."""
        try:
            driver = getattr(
                getattr(self.growhire_bot, "linkedin_navigator", None),
                "driver",
                None,
            )
            if not driver:
                self.error.emit("No browser driver. Please log in first.")
                return

            payload = capture_apply_popup(driver, job_url=self.job_url)

            if payload.get("error"):
                self.error.emit(payload["error"])
                return

            if not self.api_url:
                logger.warning("DEBUG_APPLY_API_URL not set; skipping POST.")
                self.result_ready.emit("Captured (API URL not set)")
                return

            r = requests.post(
                self.api_url,
                json=payload,
                timeout=POST_TIMEOUT,
            )
            r.raise_for_status()
            self.result_ready.emit(f"Sent ({r.status_code})")
        except requests.RequestException as e:
            msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    msg = f"{e.response.status_code}: {e.response.text[:200]}"
                except Exception:
                    pass
            logger.exception("Apply test POST failed")
            self.error.emit(msg)
        except Exception as e:
            logger.exception("Apply test failed")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
