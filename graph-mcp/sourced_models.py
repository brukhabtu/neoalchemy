"""
Demonstration models using the SourcedNode and SourcedRelationship base classes.

These models inherit from SourcedNode or SourcedRelationship, requiring
at least one source for every entity created.
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional
from uuid import UUID

from neo4j.time import Date, DateTime
from pydantic import Field, model_validator
from sources import SourcedNode, SourcedRelationship, SourceType
from neoalchemy.orm.fields import UniqueField, IndexedField, PrimaryField


class SERVICE(str, Enum):
    """Types of services where accounts can exist."""

    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITHUB = "github"
    GITLAB = "gitlab"
    MS_TEAMS = "ms_teams"
    SLACK = "slack"
    EMAIL = "email"
    SALESFORCE = "salesforce"
    ZENDESK = "zendesk"
    OTHER = "other"

    @classmethod
    def to_source_type(cls, service: "SERVICE") -> SourceType:
        """Convert a SERVICE to the corresponding SourceType."""
        mapping = {
            cls.CONFLUENCE: SourceType.CONFLUENCE,
            cls.JIRA: SourceType.JIRA,
            cls.GITHUB: SourceType.GITHUB,
            cls.GITLAB: SourceType.GITLAB,
            cls.MS_TEAMS: SourceType.TEAMS,
            cls.SLACK: SourceType.SLACK,
            cls.EMAIL: SourceType.EMAIL,
            cls.SALESFORCE: SourceType.SALESFORCE,
            cls.ZENDESK: SourceType.ZENDESK,
            cls.OTHER: SourceType.OTHER,
        }
        return mapping.get(service, SourceType.OTHER)


class Person(SourcedNode):
    """Person node representing an individual with source tracking."""

    name: IndexedField(str, description="Person's full name")
    email: PrimaryField(str, description="Email address (unique identifier)")
    title: IndexedField(str, default=None, description="Job title")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    hire_date: Optional[Date] = Field(default=None, description="Date of hire")
    department : IndexedField(str, default="", description="Department name")
    primary_location : IndexedField(str, default="", description="Primary office location")
    employee_id : UniqueField(str, default=None, description="Employee ID number")

    # Explicitly set the label
    __label__: ClassVar[str] = "Person"


class Account(SourcedNode):
    """Account model representing user accounts across different services.

    Accounts must be associated with a Person using the HAS_ACCOUNT relationship.
    This is enforced at the application level when creating accounts.
    """

    username : IndexedField(str, description="Username on the service")
    email : IndexedField(str, description="Email associated with the account")
    service: SERVICE = Field(description="Service type (e.g., JIRA, Slack)")
    person_id: UUID = Field(description="Reference to the associated Person")
    display_name: str = Field(default="", description="Display name on the service")
    avatar_url: str = Field(default="", description="URL to avatar/profile image")
    last_active: DateTime = Field(
        default_factory=lambda: DateTime.from_native(datetime.now()),
        description="Last activity timestamp",
    )
    profile_url: Optional[str] = Field(default=None, description="URL to user profile")
    account_id : UniqueField(str, default=None, description="Service-specific ID (unique identifier)")
    is_primary: bool = Field(default=False, description="Whether this is the primary account")

    # Explicitly set the label
    __label__: ClassVar[str] = "Account"

    @model_validator(mode="after")
    def validate_person_id(self):
        """Validate that the account has a person_id."""
        if not getattr(self, "person_id", None):
            raise ValueError("Account must be associated with a Person (person_id is required)")
        return self


class Team(SourcedNode):
    """Team node representing a group of people working together with source tracking."""

    name : UniqueField(str, description="Team name (unique identifier)")
    description: Optional[str] = Field(default=None, description="Team description")
    department : IndexedField(str, default=None, description="Department name")
    formation_date: Optional[Date] = Field(default=None, description="Date when team was formed")

    # Explicitly set the label
    __label__: ClassVar[str] = "Team"


class Project(SourcedNode):
    """Project node representing a business initiative with source tracking."""

    name : UniqueField(str, description="Project name (unique identifier)")
    description: Optional[str] = Field(default=None, description="Project description")
    start_date: Optional[Date] = Field(default=None, description="Project start date")
    end_date: Optional[Date] = Field(default=None, description="Project end date")
    budget: Optional[float] = Field(default=None, description="Project budget")
    status : IndexedField(str, default="planning", description="Current project status")

    # Explicitly set the label
    __label__: ClassVar[str] = "Project"


class ConfluenceEntity(SourcedNode):
    """Base model for all Confluence entities."""

    confluence_id : UniqueField(str, description="Confluence's internal ID (unique identifier)")
    url: str = Field(description="URL to the entity")
    creator_username : IndexedField(str, description="Username of the creator")
    created_at: DateTime = Field(
        default_factory=lambda: DateTime.from_native(datetime.now()),
        description="Creation timestamp",
    )
    updated_at: Optional[DateTime] = Field(default=None, description="Last update timestamp")

    # Customize Neo4j label to include type
    def __init_subclass__(cls, **kwargs):
        """Register subclasses with customized labels."""
        super().__init_subclass__(**kwargs)
        # Get class name without "Confluence" prefix
        short_name = cls.__name__
        if short_name.startswith("Confluence"):
            short_name = short_name[len("Confluence") :]
        # Set label to Confluence:TypeName
        cls.__label__ = f"Confluence:{short_name}"


class ConfluenceSpace(ConfluenceEntity):
    """Confluence space model."""

    key : UniqueField(str, description="Confluence space key (unique identifier)")
    name : IndexedField(str, description="Space name")
    description: str = Field(default="", description="Space description")
    type : IndexedField(str, default="global", description="Space type (global, personal, etc.)")
    is_archived: bool = Field(default=False, description="Whether the space is archived")


class ConfluencePage(ConfluenceEntity):
    """Confluence page/document model."""

    title : IndexedField(str, description="Page title")
    content: str = Field(description="Page content")
    space_key : IndexedField(str, description="Key of the space containing this page")
    version: int = Field(default=1, description="Page version number")
    parent_id : IndexedField(str, default=None, description="Parent page ID")
    last_modifier_username : IndexedField(str, default=None, description="Username of last modifier")
    tags: list[str] = Field(default=[], description="Page tags")
    is_draft: bool = Field(default=False, description="Whether this is a draft")


class ConfluenceComment(ConfluenceEntity):
    """Comment on a Confluence page."""

    content: str = Field(description="Comment content")
    page_id : IndexedField(str, description="ID of the page being commented on")
    parent_comment_id : IndexedField(str, default=None, description="Parent comment ID")


class ConfluenceAttachment(ConfluenceEntity):
    """File attached to a Confluence page."""

    filename : IndexedField(str, description="Attachment filename")
    media_type : IndexedField(str, description="MIME type")
    file_size: int = Field(description="File size in bytes")
    page_id : IndexedField(str, description="ID of the page with the attachment")
    download_url: str = Field(description="URL to download the attachment")


# Relationships
class WORKS_ON(SourcedRelationship):
    """Relationship between Person and Project with source tracking."""

    role : IndexedField(str, description="Role on the project")
    joined_date: Optional[Date] = Field(default=None, description="Date joined the project")
    allocation_percentage: float = Field(default=100.0, description="Percentage of time allocated")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "WORKS_ON"


class BELONGS_TO(SourcedRelationship):
    """Relationship between Person and Team with source tracking."""

    role : IndexedField(str, default=None, description="Role in the team")
    joined_date: Optional[Date] = Field(default=None, description="Date joined the team")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "BELONGS_TO"


class MANAGES(SourcedRelationship):
    """Management relationship between Person and Team/Project with source tracking."""

    since: Optional[Date] = Field(default=None, description="Date since managing")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "MANAGES"


class HAS_ACCOUNT(SourcedRelationship):
    """Relationship between Person and Account."""

    is_primary: bool = Field(
        default=False, index=True, description="Whether this is the primary account"
    )
    verified: bool = Field(default=False, description="Whether the account is verified")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "HAS_ACCOUNT"


class AUTHORED(SourcedRelationship):
    """Content authored by a user relationship."""

    timestamp: DateTime = Field(
        default_factory=lambda: DateTime.from_native(datetime.now()),
        description="Authoring timestamp",
    )

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "AUTHORED"


class MODIFIED(SourcedRelationship):
    """Content modified by a user relationship."""

    timestamp: DateTime = Field(
        default_factory=lambda: DateTime.from_native(datetime.now()),
        description="Modification timestamp",
    )
    version : IndexedField(int, default=1, description="Version number")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "MODIFIED"


class PARENT_OF(SourcedRelationship):
    """Parent-child relationship between pages or comments."""

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "PARENT_OF"


class HAS_ATTACHMENT(SourcedRelationship):
    """Relationship between page and attachment."""

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "HAS_ATTACHMENT"


class MENTIONED_IN(SourcedRelationship):
    """User/entity mentioned in content."""

    context: str = Field(default="", description="Surrounding text for context")

    # Explicitly set the relationship type
    __type__: ClassVar[str] = "MENTIONED_IN"
