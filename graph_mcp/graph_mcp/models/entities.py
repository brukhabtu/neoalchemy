"""
Simplified core entities for the engineering management graph.

This module contains 5 fundamental entity types that represent the core
elements of an engineering organization: Person, Team, Service, Task, and Document.
Each entity includes a sources field for URI-based source tracking.
"""

from enum import Enum
from typing import ClassVar

from neo4j.time import Date
from neoalchemy.orm.fields import IndexedField, PrimaryField
from neoalchemy.orm.models import Node
from pydantic import Field, field_validator


class TaskStatus(str, Enum):
    """Task status values."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"




# =============================================================================
# CORE ENTITIES
# =============================================================================


class Person(Node):
    """Person entity - represents team members and stakeholders."""

    email: PrimaryField[str] = Field(
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        description="Valid email address",
        examples=["john.doe@company.com"],
    )
    name: IndexedField[str] = Field(
        min_length=1, max_length=100, description="Full name", examples=["John Doe"]
    )
    title: IndexedField[str] | None = Field(
        default=None,
        max_length=100,
        description="Job title or role",
        examples=["Senior Engineer", "Product Manager"],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source URIs where this person's data originated",
        examples=[
            "ldap://company.com/cn=john.doe",
            "jira://company.atlassian.net/user/john.doe",
            "teams://company.com/user/john.doe",
        ],
    )

    __label__: ClassVar[str] = "Person"

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class Team(Node):
    """Team entity - represents organizational units and working groups."""

    name: PrimaryField[str] = Field(
        min_length=1,
        max_length=100,
        description="Team name",
        examples=["Platform Team", "Mobile Team"],
    )
    focus_area: IndexedField[str] | None = Field(
        default=None,
        max_length=200,
        description="Domain of responsibility",
        examples=["Authentication Services", "Mobile Platform"],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source URIs where this team's data originated",
        examples=[
            "ldap://company.com/ou=platform-team",
            "confluence://company.atlassian.net/spaces/PLAT",
            "jira://company.atlassian.net/projects/PLAT",
        ],
    )

    __label__: ClassVar[str] = "Team"



class Service(Node):
    """Service entity - represents technical services, systems, and repositories."""

    name: PrimaryField[str] = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z][a-zA-Z0-9-_.]*$",
        description="Service name (alphanumeric, dash, underscore, dot)",
        examples=["auth-service", "user-management", "PaymentAPI"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="What the service does",
        examples=["Handles user authentication and authorization"],
    )
    url: str | None = Field(
        default=None,
        description="Primary URL (repository, deployment, documentation)",
        examples=["https://github.com/company/auth-service"],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source URIs where this service's data originated",
        examples=[
            "github://company/auth-service",
            "confluence://company.atlassian.net/pages/123456",
            "jira://company.atlassian.net/projects/AUTH",
        ],
    )

    __label__: ClassVar[str] = "Service"


class Task(Node):
    """Task entity - represents work items, projects, tickets, and initiatives."""

    title: PrimaryField[str] = Field(
        min_length=1,
        max_length=200,
        description="Task title or summary",
        examples=["Implement user authentication", "Migrate to new database"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed task description",
    )
    status: IndexedField[TaskStatus] = Field(
        default=TaskStatus.TODO, description="Current task status"
    )
    priority: IndexedField[str] | None = Field(
        default=None, description="Task priority level"
    )
    assignee: str | None = Field(
        default=None,
        description="Email of the person assigned to this task",
        examples=["john.doe@company.com"],
    )
    due_date: Date | None = Field(default=None, description="When the task is due")
    sources: list[str] = Field(
        default_factory=list,
        description="Source URIs where this task's data originated",
        examples=[
            "jira://company.atlassian.net/browse/PROJ-123",
            "github://company/repo/issues/456",
            "teams://company.com/meetings/planning-session",
        ],
    )

    __label__: ClassVar[str] = "Task"



class Document(Node):
    """Document entity - represents documentation, meeting notes, and knowledge."""

    title: PrimaryField[str] = Field(
        min_length=1,
        max_length=200,
        description="Document title",
        examples=["API Documentation", "Sprint Planning Notes", "Architecture Overview"],
    )
    url: str | None = Field(
        default=None,
        description="URL to the original document",
        examples=["https://company.confluence.com/pages/123456"],
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source URIs where this document's data originated",
        examples=[
            "confluence://company.atlassian.net/pages/123456",
            "teams://company.com/meetings/sprint-planning",
            "sharepoint://company.com/sites/docs/file.docx",
        ],
    )

    __label__: ClassVar[str] = "Document"

