"""
Database configuration for the Bug-to-Task-Graph Pipeline.
This module provides the connection details and configuration for PostgreSQL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database credentials from environment variables
DB_USER = os.getenv("DB_USER", "bug_processor")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_password_123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bug_attachment_db")

# Create SQLAlchemy engine URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Get a database session.
    Yields a session that will be closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
