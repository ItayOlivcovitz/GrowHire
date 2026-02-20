"""
Capture LinkedIn job apply popup/modal content via Selenium.
Selectors may need updating if LinkedIn changes their DOM.
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

# Timeouts (seconds)
NAVIGATE_WAIT = 5
APPLY_BUTTON_WAIT = 10
MODAL_WAIT = 10

# LinkedIn apply button selectors (try in order; update if DOM changes)
APPLY_BUTTON_SELECTORS = [
    (By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_apply']"),
    (By.XPATH, "//button[contains(., 'Easy Apply')]"),
    (By.XPATH, "//button[contains(., 'Apply')]"),
    (By.CSS_SELECTOR, ".jobs-apply-button"),
    (By.CSS_SELECTOR, "button.jobs-apply-button--top-card"),
]

# Apply modal/panel container selectors
MODAL_SELECTORS = [
    (By.CSS_SELECTOR, ".jobs-easy-apply-content"),
    (By.CSS_SELECTOR, "[data-test-modal]"),
    (By.CSS_SELECTOR, ".jobs-easy-apply-form-section"),
    (By.XPATH, "//div[contains(@class, 'jobs-easy-apply')]"),
]


def capture_apply_popup(
    driver: WebDriver,
    job_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Navigate to job (if URL given), click Easy Apply/Apply, wait for modal, extract content.
    Returns a dict suitable for JSON serialization and API POST.
    """
    payload: Dict[str, Any] = {
        "job_url": job_url or (driver.current_url if driver else ""),
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "popup_text": "",
        "fields": [],
    }

    if not driver:
        logger.error("No driver provided")
        return payload

    try:
        if job_url and job_url.strip():
            driver.get(job_url.strip())
            time.sleep(2)
            try:
                WebDriverWait(driver, NAVIGATE_WAIT).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".jobs-details__main-content")
                    )
                )
            except TimeoutException:
                logger.warning("Job details did not load in time; continuing anyway.")

        payload["job_url"] = driver.current_url

        # Find and click Apply / Easy Apply
        apply_clicked = False
        for by, selector in APPLY_BUTTON_SELECTORS:
            try:
                btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                btn.click()
                apply_clicked = True
                logger.info("Clicked apply button with selector: %s", selector)
                break
            except (TimeoutException, Exception):
                continue

        if not apply_clicked:
            logger.warning("Could not find or click Easy Apply / Apply button")
            payload["error"] = "Apply button not found or not clickable"
            return payload

        time.sleep(2)

        # Wait for modal and get container element
        modal_el = None
        for by, selector in MODAL_SELECTORS:
            try:
                modal_el = WebDriverWait(driver, MODAL_WAIT).until(
                    EC.presence_of_element_located((by, selector))
                )
                if modal_el and modal_el.is_displayed():
                    break
            except TimeoutException:
                continue

        if not modal_el or not modal_el.is_displayed():
            logger.warning("Apply modal did not appear or could not be located")
            payload["error"] = "Apply modal not found"
            return payload

        # Extract visible text from modal
        popup_text = driver.execute_script(
            "return arguments[0].innerText || arguments[0].textContent || '';",
            modal_el,
        )
        if isinstance(popup_text, str):
            payload["popup_text"] = popup_text.strip()

        # Extract form fields (labels, types, names, placeholders)
        fields_script = """
        var container = arguments[0];
        var inputs = container.querySelectorAll('input, select, textarea');
        var result = [];
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var label = '';
            var id = el.id;
            if (id) {
                var labelEl = container.querySelector('label[for="' + id + '"]');
                if (labelEl) label = labelEl.innerText || labelEl.textContent || '';
            }
            result.push({
                tag: el.tagName.toLowerCase(),
                type: (el.type || '').toLowerCase(),
                name: el.name || '',
                id: id || '',
                placeholder: el.placeholder || '',
                label: label.trim()
            });
        }
        return result;
        """
        try:
            fields = driver.execute_script(fields_script, modal_el)
            if fields is not None:
                payload["fields"] = fields
        except Exception as e:
            logger.debug("Could not extract form fields: %s", e)

        return payload

    except Exception as e:
        logger.exception("Error capturing apply popup")
        payload["error"] = str(e)
        return payload
