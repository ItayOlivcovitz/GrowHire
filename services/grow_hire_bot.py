import logging
from services.linkedinNavigator.linkedin_navigator import LinkedInNavigator
from services.jobScraper.job_scraper import JobScraper  
from db.job_storage import JobStorage  
from services.pdfReader.pdf_reader import PDFReader
from services.feedScraper.feed_scraper import FeedScraper  

logger = logging.getLogger(__name__)

class GrowHireBot:
    """Main bot controller that orchestrates LinkedIn automation, job scraping, and AI analysis."""
    
    def __init__(self):
        """Initializes GrowHireBot with  required modules."""
        
        self.linkedin_navigator = LinkedInNavigator()  # Start LinkedInNavigator (Creates a WebDriver)
        self._driver = self.linkedin_navigator.driver  # 🔹 Extract WebDriver instance
        self._job_scraper = JobScraper(self._driver)  # 🔹 Pass the WebDriver to JobScraper
        self._job_storage = JobStorage()
        self._job_pdf_reader = PDFReader() 
        self.feed_scraper = FeedScraper(self._driver)  # ✅ Loads keywords from 'keywords.txt' if no list is provided
        
    
    def extract_job_descriptions(self, num_pages=1):
        """Triggers job descriptions extraction through JobScraper."""
        return self._job_scraper.extract_job_descriptions(num_pages=num_pages)
    
    
    def evaluate_job_matches(self, job_descriptions):
        """Triggers job matches evaluation through JobScraper."""
        return self._job_scraper.evaluate_job_matches(job_descriptions)
    
    
    def save_job_matches_to_db(self, job_match_results):
        """Saves job descriptions with AI analysis results to the database."""
        self._job_storage.save_job_matches_to_db(job_match_results)

    def save_job_posts_to_db(self, job_match_results):
        """Saves job descriptions with AI analysis results to the database."""
        self._job_storage.save_job_posts_to_db(job_match_results)

    def set_resume_path(self, path):
            """Sets the resume path and performs any additional initialization if necessary."""
            self.resume_path = path    


    def run(self, job_title, location, filters):
        """Runs the job search and evaluation workflow."""
        
        
        logger.info("✅ GrowHireBot run completed!")

   
