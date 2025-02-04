import os  # Ensure this import is present
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime


# ✅ Configure Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Define Base Model
Base = declarative_base()

class JobDescription(Base):
    """Job Description Model for SQLAlchemy ORM."""
    __tablename__ = "job_descriptions"  # Ensure this matches the table name in your database

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_location = Column(String(255), nullable=False)
    job_url = Column(Text, unique=True, nullable=False)  # 
    connections = Column(Integer, default=0)
    score = Column(Integer, default=0)
    job_description = Column(Text, nullable=False)
    chat_gpt_response = Column(Text)  # ChatGPT response field
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())  


# ✅ JobStorage Class
class JobStorage:
    """Handles saving job details to the database using SQLAlchemy."""

    def __init__(self, db_url=None):
        """Initialize database storage."""
        # Use MySQL connection string (Update with your credentials)
        self.db_url = db_url or os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/growhire")  # Default to MySQL
        self.engine = create_engine(self.db_url, echo=False)  # Create engine for MySQL connection
        self.Session = sessionmaker(bind=self.engine)  # Create sessionmaker bound to the engine
        
        # Create tables in the database
        Base.metadata.create_all(self.engine)

        logger.info(f"✅ Database Storage Initialized: {self.db_url}")

    def save_to_db(self, job_data):
        """Saves a job description to the database."""
        session = self.Session()  # Create a new session
        try:
            # ✅ Remove 'created_at' (MySQL auto-fills it)
            job_data.pop("created_at", None)

            # ✅ Convert dictionary to JobDescription object
            job_description = JobDescription(**job_data)  
            session.add(job_description)  # Add job description to the session
            
            session.commit()  # ✅ Ensure the transaction is committed
            
            logger.info(f"✅ Job description saved to database: {job_description.job_title} at {job_description.company_name}")

        except Exception as e:
            session.rollback()  # ✅ Ensure rollback only happens on error
            logger.error(f"❌ Error saving job description: {e}")
        
        finally:
            session.close()  # ✅ Always close the session

    def get_jobs(self):
        """Fetch all job descriptions from the database."""
        session = self.Session()  # Create a new session
        job_descriptions = session.query(JobDescription).all()  # Query all job descriptions
        session.close()  # Close session
        return job_descriptions
    
    def save_job_matches_to_db(self, job_match_results):
        """Saves job descriptions with AI analysis results to the database."""
        session = self.Session()
        try:
            for match in job_match_results:
                job = session.query(JobDescription).filter_by(job_url=match["job_url"]).first()  # ✅ Query job first

                if job:  # ✅ If job exists, update it
                    job.score = match.get("score", 0)  # ✅ Default to 0 if missing
                    job.chat_gpt_response = match.get("chat_gpt_response", "")
                else:  # ✅ If no job exists, create a new one
                    job = JobDescription(
                        job_title=match["job_title"],  # ✅ Fix key names
                        company_name=match["company_name"],
                        job_location=match["job_location"],
                        job_url=match["job_url"],
                        connections=match.get("connections", 0),
                        score=match.get("score", 0),
                        job_description=match["job_description"],
                        chat_gpt_response=match.get("chat_gpt_response"),
                    )
                    session.add(job)  # ✅ Insert new record

            session.commit()  # ✅ Commit transaction
            logger.info(f"✅ Successfully saved {len(job_match_results)} job descriptions.")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving job match results: {e}")

        finally:
            session.close()

