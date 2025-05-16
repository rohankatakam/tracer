"""
Task Graph Schema Definition with Pydantic

This module defines Pydantic models representing the task graph schema, providing:
1. Type validation
2. Schema documentation
3. Serialization/deserialization
4. Integration with FastAPI (future use)

The schema is based on the specifications in task_graph_schema.md
"""

from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator


class NodeType(str, Enum):
    """Types of nodes in a task graph."""
    ACTION = "action"
    VERIFICATION = "verification"


class NodeMetadata(BaseModel):
    """Metadata associated with a task graph node."""
    image_refs: List[str] = Field(
        default_factory=list,
        description="References to images that illustrate the step"
    )
    ui_elements: List[str] = Field(
        default_factory=list,
        description="UI elements involved in this step"
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Input values required for this step"
    )
    expected_result: str = Field(
        default="",
        description="Description of the expected outcome"
    )


class Node(BaseModel):
    """Node representing a single step in a task graph."""
    id: str = Field(..., description="Unique identifier for the node")
    type: NodeType = Field(..., description="Type of node: action or verification")
    content: str = Field(..., description="Description of the action to perform or verification to check")
    metadata: NodeMetadata = Field(default_factory=NodeMetadata, description="Additional metadata for the node")


class Edge(BaseModel):
    """Edge defining a relationship between nodes in a task graph."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")

    @validator('target')
    def target_different_from_source(cls, v, values):
        """Validate that target is different from source."""
        if 'source' in values and v == values['source']:
            raise ValueError("Edge target must be different from source")
        return v


class Environment(BaseModel):
    """Environment details for a task graph."""
    application: str = Field(..., description="Application name and version")
    browser: Optional[str] = Field(None, description="Browser used (if applicable)")
    operating_system: Optional[str] = Field(None, description="OS requirements (if applicable)")


class Graph(BaseModel):
    """The graph structure containing nodes and edges."""
    nodes: List[Node] = Field(..., description="List of nodes in the task graph")
    edges: List[Edge] = Field(default_factory=list, description="List of edges defining relationships between nodes")

    @validator('edges')
    def validate_edge_connections(cls, edges, values):
        """Validate that edges reference existing nodes."""
        if 'nodes' not in values:
            return edges
        
        node_ids = {node.id for node in values['nodes']}
        for edge in edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge references non-existent target node: {edge.target}")
        
        return edges


class AttachmentType(str, Enum):
    """Types of attachments in a bug report."""
    PDF = "pdf"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    MP4 = "mp4"


class AttachmentContent(BaseModel):
    """Content of an attachment with extracted text and images."""
    raw_text: str = Field(default="", description="Extracted text from the attachment")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Images extracted from the attachment")
    file_path: Optional[str] = Field(None, description="Path to the original file")


class Attachment(BaseModel):
    """Attachment in a bug report."""
    id: str = Field(..., description="Unique identifier for the attachment")
    name: str = Field(..., description="Name of the attachment")
    type: AttachmentType = Field(..., description="Type of the attachment")
    uploaded_by: Optional[str] = Field(None, description="User who uploaded the attachment")
    uploaded_at: Optional[datetime] = Field(None, description="When the attachment was uploaded")
    description: Optional[str] = Field(None, description="Description of the attachment")
    content: Optional[AttachmentContent] = Field(None, description="Extracted content from the attachment")
    confidentiality: Optional[str] = Field(None, description="Confidentiality level of the attachment")


class Source(BaseModel):
    """Source information for a task graph."""
    model: str = Field(..., description="Model used to generate the task graph")
    raw_data_package: str = Field(..., description="Source of the raw data used to generate the task graph")


class TaskGraph(BaseModel):
    """Complete task graph representation."""
    name: str = Field(..., description="Name of the task graph")
    description: str = Field(..., description="Description of the overall task")
    environment: Environment = Field(..., description="Environment details")
    task_graph: Graph = Field(..., description="The task graph structure with nodes and edges")
    verification_steps: List[str] = Field(
        default_factory=list, 
        description="High-level descriptions of verification points"
    )
    confidence_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for the task graph (0.0 to 1.0)"
    )
    missing_information: List[str] = Field(
        default_factory=list, 
        description="Information that would be helpful but is currently missing"
    )
    source: Optional[Source] = Field(None, description="Source information for the task graph")
    attachments: Optional[List[Attachment]] = Field(
        default_factory=list,
        description="Attachments associated with the bug report"
    )
    
    @root_validator
    def check_graph_connectivity(cls, values):
        """Validate that the graph is connected if it has more than one node."""
        if 'task_graph' not in values:
            return values
        
        graph = values['task_graph']
        if not graph.nodes or len(graph.nodes) <= 1:
            return values
            
        # Check that all nodes are reachable from the first node
        edges_dict = {}
        for edge in graph.edges:
            if edge.source not in edges_dict:
                edges_dict[edge.source] = []
            edges_dict[edge.source].append(edge.target)
        
        # BFS to check connectivity
        visited = set()
        queue = [graph.nodes[0].id]
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            # Add neighbors to queue
            if node_id in edges_dict:
                for neighbor in edges_dict[node_id]:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        # Check if all nodes are visited
        all_node_ids = {node.id for node in graph.nodes}
        if len(visited) != len(all_node_ids):
            unreachable = all_node_ids - visited
            raise ValueError(f"Graph is not fully connected. Unreachable nodes: {unreachable}")
        
        return values


# BugReport has been moved to bug_schema.py
# Import it with: from core.models.bug_schema import BugReport
