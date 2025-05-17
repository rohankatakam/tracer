"""
Services Package

This package provides service layers that encapsulate business logic and data access.
Services abstract the underlying data storage mechanisms, making it easier to maintain
and update the application without changing higher-level components.
"""

from core.services.attachment_service import (
    store_attachment,
    get_attachment,
    get_attachments_by_bug_id,
    store_text_content,
    get_text_content,
    store_image_content,
    get_image_content,
    store_pdf_content,
    get_pdf_content,
    store_video_content,
    get_video_content,
    get_attachment_database
)

__all__ = [
    'store_attachment',
    'get_attachment',
    'get_attachments_by_bug_id',
    'store_text_content',
    'get_text_content',
    'store_image_content',
    'get_image_content',
    'store_pdf_content',
    'get_pdf_content',
    'store_video_content',
    'get_video_content',
    'get_attachment_database'
]
