"""
Comment model for the SQLAlchemy ORM.

This module defines the Comment entity, which represents user comments
on bugs in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from config.database import Base
import datetime
from uuid import uuid4


# Association table for comment-attachment many-to-many relationship
comment_attachment_association = Table(
    'comment_attachment_association',
    Base.metadata,
    Column('comment_id', String, ForeignKey('comments.comment_id', ondelete="CASCADE")),
    Column('attachment_id', String, ForeignKey('attachments.attachment_id', ondelete="CASCADE"))
)


class Comment(Base):
    """SQLAlchemy model for a bug comment."""
    __tablename__ = "comments"
    
    comment_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    bug_id = Column(String, ForeignKey("bugs.bug_id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    is_private = Column(Boolean, default=False)
    
    # Relationships
    bug = relationship("Bug", back_populates="comments")
    referenced_attachments = relationship(
        "Attachment",
        secondary=comment_attachment_association,
        backref="referenced_in_comments"
    )
    
    # Association proxy to get attachment_ids directly
    attachment_ids = association_proxy(
        "referenced_attachments", "attachment_id"
    )
    
    def to_dict(self):
        """Convert model instance to dictionary for API responses."""
        return {
            "comment_id": self.comment_id,
            "bug_id": self.bug_id,
            "author": self.author,
            "text": self.text,
            "timestamp": self.timestamp,
            "is_private": self.is_private,
            "attachment_ids": [a.attachment_id for a in self.referenced_attachments] if self.referenced_attachments else []
        }
