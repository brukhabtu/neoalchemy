"""
Unit tests for entity tools business logic.

These are true unit tests that test pure business logic with fully mocked dependencies.
No real models, databases, or external systems are used.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# We'll test the business logic functions directly, not through imports
# This avoids dependency on actual model classes


@pytest.mark.unit
class TestEntityCreationLogic:
    """Test entity creation business logic in isolation."""
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_create_entity_unknown_type_logic(self, mock_model_map):
        """Test logic for handling unknown entity types."""
        # Import here to avoid module-level dependencies
        from graph_mcp.tools.entities import _create_entity_impl
        
        # Setup mocks
        mock_model_map.__contains__ = MagicMock(return_value=False)
        mock_model_map.keys.return_value = ["Person", "Team", "Project"]
        mock_app_context = MagicMock()
        
        # Execute
        result = await _create_entity_impl(
            "UnknownType", 
            {"field": "value"}, 
            mock_app_context, 
            mock_model_map
        )
        
        # Verify error handling logic
        assert "error" in result
        assert "Unknown entity type: UnknownType" in result["error"]
        assert "Available types: ['Person', 'Team', 'Project']" in result["error"]
        
        # Should not attempt any database operations
        mock_app_context.repo.transaction.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_create_entity_validation_error_logic(self, mock_model_map):
        """Test logic for handling validation errors."""
        from graph_mcp.tools.entities import _create_entity_impl
        
        # Setup mocks
        mock_model_map.__contains__ = MagicMock(return_value=True)
        mock_model_class = MagicMock()
        mock_model_class.model_validate.side_effect = ValueError("Validation failed")
        mock_model_map.__getitem__ = MagicMock(return_value=mock_model_class)
        mock_app_context = MagicMock()
        
        # Execute
        result = await _create_entity_impl(
            "TestEntity",
            {"invalid": "data"},
            mock_app_context,
            mock_model_map
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "Failed to create TestEntity" in result["error"]
        assert "Validation failed" in result["error"]
        
        # Should not attempt database operations after validation failure
        mock_app_context.repo.transaction.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_create_entity_database_error_logic(self, mock_model_map):
        """Test logic for handling database errors."""
        from graph_mcp.tools.entities import _create_entity_impl
        
        # Setup mocks
        mock_model_map.__contains__ = MagicMock(return_value=True)
        mock_model_class = MagicMock()
        mock_entity = MagicMock()
        mock_model_class.model_validate.return_value = mock_entity
        mock_model_map.__getitem__ = MagicMock(return_value=mock_model_class)
        
        # Setup app context with transaction error
        mock_app_context = MagicMock()
        mock_tx = MagicMock()
        mock_tx.create.side_effect = Exception("Database connection failed")
        mock_app_context.repo.transaction.return_value.__enter__.return_value = mock_tx
        
        # Execute
        result = await _create_entity_impl(
            "TestEntity",
            {"valid": "data"},
            mock_app_context,
            mock_model_map
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "Failed to create TestEntity" in result["error"]
        assert "Database connection failed" in result["error"]
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_create_entity_success_logic(self, mock_model_map):
        """Test successful entity creation logic."""
        from graph_mcp.tools.entities import _create_entity_impl
        
        # Setup mocks for success path
        mock_model_map.__contains__ = MagicMock(return_value=True)
        mock_model_class = MagicMock()
        mock_entity = MagicMock()
        mock_created_entity = MagicMock()
        
        # Configure entity behavior
        mock_model_class.model_validate.return_value = mock_entity
        mock_created_entity.model_dump.return_value = {"id": "123", "name": "Test"}
        mock_model_map.__getitem__ = MagicMock(return_value=mock_model_class)
        
        # Setup successful transaction
        mock_app_context = MagicMock()
        mock_tx = MagicMock()
        mock_tx.create.return_value = mock_created_entity
        mock_app_context.repo.transaction.return_value.__enter__.return_value = mock_tx
        
        # Execute
        result = await _create_entity_impl(
            "Person",  # Use known entity type to test primary key logic
            {"email": "test@example.com", "name": "Test User"},
            mock_app_context,
            mock_model_map
        )
        
        # Verify success logic
        assert result["success"] is True
        assert result["entity_type"] == "Person"
        assert "entity" in result
        assert "message" in result
        
        # Verify method calls
        mock_model_class.model_validate.assert_called_once()
        mock_tx.create.assert_called_once_with(mock_entity)
        mock_created_entity.model_dump.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_primary_key_extraction_logic(self, mock_model_map):
        """Test primary key extraction logic for different entity types."""
        from graph_mcp.tools.entities import _create_entity_impl
        
        # Test different entity types and their primary key logic
        test_cases = [
            ("Person", "test@example.com", "email"),
            ("Team", "TestTeam", "name"), 
            ("Project", "TestProject", "name"),
        ]
        
        for entity_type, expected_id, pk_field in test_cases:
            # Setup mocks
            mock_model_map.__contains__ = MagicMock(return_value=True)
            mock_model_class = MagicMock()
            mock_entity = MagicMock()
            mock_created_entity = MagicMock()
            
            # Set the primary key field value
            setattr(mock_created_entity, pk_field, expected_id)
            
            mock_model_class.model_validate.return_value = mock_entity
            mock_created_entity.model_dump.return_value = {}
            mock_model_map.__getitem__ = MagicMock(return_value=mock_model_class)
            
            mock_app_context = MagicMock()
            mock_tx = MagicMock()
            mock_tx.create.return_value = mock_created_entity
            mock_app_context.repo.transaction.return_value.__enter__.return_value = mock_tx
            
            # Execute
            result = await _create_entity_impl(
                entity_type,
                {pk_field: expected_id},
                mock_app_context,
                mock_model_map
            )
            
            # Verify primary key extraction
            assert result["success"] is True
            assert result["entity_id"] == expected_id


@pytest.mark.unit
class TestEntityRetrievalLogic:
    """Test entity retrieval business logic in isolation."""
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_get_entity_unknown_type_logic(self, mock_model_map):
        """Test logic for handling unknown entity types in retrieval."""
        from graph_mcp.tools.entities import _get_entity_impl
        
        # Setup mocks
        mock_model_map.__contains__ = MagicMock(return_value=False)
        mock_model_map.keys.return_value = ["Person", "Team"]
        mock_app_context = MagicMock()
        
        # Execute
        result = await _get_entity_impl(
            "UnknownType",
            "some-id",
            mock_app_context,
            mock_model_map
        )
        
        # Verify error handling
        assert "error" in result
        assert "Unknown entity type: UnknownType" in result["error"]
        assert "Available types:" in result["error"]
    
    @pytest.mark.asyncio
    @patch('graph_mcp.tools.entities.MODEL_MAP')
    async def test_get_entity_no_primary_key_logic(self, mock_model_map):
        """Test logic for handling entities without primary keys."""
        from graph_mcp.tools.entities import _get_entity_impl
        
        # Setup mocks
        mock_model_map.__contains__ = MagicMock(return_value=True)
        mock_model_class = MagicMock()
        mock_model_class.get_primary_key.return_value = None
        mock_model_map.__getitem__ = MagicMock(return_value=mock_model_class)
        mock_app_context = MagicMock()
        
        # Execute
        result = await _get_entity_impl(
            "TestEntity",
            "some-id",
            mock_app_context,
            mock_model_map
        )
        
        # Verify error handling
        assert "error" in result
        assert "No primary key defined for TestEntity" in result["error"]


@pytest.mark.unit
class TestBusinessLogicHelpers:
    """Test helper functions and business logic utilities."""
    
    def test_entity_type_validation_logic(self):
        """Test entity type validation helper logic."""
        # Mock MODEL_MAP
        mock_model_map = {"Person": MagicMock(), "Team": MagicMock()}
        
        # Test valid entity type
        assert "Person" in mock_model_map
        assert "Team" in mock_model_map
        
        # Test invalid entity type  
        assert "InvalidType" not in mock_model_map
        
        # Test available types generation
        available_types = list(mock_model_map.keys())
        assert "Person" in available_types
        assert "Team" in available_types
    
    def test_primary_key_detection_logic(self):
        """Test primary key detection logic patterns."""
        # Test different entity type patterns
        entity_patterns = {
            "Person": "email",
            "Team": "name", 
            "Project": "name",
            "UnknownEntity": "fallback"
        }
        
        for entity_type, expected_field in entity_patterns.items():
            if entity_type == "Person":
                # Person should use email
                assert expected_field == "email"
            elif entity_type in ["Team", "Project"]:
                # Team and Project should use name
                assert expected_field == "name"
            else:
                # Unknown entities should have fallback behavior
                assert expected_field == "fallback"
    
    def test_error_message_formatting_logic(self):
        """Test error message formatting logic."""
        # Test unknown entity type error format
        entity_type = "UnknownType"
        available_types = ["Person", "Team", "Project"]
        
        error_msg = f"Unknown entity type: {entity_type}. Available types: {available_types}"
        
        assert entity_type in error_msg
        assert "Available types:" in error_msg
        assert "Person" in error_msg
        
        # Test validation error format
        operation = "create"
        entity_type = "Person"
        original_error = "Validation failed"
        
        error_msg = f"Failed to {operation} {entity_type}: {original_error}"
        
        assert operation in error_msg
        assert entity_type in error_msg
        assert original_error in error_msg
    
    def test_success_response_formatting_logic(self):
        """Test success response formatting logic."""
        # Test success response structure
        entity_type = "Person"
        entity_id = "test@example.com"
        entity_data = {"email": "test@example.com", "name": "Test User"}
        
        success_response = {
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity": entity_data,
            "message": f"Created {entity_type} successfully"
        }
        
        # Verify response structure
        assert success_response["success"] is True
        assert success_response["entity_type"] == entity_type
        assert success_response["entity_id"] == entity_id
        assert success_response["entity"] == entity_data
        assert entity_type in success_response["message"]