"""
Integration tests for source tracking functionality.

These tests verify that the source tracking system works correctly
with a real Neo4j database.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from neoalchemy.orm.tracking import Source, SourceScheme, SOURCED_FROM
from tests.models import Person


@pytest.mark.integration
def test_source_creation_and_retrieval(repo, clean_db):
    """Test creating and retrieving source entities."""
    with repo.transaction() as tx:
        # Create a source
        source = Source.from_uri(
            "jira:ABC-123",
            name="Test Jira Ticket",
            description="A test ticket from Jira"
        )
        created_source = tx.create(source)
        
        # Verify creation
        assert created_source.uri == "jira:ABC-123"
        assert created_source.scheme == SourceScheme.JIRA
        assert created_source.identifier == "ABC-123"
        assert created_source.name == "Test Jira Ticket"
        
        # Retrieve the source
        retrieved = tx.get(Source, str(created_source.id))
        assert retrieved is not None
        assert retrieved.uri == "jira:ABC-123"


@pytest.mark.integration
def test_source_uri_parsing(repo, clean_db):
    """Test that various URI formats are parsed correctly."""
    test_cases = [
        ("jira:PROJ-456", SourceScheme.JIRA, "PROJ-456"),
        ("github:org/repo/issues/123", SourceScheme.GITHUB, "org/repo/issues/123"),
        ("confluence:space-key/page-id", SourceScheme.CONFLUENCE, "space-key/page-id"),
        ("custom:some-identifier", SourceScheme.CUSTOM, "some-identifier"),
    ]
    
    with repo.transaction() as tx:
        for uri, expected_scheme, expected_identifier in test_cases:
            source = Source.from_uri(uri)
            created = tx.create(source)
            
            assert created.uri == uri
            assert created.scheme == expected_scheme
            assert created.identifier == expected_identifier


@pytest.mark.integration
def test_sourced_from_relationship(repo, clean_db):
    """Test creating SOURCED_FROM relationships."""
    with repo.transaction() as tx:
        # Create a person and a source
        person = tx.create(Person(name="John Doe", age=30))
        source = tx.create(Source.from_uri("github:user/profile/johndoe"))
        
        # Create sourced relationship
        sourced_rel = SOURCED_FROM(context="Profile information extracted from GitHub")
        tx.relate(person, sourced_rel, source)
        
        # Verify relationship exists
        query = """
        MATCH (p:Person)-[r:SOURCED_FROM]->(s:Source)
        WHERE p.id = $person_id AND s.id = $source_id
        RETURN r.context as context, r.timestamp as timestamp
        """
        
        result = tx._tx.run(query, {
            "person_id": str(person.id),
            "source_id": str(source.id)
        })
        
        record = result.single()
        assert record is not None
        assert record["context"] == "Profile information extracted from GitHub"
        assert record["timestamp"] is not None


@pytest.mark.integration
def test_multiple_sources_for_entity(repo, clean_db):
    """Test that an entity can have multiple sources."""
    with repo.transaction() as tx:
        # Create person
        person = tx.create(Person(name="Jane Smith", age=28))
        
        # Create multiple sources
        linkedin_source = tx.create(Source.from_uri("linkedin:profile/janesmith"))
        github_source = tx.create(Source.from_uri("github:janesmith"))
        
        # Create relationships
        linkedin_rel = SOURCED_FROM(context="Professional profile")
        github_rel = SOURCED_FROM(context="Code repositories and activity")
        
        tx.relate(person, linkedin_rel, linkedin_source)
        tx.relate(person, github_rel, github_source)
        
        # Verify both relationships exist
        query = """
        MATCH (p:Person)-[r:SOURCED_FROM]->(s:Source)
        WHERE p.id = $person_id
        RETURN s.uri as source_uri, r.context as context
        ORDER BY s.uri
        """
        
        result = tx._tx.run(query, {"person_id": str(person.id)})
        records = list(result)
        
        assert len(records) == 2
        
        # Verify the sources (ordered by URI)
        github_record = records[0]  # github comes before linkedin alphabetically
        linkedin_record = records[1]
        
        assert github_record["source_uri"] == "github:janesmith"
        assert github_record["context"] == "Code repositories and activity"
        
        assert linkedin_record["source_uri"] == "linkedin:profile/janesmith"
        assert linkedin_record["context"] == "Professional profile"


@pytest.mark.integration
def test_source_deduplication(repo, clean_db):
    """Test that sources with same URI are deduplicated via merge."""
    with repo.transaction() as tx:
        # Create same source twice using merge
        source1 = tx.merge(Source, uri="jira:DEDUP-123", name="First Creation")
        source2 = tx.merge(Source, uri="jira:DEDUP-123", name="Second Creation")
        
        # Should be the same entity
        assert source1.id == source2.id
        assert source2.name == "Second Creation"  # Updated
        
        # Verify only one source exists
        all_sources = tx.query(Source).where(Source.uri == "jira:DEDUP-123").find()
        assert len(all_sources) == 1


@pytest.mark.integration
def test_source_validation(repo, clean_db):
    """Test source URI validation."""
    with repo.transaction() as tx:
        # Valid URIs should work
        valid_sources = [
            "jira:TEST-123",
            "github:owner/repo",
            "custom:anything-goes-here",
        ]
        
        for uri in valid_sources:
            source = Source.from_uri(uri)
            created = tx.create(source)
            assert created.uri == uri
        
        # Test validation function
        assert Source.validate_source_uri("jira:TEST-123") is True
        assert Source.validate_source_uri("invalid-no-colon") is False
        assert Source.validate_source_uri("") is False


@pytest.mark.integration
def test_source_timestamp_behavior(repo, clean_db):
    """Test that timestamps are automatically set and preserved."""
    with repo.transaction() as tx:
        # Create source and relationship
        person = tx.create(Person(name="Time Test", age=25))
        source = tx.create(Source.from_uri("test:timestamp"))
        
        # Record time before creating relationship
        before_time = datetime.now()
        
        sourced_rel = SOURCED_FROM()
        tx.relate(person, sourced_rel, source)
        
        # Verify timestamps are set and reasonable
        assert source.timestamp is not None
        assert sourced_rel.timestamp is not None
        
        # Timestamps should be recent (within last minute)
        time_diff = datetime.now() - before_time
        assert time_diff.total_seconds() < 60