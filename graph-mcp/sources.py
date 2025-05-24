"""
Sources mechanism for tracking data lineage in Neo4j.

This module provides a way to track the origin of data in Neo4j nodes and relationships.
Every entity can have one or more associated data sources that represent external systems
from which the entity was created or updated.
"""

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, List, Optional, Type, Union
from uuid import UUID

from neo4j.time import DateTime
from pydantic import Field, model_validator

from neoalchemy.orm.models import Node, Relationship


class SourceType(str, Enum):
    """Types of business data sources."""

    ATLASSIAN_TEAMS = "attlasian_teams"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    SLACK = "slack"
    TEAMS = "teams"
    TEAMS_MEETING = "teams_meeting"
    EMAIL = "email"
    GITHUB = "github"
    GITLAB = "gitlab"
    JENKINS = "jenkins"
    SALESFORCE = "salesforce"
    ZENDESK = "zendesk"
    SPREADSHEET = "spreadsheet"
    DATABASE = "database"
    USER_INPUT = "user_input"
    LLM = "llm"  # LLM-inferred data
    OTHER = "other"


class Source(Node):
    """Node representing a data source for entities in the graph."""

    name: str
    type: SourceType
    description: Optional[str] = None
    url: Optional[str] = None
    identifier: Optional[str] = None  # e.g. Jira issue key, Confluence page ID
    timestamp: DateTime = Field(default_factory=lambda: DateTime.from_native(datetime.now()))

    # Custom Neo4j label
    __label__: ClassVar[str] = "Source"


class SOURCED_FROM(Relationship):
    """Relationship connecting an entity to its data source."""

    import_timestamp: DateTime = Field(default_factory=lambda: DateTime.from_native(datetime.now()))
    method: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0 score of confidence in this source
    primary: bool = False  # Whether this is the primary source for the entity
    context: Optional[str] = None  # Additional context about how data was extracted
    notes: Optional[str] = None


class SourcedNode(Node):
    """Base class for Neo4j nodes that require at least one source."""

    # Sources is an array of source IDs
    sources: List[UUID] = []

    # Explicitly set label to None so subclasses use their own class name
    __label__: ClassVar[Optional[str]] = None

    def __init_subclass__(cls, **kwargs):
        """Register subclasses with proper label inheritance."""
        super().__init_subclass__(**kwargs)

        # If the subclass doesn't explicitly set __label__, use the class name
        if cls.__label__ is None:
            cls.__label__ = cls.__name__

    @model_validator(mode="after")
    def validate_sources(self):
        """Validate that the node has at least one source."""
        if not getattr(self, "sources", None):
            raise ValueError(f"{self.__class__.__name__} requires at least one source")
        return self

    def add_source_id(self, source_id: UUID):
        """Add a source ID to this node."""
        if not hasattr(self, "sources") or self.sources is None:
            self.sources = []

        # Convert to string if it's a UUID
        source_id_str = str(source_id) if hasattr(source_id, "__str__") else source_id

        # Don't add duplicates
        if source_id_str not in self.sources:
            self.sources.append(source_id_str)

    def get_source_ids(self) -> List[str]:
        """Get the list of source IDs."""
        return self.sources if hasattr(self, "sources") and self.sources else []


class SourcedRelationship(Relationship):
    """Base class for Neo4j relationships that require at least one source."""

    # Sources is an array of source IDs
    sources: List[UUID] = []

    # Explicitly set type to None so subclasses use their own class name
    __type__: ClassVar[Optional[str]] = None

    def __init_subclass__(cls, **kwargs):
        """Register subclasses with proper type inheritance."""
        super().__init_subclass__(**kwargs)

        # If the subclass doesn't explicitly set __type__, use uppercase class name
        if cls.__type__ is None:
            cls.__type__ = cls.__name__.upper()

    @model_validator(mode="after")
    def validate_sources(self):
        """Validate that the relationship has at least one source."""
        if not getattr(self, "sources", None):
            raise ValueError(f"{self.__class__.__name__} requires at least one source")
        return self

    def add_source_id(self, source_id: UUID):
        """Add a source ID to this relationship."""
        if not hasattr(self, "sources") or self.sources is None:
            self.sources = []

        # Convert to string if it's a UUID
        source_id_str = str(source_id) if hasattr(source_id, "__str__") else source_id

        # Don't add duplicates
        if source_id_str not in self.sources:
            self.sources.append(source_id_str)

    def get_source_ids(self) -> List[str]:
        """Get the list of source IDs."""
        return self.sources if hasattr(self, "sources") and self.sources else []


# Extend the Neo4jTransaction class with source methods
class SourceMethods:
    """Mixin class adding source-related methods to Neo4jTransaction."""

    def add_source(
        self,
        entity: Any,
        source: Source,
        method: Optional[str] = None,
        confidence: float = 1.0,
        primary: bool = False,
        context: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SOURCED_FROM:
        """
        Add a source to an entity.

        Args:
            entity: The entity (Node or Relationship) to add the source to
            source: The Source object to associate with the entity
            method: Method used to extract from this source
            confidence: Confidence score (0.0 to 1.0)
            primary: Whether this is the primary source
            context: Contextual information about extraction
            notes: Additional notes about this source connection

        Returns:
            The created SOURCED_FROM relationship
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # Create the source if it doesn't exist
        created_source = tx.create(source) if not getattr(source, "id", None) else source

        # Create the relationship
        relationship = SOURCED_FROM(
            method=method, confidence=confidence, primary=primary, context=context, notes=notes
        )

        # Connect the entity to the source
        sourced_from = tx.relate(entity, relationship, created_source)

        # Add the source ID to the entity's sources list
        if hasattr(entity, "add_source_id"):
            entity.add_source_id(created_source.id)

            # Update the entity to persist the sources list
            tx.update(entity)

        return sourced_from

    def get_sources(self, entity: Any) -> List[Source]:
        """
        Get all sources for an entity.

        Args:
            entity: The entity to get sources for

        Returns:
            List of Source nodes
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        return tx.query(Source).related_from(entity, SOURCED_FROM).find()

    def get_primary_source(self, entity: Any) -> Optional[Source]:
        """
        Get the primary source for an entity.

        Args:
            entity: The entity to get the primary source for

        Returns:
            Primary Source node or None if no primary source exists
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        return (
            tx.query(Source)
            .related_from(entity, SOURCED_FROM, relationship_filter=SOURCED_FROM.primary == True)
            .find_one()
        )

    def find_entities_by_source(
        self, source: Source, entity_type: Type[Any], confidence_threshold: Optional[float] = None
    ) -> List[Any]:
        """
        Find all entities of a given type that come from a specific source.

        Args:
            source: Source to search for
            entity_type: Type of entities to return
            confidence_threshold: Optional minimum confidence threshold

        Returns:
            List of entities from the given source
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        query = tx.query(entity_type).related_to(source, SOURCED_FROM)

        # Add confidence filter if specified
        if confidence_threshold is not None:
            query = query.where(SOURCED_FROM.confidence >= confidence_threshold)

        return query.find()

    def create_source(
        self,
        name: str,
        type: Union[SourceType, str],
        description: Optional[str] = None,
        url: Optional[str] = None,
        identifier: Optional[str] = None,
    ) -> Source:
        """
        Create a Source node.

        Args:
            name: Source name
            type: Source type (can be SourceType enum or string)
            description: Optional description
            url: Optional URL
            identifier: Optional unique identifier for the source

        Returns:
            Created Source node
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # Convert string to enum if needed
        if isinstance(type, str):
            type = SourceType(type)

        source = Source(
            name=name, type=type, description=description, url=url, identifier=identifier
        )

        return tx.create(source)

    def create_llm_source(
        self,
        model_name: str,
        prompt_id: Optional[str] = None,
        description: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Source:
        """
        Create a Source node for LLM-inferred data.

        Args:
            model_name: Name of the LLM model (e.g., "gpt-4", "claude-3")
            prompt_id: Optional identifier for the prompt used
            description: Optional description of the inference
            confidence: Optional confidence score from the LLM (0.0 to 1.0)

        Returns:
            Created Source node
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # Format the name and description
        name = f"LLM: {model_name}"
        if description is None:
            description = f"Data inferred by {model_name}"
        if confidence is not None:
            description += f" (confidence: {confidence:.2f})"

        source = Source(
            name=name, type=SourceType.LLM, description=description, identifier=prompt_id
        )

        return tx.create(source)

    def create_with_source(
        self,
        entity: Any,
        source: Source,
        method: Optional[str] = None,
        confidence: float = 1.0,
        primary: bool = True,
        context: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Any:
        """
        Create an entity and immediately associate it with a source.

        This is a convenience method that combines create() and add_source()
        in a single operation.

        Args:
            entity: Entity to create
            source: Source to associate with the entity
            method: Method used to extract from this source
            confidence: Confidence score (0.0 to 1.0)
            primary: Whether this is the primary source
            context: Contextual information about extraction
            notes: Additional notes about this source connection

        Returns:
            The created entity
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # First create the source if it doesn't exist
        created_source = tx.create(source) if not getattr(source, "id", None) else source

        # Add the source ID to the entity's sources list
        if hasattr(entity, "add_source_id"):
            entity.add_source_id(created_source.id)

        # Create the entity
        created_entity = tx.create(entity)

        # Create the relationship
        relationship = SOURCED_FROM(
            method=method, confidence=confidence, primary=primary, context=context, notes=notes
        )

        # Connect the entity to the source
        tx.relate(created_entity, relationship, created_source)

        return created_entity

    def create_with_llm_source(
        self,
        entity: Any,
        model_name: str,
        method: str = "LLM Inference",
        confidence: float = 0.8,
        primary: bool = True,
        prompt_id: Optional[str] = None,
        context: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Any:
        """
        Create an entity and immediately associate it with an LLM source.

        This is a convenience method that combines create_llm_source() and create_with_source()
        in a single operation.

        Args:
            entity: Entity to create
            model_name: Name of the LLM model (e.g., "gpt-4", "claude-3")
            method: Method used to generate the entity (default: "LLM Inference")
            confidence: Confidence score (0.0 to 1.0)
            primary: Whether this is the primary source
            prompt_id: Optional identifier for the prompt used
            context: Contextual information about inference
            notes: Additional notes about this source connection

        Returns:
            The created entity
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # Create an LLM source
        llm_source = tx.create_llm_source(
            model_name=model_name, prompt_id=prompt_id, confidence=confidence
        )

        # Use the regular create_with_source method
        return tx.create_with_source(
            entity=entity,
            source=llm_source,
            method=method,
            confidence=confidence,
            primary=primary,
            context=context,
            notes=notes,
        )

    def relate_with_source(
        self,
        from_entity: Any,
        relationship: Any,
        to_entity: Any,
        source: Source,
        method: Optional[str] = None,
        confidence: float = 1.0,
        primary: bool = True,
        context: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Any:
        """
        Create a relationship and immediately associate it with a source.

        This is a convenience method that combines relate() and add_source()
        in a single operation.

        Args:
            from_entity: Source entity
            relationship: Relationship instance
            to_entity: Target entity
            source: Source to associate with the relationship
            method: Method used to extract from this source
            confidence: Confidence score (0.0 to 1.0)
            primary: Whether this is the primary source
            context: Contextual information about extraction
            notes: Additional notes about this source connection

        Returns:
            The created relationship
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # First create the source if it doesn't exist
        created_source = tx.create(source) if not getattr(source, "id", None) else source

        # Add the source ID to the relationship's sources list
        if hasattr(relationship, "add_source_id"):
            relationship.add_source_id(created_source.id)

        # Create the relationship
        created_rel = tx.relate(from_entity, relationship, to_entity)

        # Create the SOURCED_FROM relationship
        sourced_from = SOURCED_FROM(
            method=method, confidence=confidence, primary=primary, context=context, notes=notes
        )

        # Connect the relationship to the source
        # Note: We can't directly relate to a relationship in Neo4j,
        # so we're storing the source IDs in the relationship's properties

        return created_rel

    def relate_with_llm_source(
        self,
        from_entity: Any,
        relationship: Any,
        to_entity: Any,
        model_name: str,
        method: str = "LLM Inference",
        confidence: float = 0.8,
        primary: bool = True,
        prompt_id: Optional[str] = None,
        context: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Any:
        """
        Create a relationship and immediately associate it with an LLM source.

        This method is particularly useful for LLM-inferred relationships where
        an AI has detected or suggested a connection between entities.

        Args:
            from_entity: Source entity
            relationship: Relationship instance
            to_entity: Target entity
            model_name: Name of the LLM model (e.g., "gpt-4", "claude-3")
            method: Method used to infer the relationship (default: "LLM Inference")
            confidence: Confidence score (0.0 to 1.0)
            primary: Whether this is the primary source
            prompt_id: Optional identifier for the prompt used
            context: Contextual information about inference
            notes: Additional notes about this source connection

        Returns:
            The created relationship
        """
        # The 'self' here refers to the Neo4jTransaction instance
        tx = self

        # Create an LLM source
        llm_source = tx.create_llm_source(
            model_name=model_name, prompt_id=prompt_id, confidence=confidence
        )

        # Use the regular relate_with_source method
        return tx.relate_with_source(
            from_entity=from_entity,
            relationship=relationship,
            to_entity=to_entity,
            source=llm_source,
            method=method,
            confidence=confidence,
            primary=primary,
            context=context,
            notes=notes,
        )


# Function to extend Neo4jTransaction with source methods
def extend_transaction_with_sources():
    """
    Extend the Neo4jTransaction class with source-related methods.

    This function adds the source methods to the Neo4jTransaction class,
    allowing all transactions to work with sources.
    """
    from neoalchemy.orm.repository import Neo4jTransaction

    # Add source methods to Neo4jTransaction
    for method_name in dir(SourceMethods):
        # Skip private methods and properties
        if method_name.startswith("_"):
            continue

        # Get the method from SourceMethods
        method = getattr(SourceMethods, method_name)

        # Only add callable methods (not properties or variables)
        if callable(method):
            # Add the method to Neo4jTransaction if it doesn't already exist
            if not hasattr(Neo4jTransaction, method_name):
                setattr(Neo4jTransaction, method_name, method)


# Initialize the extensions
def initialize_sources():
    """
    Initialize the source mechanism by extending NeoAlchemy classes.

    This function should be called before using the source functionality.
    """
    extend_transaction_with_sources()
