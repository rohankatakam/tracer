"""
Base models and association tables for the SQLAlchemy ORM.

This module defines the common base classes and association tables
used across all database models for the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, ForeignKey, Table
from config.database import Base

# Association tables for many-to-many relationships
attachment_text_association = Table(
    'attachment_text_association', Base.metadata,
    Column('attachment_id', String, ForeignKey('attachments.attachment_id')),
    Column('text_id', String, ForeignKey('text_contents.text_id'))
)

attachment_image_association = Table(
    'attachment_image_association', Base.metadata,
    Column('attachment_id', String, ForeignKey('attachments.attachment_id')),
    Column('image_id', String, ForeignKey('image_contents.image_id'))
)

pdf_page_text_association = Table(
    'pdf_page_text_association', Base.metadata,
    Column('pdf_page_id', String, ForeignKey('pdf_pages.page_id')),
    Column('text_id', String, ForeignKey('text_contents.text_id'))
)

pdf_page_image_association = Table(
    'pdf_page_image_association', Base.metadata,
    Column('pdf_page_id', String, ForeignKey('pdf_pages.page_id')),
    Column('image_id', String, ForeignKey('image_contents.image_id'))
)
