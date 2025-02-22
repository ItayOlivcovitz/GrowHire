import os  # Ensure this import is present
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func
import json 
from sqlalchemy import text
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import JSON  # ✅ Correct import for MySQL
from sqlalchemy.orm import sessionmaker, declarative_base
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from db.models.job_description import JobDescription
from db.models.linkedin_post import LinkedInPost
from db.sqlite import sqlite
from pathlib import Path



# ✅ Configure Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Define Base Model
Base = declarative_base()





# ✅ JobStorage Class
class JobStorage:
    """Handles saving job details to the database using SQLAlchemy."""

     #Singleton pattern
     # Class-level variable to hold the singleton instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        # If an instance does not exist, create one
        if cls._instance is None:
            cls._instance = super(JobStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self, retries=5, delay=5):
        """Initialize database storage with Docker detection and retries."""
        
        # Detect if running inside Docker
        IS_DOCKER = os.path.exists("/.dockerenv")
        DB_HOST = "db" if IS_DOCKER else "localhost"
        
        # Look up the DATABASE_URL from environment variables; default to MySQL if not set.
        self.db_url = os.getenv("DATABASE_URL", f"mysql://root:root@{DB_HOST}:3306/growhire")
        
        # If using MySQL, enforce pymysql usage
        if self.db_url.startswith("mysql://"):
            self.db_url = self.db_url.replace("mysql://", "mysql+pymysql://")
        
        # If using SQLite, ensure we have an absolute path and that the directory exists
        if self.db_url.startswith("sqlite"):
            base_dir = Path(os.getcwd()).resolve()
            db_dir = base_dir / "data"  # Use a dedicated subdirectory (e.g., "data")
            db_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
            db_path = db_dir / "growhire.db"
            self.db_url = f"sqlite:///{db_path.as_posix()}"
        
        logger.info(f"🔍 Using Database URL: {self.db_url}")
        
        # Create engine with retries, adding connect_args if using SQLite
        if self.db_url.startswith("sqlite"):
            self.engine = self.create_db_engine_with_retries(retries, delay, connect_args={"check_same_thread": False})
        else:
            self.engine = self.create_db_engine_with_retries(retries, delay)
        
        # If using SQLite, initialize the database (create tables) using our custom function.
        if self.db_url.startswith("sqlite"):
            import db.sqlite.sqlite as sqlite
            sqlite.init_db(self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        logger.info("✅ Database Storage Initialized")
    

    from pathlib import Path
import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

class JobStorage:
    def __init__(self, retries=5, delay=5):
        """Initialize database storage with Docker detection and retries."""
        
        # Detect if running inside Docker
        IS_DOCKER = os.path.exists("/.dockerenv")
        DB_HOST = "db" if IS_DOCKER else "localhost"
        
        # Look up the DATABASE_URL from environment variables; default to MySQL if not set.
        self.db_url = os.getenv("DATABASE_URL", f"mysql://root:root@{DB_HOST}:3306/growhire")
        
        # If using MySQL, enforce pymysql usage
        if self.db_url.startswith("mysql://"):
            self.db_url = self.db_url.replace("mysql://", "mysql+pymysql://")
        
        # If using SQLite, ensure we have an absolute path and that the directory exists
        if self.db_url.startswith("sqlite"):
            base_dir = Path(os.getcwd()).resolve()
            db_dir = base_dir / "data"  # Use a dedicated subdirectory (e.g., "data")
            db_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
            db_path = db_dir / "growhire.db"
            self.db_url = f"sqlite:///{db_path.as_posix()}"
        
        logger.info(f"🔍 Using Database URL: {self.db_url}")
        
        # Create engine with retries, adding connect_args if using SQLite
        if self.db_url.startswith("sqlite"):
            self.engine = self.create_db_engine_with_retries(retries, delay, connect_args={"check_same_thread": False})
        else:
            self.engine = self.create_db_engine_with_retries(retries, delay)
        
        # If using SQLite, initialize the database (create tables) using our custom function.
        if self.db_url.startswith("sqlite"):
            import db.sqlite.sqlite as sqlite
            sqlite.init_db(self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        logger.info("✅ Database Storage Initialized")

    def create_db_engine_with_retries(self, retries=5, delay=5, **kwargs):
        """Try connecting to the database with retries."""
        for attempt in range(1, retries + 1):
            try:
                engine = create_engine(self.db_url, echo=False, **kwargs)
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                logger.info(f"✅ Database connected on attempt {attempt}/{retries}.")
                return engine
            except OperationalError as e:
                logger.error(f"❌ Database connection failed (Attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    logger.info(f"🔄 Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("🚨 Database connection failed after multiple attempts.")
                    raise
    
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

    def save_job_posts_to_db(self, post_data_list):
        """Saves LinkedIn posts to the database, including links, emails, and keyword_found."""
        session = self.Session()
        try:
            for post_data in post_data_list:
                if not isinstance(post_data, dict):  # Ensure correct data format
                    logger.error(f"❌ Invalid post format: {post_data}")
                    continue

                post_id = post_data.get("post_id")
                if not post_id:
                    logger.error(f"❌ Missing post_id in post: {post_data}")
                    continue  # Skip invalid posts

                # Check if the post already exists
                post = session.query(LinkedInPost).filter_by(post_id=post_id).first()

                if post:  # Update existing post
                    post.publisher_url = post_data.get("post_publisher_url")
                    post.publish_date = post_data.get("post_date")
                    post.post_text = post_data.get("post_text", "")
                    post.links = json.dumps(post_data.get("post_links", []))  # Store links as JSON
                    post.emails = json.dumps(post_data.get("post_emails", []))  # Store emails as JSON
                    post.keyword_found = post_data.get("keyword_found")
                else:  # Insert new post
                    post = LinkedInPost(
                        post_id=post_id,
                        publisher_url=post_data.get("post_publisher_url"),
                        publish_date=post_data.get("post_date"),
                        post_text=post_data.get("post_text", ""),
                        links=json.dumps(post_data.get("post_links", [])),  # Store links as JSON
                        emails=json.dumps(post_data.get("post_emails", [])),  # Store emails as JSON
                        keyword_found=post_data.get("keyword_found")
                    )
                    session.add(post)

            session.commit()  # Commit transaction
            logger.info(f"✅ Successfully saved {len(post_data_list)} LinkedIn posts.")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving LinkedIn posts: {e}")

        finally:
            session.close()


    def get_all_job_descriptions(self):
            """Retrieve all job description records from the database."""
            session = self.Session()
            try:
                jobs = session.query(JobDescription).all()
                logger.info(f"✅ Retrieved {len(jobs)} job descriptions from the database.")
                return jobs
            except Exception as e:
                logger.error(f"❌ Error retrieving job descriptions: {e}")
                return []
            finally:
                session.close()

    def get_all_linkedin_posts(self):
        """Retrieve all LinkedIn post records from the database."""
        session = self.Session()
        try:
            posts = session.query(LinkedInPost).all()
            logger.info(f"✅ Retrieved {len(posts)} LinkedIn posts from the database.")
            return posts
        except Exception as e:
            logger.error(f"❌ Error retrieving LinkedIn posts: {e}")
            return []
        finally:
            session.close()