"""
Bug Schema Definition with Pydantic

This module defines Pydantic models representing the bug schema, providing:
1. Type validation
2. Schema documentation
3. Serialization/deserialization
4. Integration with FastAPI (future use)

The schema represents bug reports and their relationships to attachments and task graphs.
"""

from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, validator, root_validator

# Import references to related schemas
from core.models.attachment_schema import BugAttachment
from core.models.task_graph_schema import TaskGraph


class BugSeverity(str, Enum):
    """Severity levels for bugs."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class BugStatus(str, Enum):
    """Status values for bugs."""
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"
    REOPENED = "reopened"


class OracleBugStatus(int, Enum):
    """Oracle-specific bug status codes and descriptions."""
    DESCRIPTION_PHASE = 10
    CODE_HARDWARE_BUG = 11
    ASSIGNED_TO_SOLUTION_PARTNER = 14
    SCREENING_TRIAGE = 16
    WORK_IN_PROGRESS = 17
    DEFERRED_AWAITING_ENGINEERING = 24
    OPEN_AWAITING_REVIEW = 25
    OPEN_FAILED_VERIFICATION = 26
    MORE_INFO_REQUESTED = 30
    COULD_NOT_REPRODUCE = 31
    NOT_A_BUG = 32
    SUSPENDED_INFO_NOT_AVAILABLE = 33
    MERGE_TO_BASE_BUG = 34
    TO_FILER_FOR_REVIEW = 35
    DUPLICATE_BUG = 36
    REVIEW_MERGE_REQUIRED = 37
    DUPLICATE_OF_AIME_LRG = 38
    APPROVED_WAITING_FOR_CODELINE = 39
    WAITING_FOR_BASE_BUG_FIX = 40
    BASE_BUG_FIXED_AWAITING_LABEL = 41
    PRODUCT_OBSOLETE = 43
    NOT_FEASIBLE_TO_FIX = 44
    VENDOR_PROBLEM = 45
    DOWNSTREAM_BUG = 46
    SUPPORT_APPROVED_BACKPORT = 51
    PENDING_APPROVAL_BY_PL = 52
    BACKPORT_REQUEST_REJECTED = 53
    ONE_OFF_REQUEST_APPROVED = 54
    PATCH_HAS_ISSUES = 55
    PATCH_SUPERSEDED = 59
    FIX_AVAILABLE_AWAITING_PROMOTION = 60
    CM_AWAITING_DEPLOYMENT = 66
    PSE_TO_QA_PACKAGES_DELIVERED = 69
    CLOSED_DATA_FIX_USER_ERROR = 70
    CLOSED_DATA_FIX_DATA_IMPORT = 71
    CLOSED_DATA_FIX_CODE_ERROR = 72
    CLOSED_DATA_FIX_UNKNOWN = 73
    CLOSED_FIX_VERIFIED = 74
    CLOSED_FIX_NOT_VERIFIED = 75
    CLOSED_PATCH_ISSUES_BUILD = 76
    CLOSED_BLR_MLR_INCORRECT = 77
    CLOSED_ENVIRONMENT_ISSUE = 78
    DEV_TO_QA_FIX_DELIVERED = 80
    QA_TO_DEV_PATCH_AVAILABLE = 81
    CLOSED_PRODUCT_OBSOLETE = 83
    CLOSED_NOT_FEASIBLE = 84
    FIX_SUPERSEDED_CODE_ISSUE = 85
    CLOSED_DOWNSTREAM_BUG = 86
    FIX_VERIFIED_MERGE_REQUIRED = 87
    CLOSED_DUPLICATE_OF_AIME_LRG = 88
    CLOSED_VERIFIED_BY_FILER = 90
    CLOSED_COULD_NOT_REPRODUCE = 91
    CLOSED_NOT_A_BUG = 92
    CLOSED_NOT_VERIFIED_BY_FILER = 93
    CLOSED_VENDOR_PROBLEM = 95
    CLOSED_DUPLICATE_BUG = 96
    
    @classmethod
    def get_description(cls, status_code: int) -> str:
        """Return the description for a given status code."""
        descriptions = {
            10: "Description Phase",
            11: "Code/Hardware Bug (Response/Resolution)",
            14: "Bug Assigned to Solution Partner",
            16: "Bug Screening/Triage",
            17: "Work in Progress",
            24: "Deferred, Awaiting Engineering",
            25: "Open, Awaiting Code/Hardware Review/Post-Provisioning Review",
            26: "Open/Failed Verification",
            30: "More Information Requested from Filer",
            31: "Could Not Reproduce, to Filer",
            32: "Not a Bug, to Filer",
            33: "Suspended, Required Information Not Available",
            34: "Merge to Base Bug",
            35: "To Filer for Review",
            36: "Duplicate Bug, to Filer",
            37: "Review/Merge Required, to Filer",
            38: "Duplicate of AIME LRG",
            39: "Approved, Waiting for Codeline to Open",
            40: "Waiting for Base Bug Fix",
            41: "Base Bug Fixed, Awaiting Base Label/Patch",
            43: "Product/Platform Obsolete, to Filer",
            44: "Not Feasible to Fix, to Filer",
            45: "Vendor OS/Software/Framework Problem",
            46: "Downstream Bug",
            51: "Support Approved Backport - to Development",
            52: "Pending Approval by PL",
            53: "Backport/Patchset Request Rejected",
            54: "One-Off Request Approved",
            55: "Patch/Backport Has Issues",
            59: "Patch/Backport Superseded",
            60: "Fix/Enhancement Available, Awaiting Promotion/Provision",
            66: "CM: Awaiting Deployment",
            69: "PSE to QA: Packages Delivered",
            70: "Closed, Data Fix, Cause - User Error",
            71: "Closed, Data Fix, Cause - Data Import",
            72: "Closed, Data Fix, Cause - Code Error",
            73: "Closed, Data Fix, Cause - Unknown",
            74: "Closed, Code/Hardware Fix Verified",
            75: "Closed, Code/Hardware Fix Not Verified",
            76: "Closed, Patch Issues, Cause - Build/Package",
            77: "Closed, BLR/MLR/Backport Incorrect",
            78: "Closed, Environment Issue (MOS/SaaS)",
            80: "Development to QA/Fix Delivered Internal",
            81: "QA to Dev/Patch or Workaround Available",
            83: "Closed, Product/Platform Obsolete",
            84: "Closed, Not Feasible to Fix",
            85: "Fix Superseded, Code Fix Issue",
            86: "Closed, Downstream Bug",
            87: "Fix Verified/Merge Required",
            88: "Closed as Duplicate of AIME LRG",
            90: "Closed, Verified by Filer",
            91: "Closed, Could Not Reproduce",
            92: "Closed, Not a Bug",
            93: "Closed, Not Verified by Filer",
            95: "Closed, Vendor OS/Software/Framework Problem",
            96: "Closed, Duplicate Bug"
        }
        return descriptions.get(status_code, "Unknown Status")


class BugPriority(str, Enum):
    """Priority values for bugs, indicating the order in which bugs should be fixed."""
    P0 = "p0"     # Critical - drop everything and fix now
    P1 = "p1"     # High - fix in current sprint/release
    P2 = "p2"     # Medium - fix when time allows
    P3 = "p3"     # Low - nice to have, may be deferred
    P4 = "p4"     # Very Low - fix if time permits or in a future refresh


class Comment(BaseModel):
    """Model for bug comments."""
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the comment")
    bug_id: str = Field(..., description="ID of the bug this comment belongs to")
    author: str = Field(..., description="Author of the comment")
    text: str = Field(..., description="Text content of the comment")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the comment was posted")
    is_private: bool = Field(default=False, description="Whether the comment is private")
    attachments: List[str] = Field(default_factory=list, description="IDs of attachments added with this comment")
    
    class Config:
        schema_extra = {
            "example": {
                "comment_id": "com-1234",
                "bug_id": "BUG-1234",
                "author": "jane.smith@example.com",
                "text": "I've reproduced this issue on Firefox 98.0.2. The crash happens consistently when memory usage exceeds 2GB.",
                "timestamp": "2025-05-16T10:15:30",
                "is_private": False,
                "attachments": ["att-5678"]
            }
        }


class UnifiedBugReport(BaseModel):
    """Unified bug report model that supports both generic and Oracle status tracking."""
    bug_id: str = Field(..., description="Unique identifier for the bug")
    title: str = Field(..., description="Title of the bug")
    description: str = Field(..., description="Detailed description of the bug")
    severity: str = Field(default="normal", description="Bug severity")
    priority: str = Field(default="p3", description="Bug priority")
    
    # Status can be either generic string status or Oracle numeric status
    status_type: Literal["generic", "oracle"] = Field(default="generic", description="Type of status tracking system")
    generic_status: Optional[str] = Field(default=None, description="Generic string status value")
    oracle_status: Optional[int] = Field(default=None, description="Oracle numeric status code")
    oracle_status_description: Optional[str] = Field(default=None, description="Description of Oracle status code")
    
    product: Optional[str] = Field(default=None, description="Product this bug affects")
    component: Optional[str] = Field(default=None, description="Component within the product")
    version: Optional[str] = Field(default=None, description="Version of the product")
    platform: Optional[str] = Field(default=None, description="Platform the bug appears on")
    os: Optional[str] = Field(default=None, description="Operating system the bug appears on")
    browser: Optional[str] = Field(default=None, description="Browser information if applicable")
    
    reporter: Optional[str] = Field(default=None, description="User who reported the bug")
    assigned_to: Optional[str] = Field(default=None, description="User assigned to fix the bug")
    cc: Optional[List[str]] = Field(default_factory=list, description="Users to keep informed about the bug")
    
    reported_date: Optional[datetime] = Field(default_factory=datetime.now, description="When the bug was reported")
    last_updated: Optional[datetime] = Field(default_factory=datetime.now, description="When the bug was last updated")
    
    resolution: Optional[str] = Field(default=None, description="Resolution if the bug is resolved")
    
    comments: Optional[List[Union[str, Dict[str, Any]]]] = Field(default_factory=list, description="Comments on the bug")
    attachments: Optional[List[Union[str, BugAttachment]]] = Field(default_factory=list, description="Attachments related to the bug")
    
    # Optional relationships
    blocks: Optional[List[str]] = Field(default_factory=list, description="Bugs that this bug blocks")
    depends_on: Optional[List[str]] = Field(default_factory=list, description="Bugs that this bug depends on")
    duplicate_of: Optional[str] = Field(default=None, description="If this is a duplicate, the ID of the original bug")
    
    # Optional fields for additional metadata
    keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords/tags for the bug")
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom fields specific to the installation")
    
    # Optional task graph association
    task_graph: Optional[Union[str, TaskGraph]] = Field(default=None, description="Associated task graph for this bug")
    
    @root_validator(pre=True)
    def set_oracle_status_description(cls, v):
        """Automatically set Oracle status description based on status code if not provided."""
        if v.get('status_type') == 'oracle' and v.get('oracle_status') is not None and not v.get('oracle_status_description'):
            v['oracle_status_description'] = OracleBugStatus.get_description(v['oracle_status'])
        return v
    
    @validator('generic_status', 'oracle_status', pre=True)
    def validate_status_fields(cls, v, values, field):
        """Validate that the appropriate status field is set based on status_type."""
        status_type = values.get('status_type')
        if field.name == 'generic_status' and status_type == 'generic' and v is None:
            return 'new'  # Default generic status
        if field.name == 'oracle_status' and status_type == 'oracle' and v is None:
            return OracleBugStatus.DESCRIPTION_PHASE.value  # Default Oracle status
        return v


class BugDatabase(BaseModel):
    """Model representing the bug database structure for any bug system."""
    bugs: Dict[str, UnifiedBugReport] = Field(default_factory=dict, description="Mapping of bug_id to UnifiedBugReport")
    comments: Dict[str, Comment] = Field(default_factory=dict, description="Mapping of comment_id to Comment")
    system_name: str = Field(default="Generic", description="Name of the bug tracking system")
    
    class Config:
        schema_extra = {
            "example": {
                "bugs": {
                    "BUG-1234": {
                        "bug_id": "BUG-1234",
                        "title": "Application crashes when saving large file",
                        "description": "The application crashes with an out of memory error when attempting to save files larger than 100MB.",
                        "severity": "major",
                        "priority": "p1",
                        "status_type": "generic",
                        "generic_status": "in_progress",
                        "oracle_status": None,
                        "product": "Firefox",
                        "component": "File Handling",
                        "platform": "Windows",
                        "os": "Windows 11",
                        "browser": "Firefox 123.0"
                    },
                    "BUG-5678": {
                        "bug_id": "BUG-5678",
                        "title": "Database query timeout on large datasets",
                        "description": "Query execution times out when processing datasets over 1GB",
                        "severity": "critical",
                        "priority": "p0",
                        "status_type": "oracle",
                        "generic_status": None,
                        "oracle_status": 17,
                        "oracle_status_description": "Work in Progress",
                        "product": "Oracle Database",
                        "component": "Query Processor",
                        "platform": "Linux",
                        "os": "Oracle Linux 8"
                    }
                },
                "comments": {
                    "com-1234": {
                        "comment_id": "com-1234",
                        "bug_id": "BUG-1234",
                        "author": "jane.smith@example.com",
                        "text": "I've reproduced this issue on Firefox 98.0.2. The crash happens consistently when memory usage exceeds 2GB.",
                        "timestamp": "2025-05-16T10:15:30"
                    },
                    "com-5678": {
                        "comment_id": "com-5678",
                        "bug_id": "BUG-5678",
                        "author": "database.admin@example.com",
                        "text": "I've identified the root cause as inefficient query execution plan. Working on optimization patch.",
                        "timestamp": "2025-05-16T13:45:20"
                    }
                }
            }
        }
