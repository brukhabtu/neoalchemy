"""
Unit tests for source tracking functionality.

These tests verify that the source tracking components work correctly
without requiring a Neo4j database connection.
"""

import pytest
from uuid import UUID, uuid4

from neoalchemy import initialize
from neoalchemy.orm.tracking.sources import Source, SOURCED_FROM, SourceScheme
from neoalchemy.orm.models import Node, Relationship


# Create a test model with source tracking
class TestNode(Node):
    """Test node class for source tracking tests."""
    name: str
    value: int


class TestRelationship(Relationship):
    """Test relationship class for source tracking tests."""
    type: str


class TestSource:
    """Test Source model and source tracking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        initialize()
    
    def test_source_scheme_enum(self):
        """Test that SourceScheme enum contains expected values."""
        # Standard schemes
        assert SourceScheme.JIRA == "jira"
        assert SourceScheme.GITHUB == "github"
        assert SourceScheme.LLM == "llm"
        assert SourceScheme.CUSTOM == "custom"
        
        # Check that we can convert strings to enum values
        assert SourceScheme("jira") == SourceScheme.JIRA
        assert SourceScheme("github") == SourceScheme.GITHUB
        
        # Check total number of schemes
        assert len(list(SourceScheme)) >= 10  # We should have at least 10 schemes
    
    def test_source_model_fields(self):
        """Test that Source model has expected fields."""
        # Create a source with required fields
        source = Source(
            uri="jira:ABC-123",
            scheme=SourceScheme.JIRA,
            identifier="ABC-123",
            name="JIRA Issue"
        )
        
        # Check that the required fields are set correctly
        assert source.uri == "jira:ABC-123"
        assert source.scheme == SourceScheme.JIRA
        assert source.identifier == "ABC-123"
        assert source.name == "JIRA Issue"
        
        # Optional fields should have default values
        assert source.description is None
        assert source.url is None
        assert source.timestamp is not None  # Should have a default timestamp
        
        # Check Neo4j label
        assert Source.__label__ == "Source"
    
    def test_sourced_from_relationship(self):
        """Test SOURCED_FROM relationship type."""
        # Create a relationship
        rel = SOURCED_FROM(context="Test context")
        
        # Check relationship type
        assert SOURCED_FROM.__type__ == "SOURCED_FROM"
        
        # Check that fields are set
        assert rel.context == "Test context"
        assert rel.timestamp is not None
    
    def test_source_from_uri_method(self):
        """Test the from_uri static method for creating sources."""
        # Create a source from a JIRA URI
        source = Source.from_uri("jira:ABC-123")
        
        # Check that fields are set correctly
        assert source.uri == "jira:ABC-123"
        assert source.scheme == SourceScheme.JIRA
        assert source.identifier == "ABC-123"
        assert source.name == "Jira ABC-123"  # Default name
        
        # Create with custom name and description
        source = Source.from_uri(
            "github:user/repo#123",
            name="GitHub Issue",
            description="Pull request from user",
            url="https://github.com/user/repo/issues/123"
        )
        
        # Check additional fields
        assert source.uri == "github:user/repo#123"
        assert source.scheme == SourceScheme.GITHUB
        assert source.identifier == "user/repo#123"
        assert source.name == "GitHub Issue"  # Custom name
        assert source.description == "Pull request from user"
        assert source.url == "https://github.com/user/repo/issues/123"
    
    def test_source_from_uri_with_custom_scheme(self):
        """Test creating a source with a custom scheme."""
        # Create a source with a non-standard scheme
        source = Source.from_uri("custom-system:12345")
        
        # Should use CUSTOM scheme for unknown schemes
        assert source.uri == "custom-system:12345"
        assert source.scheme == SourceScheme.CUSTOM
        assert source.identifier == "12345"
        
        # Name should still be generated correctly
        assert "custom-system" in source.name.lower()
        assert "12345" in source.name
    
    def test_validate_source_uri(self):
        """Test the validate_source_uri method."""
        # Valid URIs with standard schemes
        assert Source.validate_source_uri("jira:ABC-123") is True
        assert Source.validate_source_uri("github:user/repo") is True
        assert Source.validate_source_uri("llm:claude-3") is True
        
        # Valid URIs with custom schemes
        assert Source.validate_source_uri("custom:anything") is True
        assert Source.validate_source_uri("my-system:12345") is True
        
        # Invalid URIs
        assert Source.validate_source_uri("not-a-uri") is False
        assert Source.validate_source_uri("") is False
        assert Source.validate_source_uri(":missing-scheme") is False
        assert Source.validate_source_uri(123) is False  # Not a string
        assert Source.validate_source_uri(None) is False
        
        # Edge cases
        assert Source.validate_source_uri(":") is False  # Empty scheme and identifier
        assert Source.validate_source_uri("scheme:") is True  # Empty identifier is allowed
    
    def test_source_uri_parsing(self):
        """Test the parse_uri method."""
        # Parse a standard URI
        uri, identifier, scheme = Source.parse_uri("jira:ABC-123")
        assert uri == "jira:ABC-123"
        assert identifier == "ABC-123"
        assert scheme == SourceScheme.JIRA
        
        # Parse a URI with a custom scheme
        uri, identifier, scheme = Source.parse_uri("custom-system:xyz")
        assert uri == "custom-system:xyz"
        assert identifier == "xyz"
        assert scheme == SourceScheme.CUSTOM
        
        # Parse a URI with a complex identifier
        uri, identifier, scheme = Source.parse_uri("github:org/repo/pull/123")
        assert uri == "github:org/repo/pull/123"
        assert identifier == "org/repo/pull/123"
        assert scheme == SourceScheme.GITHUB
        
        # Invalid URI should raise ValueError
        with pytest.raises(ValueError):
            Source.parse_uri("invalid-no-colon")
    
    @pytest.mark.skip(reason="Source tracking fields not yet implemented in base models")
    def test_node_with_sources(self):
        """Test creating a node with sources."""
        # This test will be enabled when source tracking is added to base models
        pass
    
    @pytest.mark.skip(reason="Source tracking fields not yet implemented in base models") 
    def test_relationship_with_sources(self):
        """Test creating a relationship with sources."""
        # This test will be enabled when source tracking is added to base models
        pass


@pytest.mark.skip(reason="Source tracking fields not yet implemented in base models")
class TestNodeWithSources:
    """Test Neo4jModel base class integration with sources."""
    
    def test_sources_default_empty_list(self):
        """Test that sources field defaults to an empty list."""
        # This test will be enabled when source tracking is added to base models
        pass
    
    def test_sources_validation(self):
        """Test sources field validation."""
        # This test will be enabled when source tracking is added to base models
        pass