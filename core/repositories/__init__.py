"""
Repository Package

This package provides repository classes for data access layer operations,
replacing the previous pickle-based implementation with a proper ORM-based solution.
"""

from core.repositories.bug_repository import BugRepository
from core.repositories.attachment_repository import (
    AttachmentRepository,
    TextContentRepository,
    ImageContentRepository,
    PDFContentRepository,
    VideoContentRepository
)

__all__ = [
    'BugRepository',
    'AttachmentRepository',
    'TextContentRepository',
    'ImageContentRepository',
    'PDFContentRepository',
    'VideoContentRepository'
]
