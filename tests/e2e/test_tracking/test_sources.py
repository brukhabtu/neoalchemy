"""
End-to-end tests for source tracking functionality.

These tests require a running Neo4j database with the following connection parameters:
- URL: bolt://localhost:7687
- User: neo4j
- Password: password (or set by NEO4J_PASSWORD environment variable)
"""

import pytest
from uuid import uuid4
from typing import List, Optional

from pydantic import Field
from neo4j.time import DateTime

from neoalchemy import initialize
from neoalchemy.orm.tracking.sources import Source, SOURCED_FROM, SourceScheme
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.fields import UniqueField, IndexedField


# Test models
class SourcedItem(Node):
    """Test node with sources for e2e testing."""
    sku: UniqueField(str, description="Stock keeping unit")
    name: str = Field(description="Item name")
    category: IndexedField(str, description="Item category")
    tags: List[str] = Field(default_factory=list)


class SourcedPerson(Node):
    """Test person node with sources for e2e testing."""
    email: UniqueField(str, description="Email address")
    name: str = Field(description="Person name")
    department: IndexedField(str, description="Department")


class OWNS(Relationship):
    """Test relationship with sources for e2e testing."""
    since: str = Field(description="When the ownership started")
    notes: Optional[str] = Field(default=None)


@pytest.mark.e2e
def test_source_creation(repo, clean_db):
    """Test creating Source nodes in the database."""
    initialize()
    
    with repo.transaction() as tx:
        # Create source directly
        jira_source = Source(
            uri="jira:TEST-123",
            scheme=SourceScheme.JIRA,
            identifier="TEST-123",
            name="Test Task",
            description="A test task for e2e testing"
        )
        created_source = tx.create(jira_source)
        
        # Create source using from_uri
        github_source = Source.from_uri(
            "github:neoalchemy/test#45",
            name="GitHub Issue",
            description="Test issue in GitHub",
            url="https://github.com/neoalchemy/test/issues/45"
        )
        created_github = tx.create(github_source)
        
        # Verify sources were created
        sources = tx.query(Source).find()
        assert len(sources) == 2
        
        # Verify source content
        jira = [s for s in sources if s.scheme == SourceScheme.JIRA][0]
        assert jira.uri == "jira:TEST-123"
        assert jira.identifier == "TEST-123"
        assert jira.name == "Test Task"
        assert jira.description == "A test task for e2e testing"
        
        github = [s for s in sources if s.scheme == SourceScheme.GITHUB][0]
        assert github.uri == "github:neoalchemy/test#45"
        assert github.identifier == "neoalchemy/test#45"
        assert github.name == "GitHub Issue"
        assert github.description == "Test issue in GitHub"
        assert github.url == "https://github.com/neoalchemy/test/issues/45"
        
        # Test finding by URI
        found_github = tx.query(Source).where(uri="github:neoalchemy/test#45").find_one()
        assert found_github is not None
        assert found_github.name == "GitHub Issue"
        
        # Test finding by scheme
        jira_sources = tx.query(Source).where(scheme=SourceScheme.JIRA).find()
        assert len(jira_sources) == 1
        assert jira_sources[0].uri == "jira:TEST-123"


@pytest.mark.e2e
def test_entity_with_sources(repo, clean_db):
    """Test creating entities with source URIs and linking them to Source nodes."""
    initialize()
    
    with repo.transaction() as tx:
        # Create an item with sources
        item = SourcedItem(
            sku=f"ITEM-{uuid4().hex[:8]}",
            name="Test Item",
            category="Test",
            tags=["test", "sample"],
            sources=["jira:ITEM-123", "github:neoalchemy/test#42"]
        )
        created_item = tx.create(item)
        
        # Sources list should be preserved
        assert len(created_item.sources) == 2
        assert "jira:ITEM-123" in created_item.sources
        assert "github:neoalchemy/test#42" in created_item.sources
        
        # Source nodes should be created automatically
        sources = tx.query(Source).find()
        assert len(sources) == 2
        
        source_uris = [s.uri for s in sources]
        assert "jira:ITEM-123" in source_uris
        assert "github:neoalchemy/test#42" in source_uris
        
        # Verify SOURCED_FROM relationships
        item_sources = tx.get_sources(created_item)
        assert len(item_sources) == 2
        
        source_uris = [s.uri for s in item_sources]
        assert "jira:ITEM-123" in source_uris
        assert "github:neoalchemy/test#42" in source_uris


@pytest.mark.e2e
def test_updating_sources(repo, clean_db):
    """Test adding sources to an existing entity."""
    initialize()
    
    with repo.transaction() as tx:
        # Create an item with one source
        item = SourcedItem(
            sku=f"ITEM-{uuid4().hex[:8]}",
            name="Test Item",
            category="Test",
            sources=["jira:ITEM-123"]
        )
        created_item = tx.create(item)
        
        # Add another source
        created_item.sources.append("github:neoalchemy/test#42")
        updated_item = tx.update(created_item)
        
        # Create relationship for the new source
        tx.relate_to_source(updated_item, "github:neoalchemy/test#42")
        
        # Verify sources
        assert len(updated_item.sources) == 2
        assert "jira:ITEM-123" in updated_item.sources
        assert "github:neoalchemy/test#42" in updated_item.sources
        
        # Verify source nodes
        sources = tx.query(Source).find()
        assert len(sources) == 2
        
        # Verify SOURCED_FROM relationships
        item_sources = tx.get_sources(updated_item)
        assert len(item_sources) == 2
        
        source_uris = [s.uri for s in item_sources]
        assert "jira:ITEM-123" in source_uris
        assert "github:neoalchemy/test#42" in source_uris


@pytest.mark.e2e
def test_relationship_with_sources(repo, clean_db):
    """Test creating relationships with source URIs."""
    initialize()
    
    with repo.transaction() as tx:
        # Create a person and an item
        person = SourcedPerson(
            email=f"test-{uuid4().hex[:8]}@example.com",
            name="Test Person",
            department="Testing",
            sources=["salesforce:person-123"]
        )
        created_person = tx.create(person)
        
        item = SourcedItem(
            sku=f"ITEM-{uuid4().hex[:8]}",
            name="Test Item",
            category="Test",
            sources=["jira:ITEM-456"]
        )
        created_item = tx.create(item)
        
        # Create a relationship with sources
        owns = OWNS(
            since="2025-04-19",
            notes="Test relationship",
            sources=["crm:purchase-789"]
        )
        tx.relate(created_person, owns, created_item)
        
        # Verify sources in the database
        sources = tx.query(Source).find()
        assert len(sources) == 3
        
        source_uris = [s.uri for s in sources]
        assert "salesforce:person-123" in source_uris
        assert "jira:ITEM-456" in source_uris
        assert "crm:purchase-789" in source_uris


@pytest.mark.e2e
def test_finding_by_source(repo, clean_db):
    """Test finding entities by source URI or scheme."""
    initialize()
    
    with repo.transaction() as tx:
        # Create multiple items with different sources
        item1 = SourcedItem(
            sku=f"ITEM1-{uuid4().hex[:8]}",
            name="Item 1",
            category="Category A",
            sources=["jira:ITEM-123", "github:test#1"]
        )
        created_item1 = tx.create(item1)
        
        item2 = SourcedItem(
            sku=f"ITEM2-{uuid4().hex[:8]}",
            name="Item 2",
            category="Category B",
            sources=["jira:ITEM-456"]
        )
        created_item2 = tx.create(item2)
        
        item3 = SourcedItem(
            sku=f"ITEM3-{uuid4().hex[:8]}",
            name="Item 3",
            category="Category A",
            sources=["github:test#2", "slack:channel-general"]
        )
        created_item3 = tx.create(item3)
        
        # Test find_by_source
        jira_123_items = tx.find_by_source(SourcedItem, "jira:ITEM-123")
        assert len(jira_123_items) == 1
        assert jira_123_items[0].name == "Item 1"
        
        slack_items = tx.find_by_source(SourcedItem, "slack:channel-general")
        assert len(slack_items) == 1
        assert slack_items[0].name == "Item 3"
        
        # Test find_by_source_scheme
        jira_items = tx.find_by_source_scheme(SourcedItem, "jira")
        assert len(jira_items) == 2
        names = [item.name for item in jira_items]
        assert "Item 1" in names
        assert "Item 2" in names
        
        github_items = tx.find_by_source_scheme(SourcedItem, "github")
        assert len(github_items) == 2
        names = [item.name for item in github_items]
        assert "Item 1" in names
        assert "Item 3" in names


@pytest.mark.e2e
def test_source_with_additional_data(repo, clean_db):
    """Test creating sources with additional metadata and accessing it."""
    initialize()
    
    with repo.transaction() as tx:
        # Create a source with additional data
        llm_source = Source.from_uri(
            "llm:claude-3",
            name="Claude 3 Sonnet",
            description="Language model inference",
            url="https://www.anthropic.com/claude",
            model_version="claude-3-sonnet-20240229",
            confidence=0.92
        )
        created_source = tx.create(llm_source)
        
        # Create an item using this source
        item = SourcedItem(
            sku=f"ITEM-{uuid4().hex[:8]}",
            name="AI Generated Content",
            category="Content",
            sources=["llm:claude-3"]
        )
        created_item = tx.create(item)
        
        # Relate with context
        tx.relate(
            created_item,
            SOURCED_FROM(context="Generated product description"),
            created_source
        )
        
        # Verify source
        found_source = tx.query(Source).where(uri="llm:claude-3").find_one()
        assert found_source is not None
        assert found_source.name == "Claude 3 Sonnet"
        assert found_source.description == "Language model inference"
        assert found_source.url == "https://www.anthropic.com/claude"
        
        # Additional properties should be accessible
        assert hasattr(found_source, "model_version")
        assert found_source.model_version == "claude-3-sonnet-20240229"
        assert hasattr(found_source, "confidence")
        assert found_source.confidence == 0.92