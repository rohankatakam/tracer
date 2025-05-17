"""
API Dependencies

This module provides dependency injection for FastAPI endpoints.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Generator

from core.database.engine import get_db


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for providing a database session to FastAPI endpoints.
    Handles proper session closing upon request completion.
    
    Yields:
        A SQLAlchemy database session that will be automatically closed
    """
    session = get_db()
    try:
        yield session
    finally:
        session.close()
