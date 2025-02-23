import os
import pymysql
pymysql.install_as_MySQLdb()

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Get DATABASE_URL from environment variables, fallback to SQLite if not set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///growhire.db")

# If using SQLite, ensure we have an absolute path and that the target directory exists
if DATABASE_URL.startswith("sqlite"):
    # Use the current working directory as the base
    base_dir = Path(os.getcwd()).resolve()
    # Optionally, create a dedicated subdirectory (e.g., "data") to store the SQLite DB file
    db_dir = base_dir / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    # Define the full path for the database file
    db_path = db_dir / "growhire.db"
    # Build the SQLite URI using a POSIX-style path (forward slashes)
    DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

# Create SQLAlchemy engine with proper connect_args for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize the database (create tables if they don't exist)
def init_db(engine):
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

# Note: Do not auto-run init_db() here. Instead, call init_db(engine) from your application.
