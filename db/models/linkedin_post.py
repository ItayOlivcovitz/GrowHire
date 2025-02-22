from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
# Import the shared Base from db.models.__init__.py
from db.models import Base

class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), unique=True, nullable=False)
    publisher_url = Column(Text, nullable=True)
    publish_date = Column(TIMESTAMP, nullable=True)
    post_text = Column(Text, nullable=False)
    links = Column(Text, nullable=True)  # JSON stored as text in SQLite
    emails = Column(Text, nullable=True)  # JSON stored as text in SQLite
    keyword_found = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())

    def __init__(self, post_id, post_text, publisher_url=None, publish_date=None,
                 links=None, emails=None, keyword_found=None):
        """
        Initialize a new LinkedInPost object.

        :param post_id: Unique identifier for the post (string)
        :param post_text: Full text content of the post (string)
        :param publisher_url: URL of the publisher (string, default None)
        :param publish_date: Publish date (timestamp, default None)
        :param links: JSON-formatted links (string, default None)
        :param emails: JSON-formatted extracted emails (string, default None)
        :param keyword_found: Keyword found in the post (string, default None)
        """
        self.post_id = post_id
        self.publisher_url = publisher_url
        self.publish_date = publish_date
        self.post_text = post_text
        self.links = links
        self.emails = emails
        self.keyword_found = keyword_found
