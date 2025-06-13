"""
Integration tests for entity tools with real NeoAlchemy objects.

These tests verify that entity tools work correctly with real model instances
and repository objects, using mocked database connections.
"""

import pytest
from unittest.mock import MagicMock

from graph_mcp.tools.entities import _create_entity_impl
from graph_mcp.models.entities import Person, Team, Project


@pytest.mark.integration
class TestCreateEntityIntegration:
    """Test entity creation with real NeoAlchemy models and mocked database."""
    
    async def test_create_person_with_real_model_validation(self, mock_transaction_context, sample_entities, mock_model_map):
        """Test creating a Person with real Pydantic validation."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        # Create mock app context
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup mock transaction to return a person instance
        created_person = sample_entities["person"]
        mock_tx.create.return_value = created_person
        
        # Execute - Test real Pydantic validation
        properties = {
            "email": "Alice.Smith@Company.COM",  # Test email normalization
            "name": "  Alice Smith  ",  # Test name trimming
            "title": "Senior Engineer"
        }
        
        result = await _create_entity_impl("Person", properties, app_context, mock_model_map)
        
        # Verify result structure
        assert result["success"] is True
        assert result["entity_type"] == "Person"
        assert result["entity_id"] == "alice.smith@company.com"  # Normalized email
        
        # Verify real transaction was called
        mock_tx.create.assert_called_once()
        
        # Verify the created entity went through real Pydantic validation
        created_entity_arg = mock_tx.create.call_args[0][0]
        assert isinstance(created_entity_arg, Person)
        assert created_entity_arg.email == "alice.smith@company.com"  # Normalized
        assert created_entity_arg.name == "Alice Smith"  # Trimmed
        assert created_entity_arg.title == "Senior Engineer"
    
    async def test_create_team_with_real_validation(self, mock_transaction_context, mock_model_map):
        """Test creating a Team with real validation logic."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Create real Team instance for mock return
        team = Team(name="Engineering", department="Product")
        mock_tx.create.return_value = team
        
        # Execute
        properties = {
            "name": "Engineering",
            "department": "Product",
            "description": "Product engineering team"
        }
        
        result = await _create_entity_impl("Team", properties, app_context, mock_model_map)
        
        # Verify
        assert result["success"] is True
        assert result["entity_type"] == "Team"
        assert result["entity_id"] == "Engineering"
        
        # Verify real Team model was created
        created_entity_arg = mock_tx.create.call_args[0][0]
        assert isinstance(created_entity_arg, Team)
        assert created_entity_arg.name == "Engineering"
        assert created_entity_arg.department == "Product"
    
    async def test_create_entity_with_validation_error(self, mock_transaction_context, mock_model_map):
        """Test that real Pydantic validation errors are handled properly."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with invalid email (should trigger real Pydantic validation)
        properties = {
            "email": "not-an-email",  # Invalid email format
            "name": "John Doe"
        }
        
        result = await _create_entity_impl("Person", properties, app_context, mock_model_map)
        
        # Verify validation error is caught and handled
        assert "error" in result
        assert "validation error" in result["error"].lower()
        
        # Transaction should not be called due to validation failure
        mock_tx.create.assert_not_called()
    
    async def test_create_entity_with_unknown_type(self, mock_transaction_context, mock_model_map):
        """Test handling of unknown entity types."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with unknown entity type
        result = await _create_entity_impl("UnknownEntity", {}, app_context, mock_model_map)
        
        # Verify error handling
        assert "error" in result
        assert "Unknown entity type: UnknownEntity" in result["error"]
        assert "Available types:" in result["error"]
        
        # Should list available types from mock_model_map
        for entity_type in mock_model_map.keys():
            assert entity_type in result["error"]
    
    async def test_create_entity_with_database_error(self, mock_transaction_context, mock_model_map):
        """Test handling of database errors during entity creation."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup database error
        mock_tx.create.side_effect = Exception("Database connection failed")
        
        # Execute
        properties = {"email": "test@company.com", "name": "Test User"}
        result = await _create_entity_impl("Person", properties, app_context, mock_model_map)
        
        # Verify error is caught and handled
        assert "error" in result
        assert "Database connection failed" in result["error"]
    
    async def test_create_entity_primary_key_detection(self, mock_transaction_context, mock_model_map):
        """Test that primary key detection works for different entity types."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Test different entity types with their respective primary keys
        test_cases = [
            ("Person", {"email": "test@company.com", "name": "Test"}, "test@company.com"),
            ("Team", {"name": "TestTeam", "department": "Test"}, "TestTeam"),
            ("Project", {"name": "TestProject", "status": "active"}, "TestProject"),
        ]
        
        for entity_type, properties, expected_id in test_cases:
            # Create mock entity with the properties
            entity_class = mock_model_map[entity_type]
            mock_entity = entity_class.model_validate(properties)
            mock_tx.create.return_value = mock_entity
            
            # Execute
            result = await _create_entity_impl(entity_type, properties, app_context, mock_model_map)
            
            # Verify correct primary key extraction
            assert result["success"] is True
            assert result["entity_id"] == expected_id
            
            # Reset mock for next iteration
            mock_tx.reset_mock()


@pytest.mark.integration
class TestEntityModelIntegration:
    """Test integration between entity tools and real NeoAlchemy models."""
    
    def test_model_map_contains_expected_entities(self, mock_model_map):
        """Test that mock_model_map contains all expected entity types."""
        expected_entities = ["Person", "Team", "Project", "Service", "Repository", "Source"]
        
        for entity_type in expected_entities:
            assert entity_type in mock_model_map, f"Missing {entity_type} in mock_model_map"
            
            # Verify it's a real model class
            model_class = mock_model_map[entity_type]
            assert hasattr(model_class, "model_validate"), f"{entity_type} is not a Pydantic model"
    
    def test_all_models_have_valid_primary_keys(self, mock_model_map):
        """Test that all models in mock_model_map have valid primary key methods."""
        for entity_type, model_class in mock_model_map.items():
            # Each model should have a primary key
            primary_key = model_class.get_primary_key()
            assert primary_key is not None, f"{entity_type} has no primary key"
            assert isinstance(primary_key, str), f"{entity_type} primary key should be string"
            
            # Primary key should be a valid field in the model
            model_fields = model_class.model_fields
            assert primary_key in model_fields, f"{entity_type} primary key '{primary_key}' not in model fields"
    
    def test_model_validation_integration(self):
        """Test that models integrate properly with Pydantic validation."""
        # Test Person validation
        person_data = {"email": "test@company.com", "name": "Test User"}
        person = Person.model_validate(person_data)
        assert person.email == "test@company.com"
        assert person.name == "Test User"
        
        # Test Team validation
        team_data = {"name": "TestTeam", "department": "Engineering"}
        team = Team.model_validate(team_data)
        assert team.name == "TestTeam"
        assert team.department == "Engineering"
        
        # Test Project validation
        project_data = {"name": "TestProject", "status": "active"}
        project = Project.model_validate(project_data)
        assert project.name == "TestProject"
        assert project.status == "active"


@pytest.mark.integration  
class TestTransactionIntegration:
    """Test integration with NeoAlchemy transaction management."""
    
    async def test_transaction_context_integration(self, mock_transaction_context, mock_model_map):
        """Test that entity tools integrate properly with transaction contexts."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Create a real Person instance for the mock
        person = Person(email="test@company.com", name="Test User")
        mock_tx.create.return_value = person
        
        # Execute
        properties = {"email": "test@company.com", "name": "Test User"}
        result = await _create_entity_impl("Person", properties, app_context, mock_model_map)
        
        # Verify transaction context was used properly
        assert result["success"] is True
        
        # Verify the repository transaction method was called
        repo.transaction.assert_called_once()
        
        # Verify the transaction create method was called
        mock_tx.create.assert_called_once()
        
        # Verify a real Person instance was passed to create
        created_entity = mock_tx.create.call_args[0][0]
        assert isinstance(created_entity, Person)
        assert created_entity.email == "test@company.com"
        assert created_entity.name == "Test User"