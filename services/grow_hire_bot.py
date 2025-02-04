import logging
from services.linkedinNavigator.linkedin_navigator import LinkedInNavigator
from services.jobScraper.job_scraper import JobScraper  # ✅ Relative Import
from db.job_storage import JobStorage  
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from services.pdfReader.pdf_reader import PDFReader
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
        

    def set_resume_path(self, path):
            """Sets the resume path and performs any additional initialization if necessary."""
            self.resume_path = path    

    def run(self, job_title, location, filters):
        """Runs the job search and evaluation workflow."""
        
        
        logger.info("✅ GrowHireBot run completed!")

   
