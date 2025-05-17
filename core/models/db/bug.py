"""
Bug model for the SQLAlchemy ORM.

This module defines the Bug entity, which represents a software issue
being tracked by the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, DateTime, Integer, Enum, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from config.database import Base
import datetime
import enum
from uuid import uuid4
from typing import Dict, Any, Optional


class BugSchemaType(enum.Enum):
    """Enum for bug schema types"""
    BASE = "base"
    MOZILLA = "mozilla"
    CHROMIUM = "chromium"
    ORACLE = "oracle"

class BugStatus(enum.Enum):
    """Enum for bug status"""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class MozillaSeverity(enum.Enum):
    """Mozilla/Bugzilla severity levels"""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    NORMAL = "normal"
    MINOR = "minor"
    TRIVIAL = "trivial"
    ENHANCEMENT = "enhancement"

class MozillaPriority(enum.Enum):
    """Mozilla/Bugzilla priority levels"""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"

class MozillaStatus(enum.Enum):
    """Mozilla/Bugzilla status values"""
    UNCONFIRMED = "UNCONFIRMED"
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    REOPENED = "REOPENED"

class MozillaResolution(enum.Enum):
    """Mozilla/Bugzilla resolution values"""
    FIXED = "FIXED"
    INVALID = "INVALID"
    WONTFIX = "WONTFIX"
    DUPLICATE = "DUPLICATE"
    WORKSFORME = "WORKSFORME"
    INCOMPLETE = "INCOMPLETE"

class ChromiumPriority(enum.Enum):
    """Chromium priority levels"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class ChromiumType(enum.Enum):
    """Chromium issue types"""
    BUG = "Bug"
    FEATURE = "Feature"
    FEATURE_REQUEST = "Feature Request"
    TASK = "Task"

class ChromiumStatus(enum.Enum):
    """Chromium issue status values"""
    UNCONFIRMED = "Unconfirmed"
    UNTRIAGED = "Untriaged"
    ASSIGNED = "Assigned"
    STARTED = "Started"
    FIXED = "Fixed"
    VERIFIED = "Verified"
    DUPLICATE = "Duplicate"
    WONTFIX = "WontFix"
    ARCHIVED = "Archived"

class BaseSeverity(enum.Enum):
    """Base severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BaseStatus(enum.Enum):
    """Base status values"""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Bug(Base):
    """SQLAlchemy model for a bug with schema-specific fields."""
    __tablename__ = "bugs"
    
    # Common fields for all bug types
    bug_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    reporter = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    schema_type = Column(Enum(BugSchemaType), default=BugSchemaType.BASE, nullable=False)
    
    # Base type fields
    severity = Column(Enum(BaseSeverity))
    status = Column(Enum(BaseStatus), default=BaseStatus.NEW)
    
    # Common optional fields
    product = Column(String)
    component = Column(String)
    version = Column(String)
    platform = Column(String)
    operating_system = Column(String)
    
    # Mozilla/Bugzilla specific fields
    mozilla_severity = Column(Enum(MozillaSeverity))
    mozilla_priority = Column(Enum(MozillaPriority))
    mozilla_status = Column(Enum(MozillaStatus))
    mozilla_resolution = Column(Enum(MozillaResolution))
    mozilla_version = Column(String)
    mozilla_component = Column(String)
    mozilla_keywords = Column(String)  # Comma-separated keywords
    
    # Chromium specific fields
    chromium_priority = Column(Enum(ChromiumPriority))
    chromium_type = Column(Enum(ChromiumType))
    chromium_status = Column(Enum(ChromiumStatus))
    chromium_component = Column(String)
    chromium_owner = Column(String)
    chromium_cc = Column(String)  # Comma-separated CC list
    chromium_labels = Column(String)  # Comma-separated labels
    
    # Oracle specific fields
    oracle_status_code = Column(Integer)
    oracle_status_description = Column(String)
    oracle_severity = Column(String)
    oracle_priority = Column(String)
    oracle_close_reason = Column(String)
    oracle_environment = Column(String)
    
    # Additional data stored as JSON for flexible extensions
    extra_data = Column(JSON, default=dict)
    
    # Relationships
    attachments = relationship("Attachment", back_populates="bug", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="bug", cascade="all, delete-orphan", lazy="dynamic")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the bug model to a dictionary with schema-specific fields."""
        # Safely convert enum to string value or handle string values directly
        def safe_enum_value(enum_obj):
            if enum_obj is None:
                return None
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # First determine what the schema_type is - handle both enum and string cases
        schema_type_value = None
        if self.schema_type:
            schema_type_value = safe_enum_value(self.schema_type)
            
        # Handle if schema_type is a string that might have the format 'BugSchemaType.BASE'
        if isinstance(schema_type_value, str) and '.' in schema_type_value:
            schema_type_value = schema_type_value.split('.')[-1]
            
        result = {
            "bug_id": self.bug_id,
            "title": self.title,
            "description": self.description,
            "reporter": self.reporter,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_type": schema_type_value,
            "product": self.product,
            "component": self.component,
            "version": self.version,
            "platform": self.platform,
            "operating_system": self.operating_system,
            "extra_data": {} if self.extra_data is None else self.extra_data,
        }
        
        # Common fields that should be included regardless of schema_type
        if hasattr(self, 'severity') and self.severity is not None:
            result["severity"] = safe_enum_value(self.severity)
            
        if hasattr(self, 'status') and self.status is not None:
            result["status"] = safe_enum_value(self.status)
            
        # Include schema-specific fields - handle both enum object and string values
        if schema_type_value == "BASE" or schema_type_value == "base":
            # Basic fields already included above
            pass
        
        # Mozilla fields
        if hasattr(self, 'mozilla_severity') and self.mozilla_severity is not None:
            result["mozilla_severity"] = safe_enum_value(self.mozilla_severity)
            
        if hasattr(self, 'mozilla_priority') and self.mozilla_priority is not None:
            result["mozilla_priority"] = safe_enum_value(self.mozilla_priority)
            
        if hasattr(self, 'mozilla_status') and self.mozilla_status is not None:
            result["mozilla_status"] = safe_enum_value(self.mozilla_status)
            
        if hasattr(self, 'mozilla_resolution') and self.mozilla_resolution is not None:
            result["mozilla_resolution"] = safe_enum_value(self.mozilla_resolution)
            
        if hasattr(self, 'mozilla_version') and self.mozilla_version is not None:
            result["mozilla_version"] = self.mozilla_version
            
        if hasattr(self, 'mozilla_component') and self.mozilla_component is not None:
            result["mozilla_component"] = self.mozilla_component
            
        if hasattr(self, 'mozilla_keywords') and self.mozilla_keywords is not None:
            result["mozilla_keywords"] = self.mozilla_keywords
            
        # Chromium fields
        if hasattr(self, 'chromium_priority') and self.chromium_priority is not None:
            result["chromium_priority"] = safe_enum_value(self.chromium_priority)
            
        if hasattr(self, 'chromium_type') and self.chromium_type is not None:
            result["chromium_type"] = safe_enum_value(self.chromium_type)
            
        if hasattr(self, 'chromium_status') and self.chromium_status is not None:
            result["chromium_status"] = safe_enum_value(self.chromium_status)
            
        if hasattr(self, 'chromium_component') and self.chromium_component is not None:
            result["chromium_component"] = self.chromium_component
            
        if hasattr(self, 'chromium_owner') and self.chromium_owner is not None:
            result["chromium_owner"] = self.chromium_owner
            
        if hasattr(self, 'chromium_cc') and self.chromium_cc is not None:
            result["chromium_cc"] = self.chromium_cc
            
        if hasattr(self, 'chromium_labels') and self.chromium_labels is not None:
            result["chromium_labels"] = self.chromium_labels
            
        # Oracle fields
        if hasattr(self, 'oracle_status_code') and self.oracle_status_code is not None:
            result["oracle_status_code"] = self.oracle_status_code
            
        if hasattr(self, 'oracle_status_description') and self.oracle_status_description is not None:
            result["oracle_status_description"] = self.oracle_status_description
            
        if hasattr(self, 'oracle_severity') and self.oracle_severity is not None:
            result["oracle_severity"] = self.oracle_severity
            
        if hasattr(self, 'oracle_priority') and self.oracle_priority is not None:
            result["oracle_priority"] = self.oracle_priority
            
        if hasattr(self, 'oracle_close_reason') and self.oracle_close_reason is not None:
            result["oracle_close_reason"] = self.oracle_close_reason
            
        if hasattr(self, 'oracle_environment') and self.oracle_environment is not None:
            result["oracle_environment"] = self.oracle_environment
            
        return result
