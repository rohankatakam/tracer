"""
VideoFrame model for the SQLAlchemy ORM.

This module defines the VideoFrame entity, which represents a single frame
extracted from video content in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
from uuid import uuid4


class VideoFrame(Base):
    """SQLAlchemy model for a video frame."""
    __tablename__ = "video_frames"
    
    frame_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    video_id = Column(String, ForeignKey("video_contents.video_id"))
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    image_id = Column(String, ForeignKey("image_contents.image_id"))
    
    # Relationships
    video = relationship("VideoContent", back_populates="frames")
    image = relationship("ImageContent")
    
    @classmethod
    def from_pydantic(cls, py_model, video_id):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import VideoFrame as PydanticVideoFrame
        
        if not isinstance(py_model, PydanticVideoFrame):
            raise TypeError(f"Expected PydanticVideoFrame, got {type(py_model)}")
            
        return cls(
            frame_id=str(uuid4()),  # Generate new ID for the frame
            video_id=video_id,
            frame_number=py_model.frame_number,
            timestamp=py_model.timestamp,
            image_id=py_model.image_id
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import VideoFrame as PydanticVideoFrame
        
        return PydanticVideoFrame(
            frame_number=self.frame_number,
            timestamp=self.timestamp,
            image_id=self.image_id
        )
