"""
Database engine and session management for the Bug Attachment Processing system.

This module provides functions to create and manage database sessions,
ensuring proper connection and cleanup of resources.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# Make sure environment variables are loaded
load_dotenv()

# Database credentials from environment variables
DB_USER = os.getenv("DB_USER", "bug_processor")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_password_123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bug_attachment_db")

# Create SQLAlchemy engine URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with appropriate configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Check if connection is alive
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True for SQL logging (development only)
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Get a database session.
    
    Returns:
        Session: A new SQLAlchemy session.
        
    Note:
        The caller is responsible for closing this session.
    """
    return SessionLocal()

@contextmanager
def db_session():
    """
    Context manager for database sessions.
    
    Automatically handles session creation and cleanup, including
    rolling back failed transactions.
    
    Yields:
        Session: A SQLAlchemy session for database operations.
        
    Usage:
        with db_session() as session:
            results = session.query(Bug).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
