from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
# Import the shared Base from db.models.__init__.py
from db.models import Base

class JobDescription(Base):
    __tablename__ = "job_descriptions"  # This tells SQLAlchemy the table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_location = Column(String(255), nullable=False)
    job_url = Column(Text, nullable=False)
    connections = Column(Integer, default=0)
    score = Column(Integer, default=0)
    job_description = Column(Text, nullable=False)
    chat_gpt_response = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())

    def __init__(self, job_title, company_name, job_location, job_url, job_description, 
                 connections=0, score=0, chat_gpt_response=None):
        """
        Initialize a new JobDescription object.

        :param job_title: Job title (string)
        :param company_name: Company name (string)
        :param job_location: Job location (string)
        :param job_url: Job posting URL (string)
        :param job_description: Full job description (string)
        :param connections: Number of connections (int, default 0)
        :param score: Score for ranking (int, default 0)
        :param chat_gpt_response: Optional ChatGPT-generated response (string, default None)
        """
        self.job_title = job_title
        self.company_name = company_name
        self.job_location = job_location
        self.job_url = job_url
        self.job_description = job_description
        self.connections = connections
        self.score = score
        self.chat_gpt_response = chat_gpt_response
