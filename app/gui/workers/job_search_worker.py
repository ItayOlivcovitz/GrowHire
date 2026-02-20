from PySide6.QtCore import QObject, Signal
import logging

logger = logging.getLogger(__name__)

class JobSearchWorker(QObject):
    """Worker class to handle job searching in a separate thread."""
    
    finished = Signal()  # ✅ Signals when processing is done
    results_ready = Signal(list)  # ✅ Sends job search results to the UI

    def __init__(self, growhire_bot, job_title, location, filters=None, num_pages=1):
        super().__init__()
        self.growhire_bot = growhire_bot
        self.job_title = job_title
        self.location = location
        self.filters = filters if filters else {}
        self.num_pages = num_pages  # ✅ Store the number of pages


    def run(self):
        """Runs the job search process in the background."""
        try:
            logger.info(f"🔍 Searching for jobs: {self.job_title} in {self.location} with filters: {self.filters}")

            self.growhire_bot.search_jobs(self.job_title, self.location, self.filters)
           
            job_results = self.growhire_bot.extract_job_descriptions(num_pages=self.num_pages)
            
            if not job_results:
                logger.warning("⚠️ No job results found. Exiting search.")
                self.results_ready.emit([])  # ✅ Emit empty results if no jobs are found
                return
            
            logger.info(f"✅ Found {len(job_results)} job listings.")

            # ✅ Evaluate job matches
            evaluated_job_matches = self.growhire_bot.evaluate_job_matches(job_results)

            if not evaluated_job_matches:
                logger.warning("⚠️ No matching job results found.")
                self.results_ready.emit([])  # ✅ Emit empty results if no matches
                return

            #Save job matches to the database
            self.growhire_bot.save_job_matches_to_db(evaluated_job_matches)

            # ✅ Sort results by score (highest first)
            def extract_score(job):
                """Safely extract and convert the job score to an integer."""
                try:
                    score = job.get("score", 0)
                    return int(score) if str(score).isdigit() else 0
                except ValueError:
                    return 0

            sorted_results = sorted(evaluated_job_matches, key=extract_score, reverse=True)

            logger.info(f"✅ Sending {len(sorted_results)} sorted job matches to the UI.")
            self.results_ready.emit(sorted_results)  # ✅ Emit sorted results to UI

        except Exception as e:
            logger.error(f"Error during job search: {e}", exc_info=True)
            # Always emit so the UI can show the popup (e.g. empty or error state)
            self.results_ready.emit([])
        finally:
            self.finished.emit()
