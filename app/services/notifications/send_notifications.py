import json
import logging
import os
import datetime
from PySide6.QtCore import QObject, QTimer
import requests
from app.services.jobScraper.job_scraper import JobScraper

logger = logging.getLogger(__name__)

class SendNotifications(QObject):
    """
    SendNotifications: A scheduled notifier that loads multiple scraping plans
    from a JSON configuration file and executes them on schedule.
    
    Each plan uses a JobScraper to extract job descriptions and sends a JSON payload
    to the API endpoint specified via the environment variable 'notifications_api'
    at specific times: 10:00, 12:00, and 18:00.
    """
    def __init__(self, job_scraper, linkedin_navigator, parent=None):
        """
        Initialize the SendNotifications instance.
        The configuration file path is taken from the environment variable
        NOTIFICATIONS_CONFIG_FILE, with a default of "plans.json".
        """
        super().__init__(parent)
        self.config_file = os.environ.get("NOTIFICATIONS_CONFIG_FILE", "plans.json")
        self.job_scraper = job_scraper
        self.linkedin_navigator = linkedin_navigator
        self.plans = self.load_config()
        self.timer = None  # This will hold the QTimer for scheduling

    def load_config(self):
        """Load and return the scraping plans from the JSON configuration file."""
        with open(self.config_file, "r") as f:
            return json.load(f)

    def get_next_run_interval(self):
        """
        Calculate the interval (in milliseconds) until the next scheduled run time.
        Scheduled times are fixed at 10:00, 12:00, and 18:00.
        """
        now = datetime.datetime.now()
        # Define today's scheduled times.
        scheduled_times = [
            now.replace(hour=10, minute=0, second=0, microsecond=0),
            now.replace(hour=12, minute=0, second=0, microsecond=0),
            now.replace(hour=18, minute=0, second=0, microsecond=0)
        ]
        # Get only the times later than now.
        future_times = [t for t in scheduled_times if t > now]
        if future_times:
            next_run = min(future_times)
        else:
            # If no time left today, schedule for tomorrow's first run (10:00).
            next_run = scheduled_times[0] + datetime.timedelta(days=1)
        interval_ms = (next_run - now).total_seconds() * 1000
        return interval_ms

    def start(self):
        """
        Execute all plans immediately, then schedule the next run
        at one of the fixed times (10:00, 12:00, 18:00).
        """
        # Execute all plans immediately.
        for plan in self.plans:
            logger.info(f"🚀 Immediately executing plan: {plan.get('job_title')} in {plan.get('location')}")
            self.execute_plan(plan)
        
        # Schedule next execution.
        self.schedule_next_run()

    def schedule_next_run(self):
        """Schedule a single-shot QTimer to run all plans at the next target time."""
        interval_ms = self.get_next_run_interval()
        minutes = interval_ms / 60000
        logger.info(f"⏳ Scheduling next execution in {minutes:.2f} minutes.")
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.run_all_plans)
        self.timer.start(interval_ms)

    def run_all_plans(self):
        """Execute all plans and then re-schedule the next run."""
        for plan in self.plans:
            logger.info(f"🚀 Executing scheduled plan: {plan.get('job_title')} in {plan.get('location')}")
            self.execute_plan(plan)
        self.schedule_next_run()

    def stop(self):
        """Stop the scheduled notifications."""
        if self.timer and self.timer.isActive():
            logger.info("Stopping scheduled notifications.")
            self.timer.stop()

    def execute_plan(self, plan):
        """
        Executes a single plan:
        - Searches LinkedIn for jobs.
        - Extracts jobs.
        - Filters jobs posted within 5 hours.
        - Evaluates them using ChatGPT.
        - Keeps only matches with score >= 80%.
        - Sends results to notifications API.
        """
        job_title = plan.get("job_title")
        location = plan.get("location")
        filters = plan.get("filters", {})

        api_url = os.environ.get("notifications_api", "http://example.com/api")
        logger.info(f"🚀 Executing plan: {job_title} in {location} with filters {filters}")

        self.linkedin_navigator.search_jobs(job_title, location, filters)

        job_results = self.job_scraper.extract_job_descriptions(num_pages=2)
        if not job_results:
            logger.warning("⚠️ No job results found. Exiting search.")
            return

        logger.info(f"📝 Found {len(job_results)} job listings in total.")

        # Filter by posting time.
        recent_jobs = [
            job for job in job_results
            if self.job_scraper.is_posted_within_5_hours(job.get("posting_time_text"))
        ]
        logger.info(f"⏰ {len(recent_jobs)} jobs posted within the last 5 hours.")

        if not recent_jobs:
            logger.warning("⚠️ No recent jobs posted within the last 5 hours.")
            return

        # Evaluate job matches in parallel.
        evaluated_job_matches = self.job_scraper.evaluate_job_matches(recent_jobs)

        # Filter for high-score jobs (score >= 80%).
        evaluated_job_matches = [
            result for result in evaluated_job_matches
            if result and result.get("score") is not None and result["score"] >= 0
        ]

        if not evaluated_job_matches:
            logger.warning("⚠️ No high-match job results found (score >= 80%).")
            return

        # Prepare data to send.
        data = {
            "message": f"Scheduled update for {job_title}",
            "status": "active",
            "job_descriptions": evaluated_job_matches
        }
      
        try:
            response = requests.post(api_url, json=data)
            response.raise_for_status()
            logger.info(f"✅ Successfully sent JSON payload for plan '{job_title}' with {len(evaluated_job_matches)} jobs.")
        except requests.RequestException as e:
            logger.error(f"❌ Failed to send JSON payload for plan '{job_title}': {e}")
