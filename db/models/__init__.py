from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import models to register them with Base
from db.models.job_description import JobDescription
from db.models.linkedin_post import LinkedInPost
