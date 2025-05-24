"""
Source tracking functionality for NeoAlchemy.

This module provides components for tracking data lineage and provenance
in a Neo4j graph database using the NeoAlchemy ORM.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union, ClassVar, Dict, Type, Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from neo4j.time import DateTime
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.fields import UniqueField, IndexedField


class SourceScheme(str, Enum):
    """Supported URI schemes for source tracking."""
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GITHUB = "github"
    GITLAB = "gitlab"
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    SALESFORCE = "salesforce"
    ZENDESK = "zendesk"
    LLM = "llm"
    USER = "user"
    API = "api"
    DATABASE = "database"
    CUSTOM = "custom"


class Source(Node):
    """Node representing a data source in Neo4j."""
    __label__: ClassVar[str] = "Source"
    
    id: UUID = Field(default_factory=uuid4)
    uri: str = UniqueField(description="URI identifier (e.g., 'jira:ABC-123')")
    scheme: SourceScheme = IndexedField(description="Source type (e.g., 'jira', 'llm')")
    identifier: str = IndexedField(description="Source identifier part of the URI")
    name: str = Field(description="Display name for the source")
    description: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    timestamp: DateTime = Field(default_factory=lambda: DateTime.from_native(datetime.now()))
    
    @staticmethod
    def parse_uri(uri: str) -> tuple[str, str, SourceScheme]:
        """Parse a source URI into its components.
        
        Args:
            uri: Source URI in format "scheme:identifier"
            
        Returns:
            Tuple of (uri, identifier, scheme_enum)
            
        Raises:
            ValueError: If URI format is invalid
        """
        if ":" not in uri:
            raise ValueError(f"Invalid source URI format: {uri}. Expected format: scheme:identifier")
            
        scheme, identifier = uri.split(":", 1)
        
        # Try to map to known scheme, fallback to CUSTOM
        try:
            scheme_enum = SourceScheme(scheme)
        except ValueError:
            scheme_enum = SourceScheme.CUSTOM
            
        return uri, identifier, scheme_enum
    
    @classmethod
    def from_uri(cls, uri: str, name: Optional[str] = None, **kwargs) -> "Source":
        """Create a Source from a URI string.
        
        Args:
            uri: Source URI in format "scheme:identifier"
            name: Optional display name (defaults to capitalized scheme and identifier)
            **kwargs: Additional properties for the source
            
        Returns:
            Source instance
            
        Raises:
            ValueError: If URI format is invalid
        """
        uri, identifier, scheme_enum = cls.parse_uri(uri)
        
        # Generate a default name if not provided
        if name is None:
            scheme_str = scheme_enum.value if scheme_enum != SourceScheme.CUSTOM else uri.split(":", 1)[0]
            name = f"{scheme_str.title()} {identifier}"
            
        return cls(
            uri=uri,
            scheme=scheme_enum,
            identifier=identifier,
            name=name,
            **kwargs
        )
    
    @staticmethod
    def validate_source_uri(uri: str) -> bool:
        """Validate a source URI string.
        
        Args:
            uri: Source URI to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(uri, str) or ":" not in uri:
            return False
            
        scheme, _ = uri.split(":", 1)
        try:
            # Validate against known schemes
            SourceScheme(scheme)
            return True
        except ValueError:
            # Allow custom schemes
            return bool(scheme.strip())


class SOURCED_FROM(Relationship):
    """Relationship connecting an entity to its source."""
    __type__: ClassVar[str] = "SOURCED_FROM"
    
    timestamp: DateTime = Field(default_factory=lambda: DateTime.from_native(datetime.now()))
    context: Optional[str] = Field(default=None, description="Additional context about the source relationship")