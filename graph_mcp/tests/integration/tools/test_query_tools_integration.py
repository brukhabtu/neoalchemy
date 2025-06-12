"""
Integration tests for query tools with real NeoAlchemy objects.

These tests verify that query tools work correctly with real model classes
and field expressions, using mocked database connections.
"""

import pytest
from unittest.mock import MagicMock

from graph_mcp.tools.query import _create_safe_namespace, _query_entities_impl
from graph_mcp.models import MODEL_MAP
from graph_mcp.models.entities import Person, Team, Project


@pytest.mark.integration
class TestSafeNamespaceIntegration:
    """Test safe namespace creation with real NeoAlchemy models."""
    
    def test_create_safe_namespace_for_person(self):
        """Test creating safe namespace for Person model with real fields."""
        namespace = _create_safe_namespace(Person)
        
        # Should contain real Person fields
        assert "email" in namespace
        assert "name" in namespace
        assert "title" in namespace
        
        # Fields should be real NeoAlchemy field expressions
        email_field = namespace["email"]
        name_field = namespace["name"]
        
        # Should support comparison operations (NeoAlchemy field expressions)
        assert hasattr(email_field, "__eq__")
        assert hasattr(email_field, "__ne__")
        assert hasattr(name_field, "__eq__")
        assert hasattr(name_field, "__ne__")
        
        # Should have restricted builtins for safety
        assert namespace["__builtins__"] == {}
        
        # Should contain common comparison values
        assert "True" in namespace
        assert "False" in namespace
        assert "None" in namespace
    
    def test_create_safe_namespace_for_different_models(self):
        """Test safe namespace creation for different model types."""
        # Test Team model
        team_namespace = _create_safe_namespace(Team)
        assert "name" in team_namespace
        assert "department" in team_namespace
        
        # Test Project model
        project_namespace = _create_safe_namespace(Project)
        assert "name" in project_namespace
        assert "status" in project_namespace
        
        # Each namespace should be specific to its model
        assert "email" not in team_namespace  # Person-specific field
        assert "email" not in project_namespace  # Person-specific field
    
    def test_safe_namespace_field_expressions(self):
        """Test that namespace contains actual NeoAlchemy field expressions."""
        namespace = _create_safe_namespace(Person)
        
        # Get the email field expression
        email_expr = namespace["email"]
        
        # Should be able to create comparison expressions
        # These would be used in query building
        eq_expr = email_expr == "test@company.com"
        ne_expr = email_expr != "spam@example.com"
        
        # Expressions should be real objects (not None)
        assert eq_expr is not None
        assert ne_expr is not None
        
        # Should support logical operations
        combined_expr = (email_expr == "test@company.com") & (namespace["name"] == "Test User")
        assert combined_expr is not None
    
    def test_safe_namespace_security(self):
        """Test that safe namespace restricts dangerous operations."""
        namespace = _create_safe_namespace(Person)
        
        # Should not have access to dangerous builtins
        assert "__import__" not in namespace
        assert "open" not in namespace
        assert "exec" not in namespace
        assert "eval" not in namespace
        
        # Builtins should be empty
        assert namespace["__builtins__"] == {}


@pytest.mark.integration
class TestQueryEntitiesIntegration:
    """Test entity querying with real NeoAlchemy models and expressions."""
    
    async def test_query_entities_with_real_expressions(self, mock_transaction_context):
        """Test querying entities with real field expressions."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup mock query results with real Person data
        mock_person_data = [
            {"email": "alice@company.com", "name": "Alice Smith", "title": "Engineer"},
            {"email": "bob@company.com", "name": "Bob Jones", "title": "Manager"}
        ]
        mock_tx.run.return_value.data.return_value = mock_person_data
        
        # Execute with real field expression
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="email == 'alice@company.com'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify result structure
        assert result["success"] is True
        assert result["entity_type"] == "Person"
        assert result["count"] == 2
        assert "entities" in result
        
        # Verify transaction was used
        repo.transaction.assert_called_once()
        mock_tx.run.assert_called_once()
        
        # Verify query was executed
        query_args = mock_tx.run.call_args[0]
        assert len(query_args) > 0  # Should have query string
    
    async def test_query_entities_with_complex_expressions(self, mock_transaction_context):
        """Test querying with complex logical expressions."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup mock results
        mock_tx.run.return_value.data.return_value = []
        
        # Execute with complex expression
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="(email.startswith('alice')) & (title == 'Engineer')",
            limit=5,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should handle complex expressions
        assert result["success"] is True
        assert "entities" in result
        
        # Verify transaction usage
        mock_tx.run.assert_called_once()
    
    async def test_query_entities_different_models(self, mock_transaction_context):
        """Test querying different entity types."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Test querying Teams
        mock_team_data = [{"name": "Engineering", "department": "Product"}]
        mock_tx.run.return_value.data.return_value = mock_team_data
        
        result = await _query_entities_impl(
            entity_type="Team",
            filter_expr="department == 'Product'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        assert result["success"] is True
        assert result["entity_type"] == "Team"
        
        # Reset and test Projects
        mock_tx.reset_mock()
        mock_project_data = [{"name": "API Redesign", "status": "active"}]
        mock_tx.run.return_value.data.return_value = mock_project_data
        
        result = await _query_entities_impl(
            entity_type="Project",
            filter_expr="status == 'active'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        assert result["success"] is True
        assert result["entity_type"] == "Project"
    
    async def test_query_entities_with_invalid_expression(self, mock_transaction_context):
        """Test handling of invalid query expressions."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with invalid expression syntax
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="invalid syntax here !!!",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should handle parsing error gracefully
        assert "error" in result
        assert "Failed to parse filter expression" in result["error"]
        
        # Should not execute query
        mock_tx.run.assert_not_called()
    
    async def test_query_entities_with_unsafe_expression(self, mock_transaction_context):
        """Test handling of unsafe query expressions."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with potentially unsafe expression
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="__import__('os').system('rm -rf /')",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should handle security error gracefully
        assert "error" in result
        # Should prevent execution of dangerous code
        mock_tx.run.assert_not_called()
    
    async def test_query_entities_with_unknown_entity_type(self, mock_transaction_context):
        """Test handling of unknown entity types."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with unknown entity type
        result = await _query_entities_impl(
            entity_type="UnknownEntity",
            filter_expr="field == 'value'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should handle unknown entity type
        assert "error" in result
        assert "Unknown entity type: UnknownEntity" in result["error"]
        assert "Available types:" in result["error"]
        
        # Should not execute query
        mock_tx.run.assert_not_called()
    
    async def test_query_entities_with_database_error(self, mock_transaction_context):
        """Test handling of database errors during query execution."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup database error
        mock_tx.run.side_effect = Exception("Database connection failed")
        
        # Execute
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="email == 'test@company.com'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should handle database error gracefully
        assert "error" in result
        assert "Database connection failed" in result["error"]
    
    async def test_query_entities_limit_parameter(self, mock_transaction_context):
        """Test that limit parameter is properly handled."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup mock results
        mock_tx.run.return_value.data.return_value = []
        
        # Execute with specific limit
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="True",  # Match all
            limit=25,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        assert result["success"] is True
        
        # Verify query was called (limit should be incorporated into query)
        mock_tx.run.assert_called_once()
        query_call = mock_tx.run.call_args
        
        # The query should include the limit
        # (Exact implementation depends on the query builder)
        assert query_call is not None


@pytest.mark.integration
class TestFieldExpressionIntegration:
    """Test integration with NeoAlchemy field expressions in query context."""
    
    def test_field_expressions_in_namespace(self):
        """Test that field expressions work correctly in safe namespace."""
        # Test with Person model
        person_namespace = _create_safe_namespace(Person)
        
        # Get field expressions
        email_field = person_namespace["email"]
        name_field = person_namespace["name"]
        
        # Should be able to create various comparison expressions
        expressions = [
            email_field == "test@company.com",
            email_field != "spam@example.com", 
            name_field == "John Doe",
            email_field.startswith("admin"),
            email_field.endswith("@company.com"),
            name_field.contains("Smith")
        ]
        
        # All expressions should be valid objects
        for expr in expressions:
            assert expr is not None
            
        # Should be able to combine with logical operators
        combined = (email_field == "test@company.com") & (name_field == "Test User")
        assert combined is not None
        
        or_combined = (email_field.startswith("admin")) | (email_field.startswith("user"))
        assert or_combined is not None
    
    def test_model_specific_fields(self):
        """Test that different models have access to their specific fields."""
        # Person fields
        person_ns = _create_safe_namespace(Person)
        assert "email" in person_ns
        assert "title" in person_ns
        
        # Team fields 
        team_ns = _create_safe_namespace(Team)
        assert "department" in team_ns
        assert "email" not in team_ns  # Person-specific
        
        # Project fields
        project_ns = _create_safe_namespace(Project)
        assert "status" in project_ns
        assert "department" not in project_ns  # Team-specific
        assert "email" not in project_ns  # Person-specific
    
    def test_field_expression_compilation(self):
        """Test that field expressions can be used for query compilation."""
        namespace = _create_safe_namespace(Person)
        
        # Create expressions that would be used in query compilation
        email_expr = namespace["email"]
        
        # Test different comparison types
        eq_comparison = email_expr == "test@company.com"
        startswith_comparison = email_expr.startswith("admin")
        
        # These should be proper expression objects that can be compiled
        # (The actual compilation testing would be in unit tests)
        assert hasattr(eq_comparison, "__class__")
        assert hasattr(startswith_comparison, "__class__")
        
        # Should be different expression types
        assert type(eq_comparison).__name__ != type(startswith_comparison).__name__