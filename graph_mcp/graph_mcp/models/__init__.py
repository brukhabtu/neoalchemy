"""
Simplified Engineering Management Graph Models.

This package contains simplified entity and relationship models for the engineering
management graph with URI-based source tracking.
"""

# Import all entities
from graph_mcp.models.entities import (
    Document,
    Person,
    Service,
    Task,
    TaskStatus,
    Team,
)

# Import all relationships
from graph_mcp.models.relationships import (
    DEPENDS_ON,
    MEMBER_OF,
    REFERENCES,
    RESPONSIBLE_FOR,
    WORKS_ON,
)

__all__ = [
    # Entities
    "Person",
    "Team",
    "Service",
    "Task",
    "Document",
    # Enums
    "TaskStatus",
    # Relationships
    "MEMBER_OF",
    "RESPONSIBLE_FOR",
    "WORKS_ON",
    "DEPENDS_ON",
    "REFERENCES",
]