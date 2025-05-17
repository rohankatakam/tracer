"""
VideoContent model for the SQLAlchemy ORM.

This module defines the VideoContent entity, which represents video files
and their extracted content in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
import datetime
from uuid import uuid4


class VideoContent(Base):
    """SQLAlchemy model for video content and metadata."""
    __tablename__ = "video_contents"
    
    video_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_path = Column(String)
    storage_location = Column(String)
    duration = Column(Float, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String, nullable=False)
    codec = Column(String)
    fps = Column(Float, nullable=False)
    audio_text_id = Column(String, ForeignKey("text_contents.text_id"))
    processing_timestamp = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    audio_text = relationship("TextContent")
    frames = relationship("VideoFrame", back_populates="video", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="video_content")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import VideoContent as PydanticVideoContent
        
        if not isinstance(py_model, PydanticVideoContent):
            raise TypeError(f"Expected PydanticVideoContent, got {type(py_model)}")
            
        # Create the VideoContent instance
        video_content = cls(
            video_id=py_model.video_id,
            file_path=py_model.file_path,
            storage_location=py_model.storage_location,
            duration=py_model.duration,
            width=py_model.width,
            height=py_model.height,
            format=py_model.format,
            codec=py_model.codec,
            fps=py_model.fps,
            audio_text_id=py_model.audio_text_id,
            processing_timestamp=py_model.processing_timestamp
        )
        
        # We'll handle the frames relationship separately
        return video_content
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import VideoContent as PydanticVideoContent
        
        # Convert frames to Pydantic models
        pydantic_frames = [frame.to_pydantic() for frame in self.frames]
        
        return PydanticVideoContent(
            video_id=self.video_id,
            file_path=self.file_path,
            storage_location=self.storage_location,
            duration=self.duration,
            width=self.width,
            height=self.height,
            format=self.format,
            codec=self.codec,
            fps=self.fps,
            extracted_frames=pydantic_frames,
            audio_text_id=self.audio_text_id,
            processing_timestamp=self.processing_timestamp
        )
