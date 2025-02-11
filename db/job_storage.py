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

class LinkedInPost(Base):
    """LinkedIn Post Model for SQLAlchemy ORM."""
    __tablename__ = "linkedin_posts"  # Ensure this matches your database table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), unique=True, nullable=False)  # Unique LinkedIn post ID
    publisher_url = Column(Text, nullable=True)  # URL of the post's author
    publish_date = Column(TIMESTAMP, nullable=True)  # Post's publish date
    post_text = Column(Text, nullable=True)  # Content of the post
    links = Column(JSON, nullable=True)  # Store links as JSON
    emails = Column(JSON, nullable=True)  # ✅ Added field to store extracted emails as JSON
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())  # Auto timestamp



# ✅ JobStorage Class
class JobStorage:
    """Handles saving job details to the database using SQLAlchemy."""

    def __init__(self, db_url=None, retries=5, delay=5):
        """Initialize database storage with Docker detection and retries."""
        
        # ✅ Detect if running inside Docker
        IS_DOCKER = os.path.exists("/.dockerenv")

        # ✅ Determine the correct database host
        DB_HOST = "db" if IS_DOCKER else "localhost"

        # ✅ Set database connection URL and enforce pymysql usage
        self.db_url = db_url or os.getenv(
            "DATABASE_URL", f"mysql://root:root@{DB_HOST}:3306/growhire"
        )
        
        # ✅ Ensure pymysql is explicitly used
        if self.db_url.startswith("mysql://"):
            self.db_url = self.db_url.replace("mysql://", "mysql+pymysql://")

        logger.info(f"🔍 Using Database URL: {self.db_url}")

        # ✅ Try connecting to the database with retries
        self.engine = self.create_db_engine_with_retries(retries, delay)
        self.Session = sessionmaker(bind=self.engine)

        logger.info("✅ Database Storage Initialized")

    def create_db_engine_with_retries(self, retries=5, delay=15):
            """Try connecting to the database with retries."""
            for attempt in range(1, retries + 1):
                try:
                    engine = create_engine(self.db_url, echo=False)
                    with engine.connect() as connection:
                        connection.execute(text("SELECT 1"))  # Test query
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

    def is_db_connected(self, retries=5, delay=5):
        """Check if the database connection is active, with retries if needed."""
        session = self.Session()
        
        for attempt in range(1, retries + 1):
            try:
                session.execute(text("SELECT 1"))  # Simple test query
                session.close()
                logger.info(f"✅ Database connection is active (Attempt {attempt}/{retries}).")
                return True
            except OperationalError as e:
                logger.error(f"❌ Database connection failed (Attempt {attempt}/{retries}): {e}")
                
                if attempt < retries:
                    logger.info(f"🔄 Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("🚨 Database is not available after multiple attempts.")
                    return False

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
        """Saves LinkedIn posts to the database, including links and emails."""
        session = self.Session()
        try:
            for post_data in post_data_list:
                if not isinstance(post_data, dict):  # ✅ Ensure correct data format
                    logger.error(f"❌ Invalid post format: {post_data}")
                    continue

                post_id = post_data.get("post_id")
                if not post_id:
                    logger.error(f"❌ Missing post_id in post: {post_data}")
                    continue  # Skip invalid posts

                # ✅ Check if the post already exists
                post = session.query(LinkedInPost).filter_by(post_id=post_id).first()

                if post:  # ✅ Update existing post
                    post.publisher_url = post_data.get("post_publisher_url")
                    post.publish_date = post_data.get("post_date")
                    post.post_text = post_data.get("post_text", "")
                    post.links = json.dumps(post_data.get("post_links", []))  # ✅ Store links as JSON
                    post.emails = json.dumps(post_data.get("post_emails", []))  # ✅ Store emails as JSON
                else:  # ✅ Insert new post
                    post = LinkedInPost(
                        post_id=post_id,
                        publisher_url=post_data.get("post_publisher_url"),
                        publish_date=post_data.get("post_date"),
                        post_text=post_data.get("post_text", ""),
                        links=json.dumps(post_data.get("post_links", [])),  # ✅ Store links as JSON
                        emails=json.dumps(post_data.get("post_emails", []))  # ✅ Store emails as JSON
                    )
                    session.add(post)

            session.commit()  # ✅ Commit transaction
            logger.info(f"✅ Successfully saved {len(post_data_list)} LinkedIn posts.")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error saving LinkedIn posts: {e}")

        finally:
            session.close()
