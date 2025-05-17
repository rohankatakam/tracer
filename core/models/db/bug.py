"""
Bug model for the SQLAlchemy ORM.

This module defines the Bug entity, which represents a software issue
being tracked by the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from config.database import Base
import datetime
from uuid import uuid4


class Bug(Base):
    """SQLAlchemy model for a bug."""
    __tablename__ = "bugs"
    
    bug_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    reporter = Column(String)
    severity = Column(String)
    status = Column(String, default="NEW")
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    attachments = relationship("Attachment", back_populates="bug", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="bug", cascade="all, delete-orphan")
