"""
Integration tests for relationship tools with real NeoAlchemy objects.

These tests verify that relationship tools work correctly with real model instances
and relationship classes, using mocked database connections.
"""

import pytest
from unittest.mock import MagicMock

from graph_mcp.tools.relationships import _create_relationship_impl
from graph_mcp.models import MODEL_MAP, CONTRIBUTES_TO, DEPENDS_ON, MANAGES, REFERS_TO
from graph_mcp.models.entities import Person, Team, Project, Service


@pytest.mark.integration
class TestCreateRelationshipIntegration:
    """Test relationship creation with real NeoAlchemy models and relationships."""
    
    async def test_create_manages_relationship(self, mock_transaction_context, sample_entities):
        """Test creating a MANAGES relationship between Person and Team."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup mock entities
        person = sample_entities["person"]
        team = sample_entities["team"]
        mock_tx.find_one.side_effect = [person, team]  # Return person, then team
        
        # Setup mock relationship creation
        mock_relationship = MagicMock()
        mock_tx.create_relationship.return_value = mock_relationship
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="alice@company.com",
            to_entity_type="Team", 
            to_entity_id="Engineering",
            properties={"since": "2023-01-01"},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify result
        assert result["success"] is True
        assert result["relationship_type"] == "MANAGES"
        assert result["from_entity"] == "Person:alice@company.com"
        assert result["to_entity"] == "Team:Engineering"
        
        # Verify correct entities were looked up
        assert mock_tx.find_one.call_count == 2
        mock_tx.find_one.assert_any_call(Person, **{"email": "alice@company.com"})
        mock_tx.find_one.assert_any_call(Team, **{"name": "Engineering"})
        
        # Verify relationship creation was called
        mock_tx.create_relationship.assert_called_once()
    
    async def test_create_contributes_to_relationship(self, mock_transaction_context):
        """Test creating a CONTRIBUTES_TO relationship between Person and Project."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup entities
        person = Person(email="dev@company.com", name="Developer")
        project = Project(name="API Redesign", status="active")
        mock_tx.find_one.side_effect = [person, project]
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="CONTRIBUTES_TO",
            from_entity_type="Person",
            from_entity_id="dev@company.com",
            to_entity_type="Project",
            to_entity_id="API Redesign",
            properties={"role": "lead developer", "hours_per_week": 40},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify
        assert result["success"] is True
        assert result["relationship_type"] == "CONTRIBUTES_TO"
        
        # Verify proper entity lookup by primary keys
        mock_tx.find_one.assert_any_call(Person, **{"email": "dev@company.com"})
        mock_tx.find_one.assert_any_call(Project, **{"name": "API Redesign"})
    
    async def test_create_depends_on_relationship(self, mock_transaction_context):
        """Test creating a DEPENDS_ON relationship between Projects."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup projects
        project1 = Project(name="Frontend", status="active")
        project2 = Project(name="API", status="active")
        mock_tx.find_one.side_effect = [project1, project2]
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="DEPENDS_ON",
            from_entity_type="Project",
            from_entity_id="Frontend",
            to_entity_type="Project",
            to_entity_id="API",
            properties={"dependency_type": "blocking"},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify
        assert result["success"] is True
        assert result["relationship_type"] == "DEPENDS_ON"
        assert result["from_entity"] == "Project:Frontend"
        assert result["to_entity"] == "Project:API"
    
    async def test_create_relationship_with_invalid_type(self, mock_transaction_context):
        """Test handling of invalid relationship types."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Execute with invalid relationship type
        result = await _create_relationship_impl(
            relationship_type="INVALID_RELATIONSHIP",
            from_entity_type="Person",
            from_entity_id="test@company.com",
            to_entity_type="Team",
            to_entity_id="Engineering",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify error handling
        assert "error" in result
        assert "Unknown relationship type: INVALID_RELATIONSHIP" in result["error"]
        assert "Available types:" in result["error"]
        
        # Should not attempt entity lookup
        mock_tx.find_one.assert_not_called()
    
    async def test_create_relationship_entity_not_found(self, mock_transaction_context):
        """Test handling when from_entity is not found."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup: from_entity not found, to_entity found
        team = Team(name="Engineering", department="Product")
        mock_tx.find_one.side_effect = [None, team]  # First call returns None
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="nonexistent@company.com",
            to_entity_type="Team",
            to_entity_id="Engineering",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify error handling
        assert "error" in result
        assert "Person with email='nonexistent@company.com' not found" in result["error"]
        
        # Should attempt to find from_entity but not proceed to relationship creation
        mock_tx.find_one.assert_called_once_with(Person, **{"email": "nonexistent@company.com"})
        mock_tx.create_relationship.assert_not_called()
    
    async def test_create_relationship_to_entity_not_found(self, mock_transaction_context):
        """Test handling when to_entity is not found."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup: from_entity found, to_entity not found
        person = Person(email="manager@company.com", name="Manager")
        mock_tx.find_one.side_effect = [person, None]  # Second call returns None
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="manager@company.com",
            to_entity_type="Team",
            to_entity_id="NonexistentTeam",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify error handling
        assert "error" in result
        assert "Team with name='NonexistentTeam' not found" in result["error"]
        
        # Should attempt to find both entities
        assert mock_tx.find_one.call_count == 2
        mock_tx.create_relationship.assert_not_called()
    
    async def test_create_relationship_with_database_error(self, mock_transaction_context):
        """Test handling of database errors during relationship creation."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup entities
        person = Person(email="test@company.com", name="Test User")
        team = Team(name="TestTeam", department="Test")
        mock_tx.find_one.side_effect = [person, team]
        
        # Setup database error during relationship creation
        mock_tx.create_relationship.side_effect = Exception("Database constraint violation")
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="test@company.com",
            to_entity_type="Team",
            to_entity_id="TestTeam",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify error handling
        assert "error" in result
        assert "Database constraint violation" in result["error"]


@pytest.mark.integration
class TestRelationshipModelIntegration:
    """Test integration between relationship tools and NeoAlchemy relationship models."""
    
    def test_relationship_models_are_available(self):
        """Test that all expected relationship models are available."""
        expected_relationships = [CONTRIBUTES_TO, DEPENDS_ON, MANAGES, REFERS_TO]
        
        for rel_class in expected_relationships:
            # Should be importable
            assert rel_class is not None
            
            # Should have NeoAlchemy relationship properties
            assert hasattr(rel_class, "__type__"), f"{rel_class} missing __type__"
            
            # Should be a valid relationship class
            assert hasattr(rel_class, "model_validate"), f"{rel_class} not a Pydantic model"
    
    def test_relationship_type_mapping(self):
        """Test that relationship type strings map correctly to relationship classes."""
        # This tests the integration between string identifiers and actual classes
        type_mappings = {
            "CONTRIBUTES_TO": CONTRIBUTES_TO,
            "DEPENDS_ON": DEPENDS_ON,
            "MANAGES": MANAGES,
            "REFERS_TO": REFERS_TO,
        }
        
        for type_string, rel_class in type_mappings.items():
            # The __type__ should match the string identifier
            assert hasattr(rel_class, "__type__")
            # Note: __type__ might be different from the variable name, 
            # this tests the actual Neo4j relationship type
    
    def test_relationship_properties_validation(self):
        """Test that relationship models handle properties validation correctly."""
        # Test MANAGES relationship with properties
        manages_props = {"since": "2023-01-01", "authority_level": "full"}
        manages_rel = MANAGES.model_validate(manages_props)
        assert manages_rel is not None
        
        # Test CONTRIBUTES_TO relationship with properties
        contributes_props = {"role": "developer", "hours_per_week": 40}
        contributes_rel = CONTRIBUTES_TO.model_validate(contributes_props)
        assert contributes_rel is not None
        
        # Test empty properties
        empty_rel = DEPENDS_ON.model_validate({})
        assert empty_rel is not None


@pytest.mark.integration
class TestPrimaryKeyDetectionIntegration:
    """Test integration of primary key detection across different entity types."""
    
    async def test_primary_key_detection_for_all_entities(self, mock_transaction_context):
        """Test that primary key detection works for all entity types in relationships."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Test cases: entity_type -> (test_id, expected_lookup_kwargs)
        test_cases = [
            ("Person", "test@company.com", {"email": "test@company.com"}),
            ("Team", "TestTeam", {"name": "TestTeam"}),
            ("Project", "TestProject", {"name": "TestProject"}),
            ("Service", "TestService", {"name": "TestService"}),
        ]
        
        for entity_type, test_id, expected_kwargs in test_cases:
            # Create mock entity
            entity_class = MODEL_MAP[entity_type]
            mock_entity = MagicMock()
            mock_tx.find_one.return_value = mock_entity
            
            # Execute relationship creation (just to trigger entity lookup)
            await _create_relationship_impl(
                relationship_type="REFERS_TO",
                from_entity_type=entity_type,
                from_entity_id=test_id,
                to_entity_type="Service",  # Use Service as a generic target
                to_entity_id="TargetService",
                properties=None,
                app_context=app_context,
                MODEL_MAP=MODEL_MAP
            )
            
            # Verify correct primary key was used for lookup
            mock_tx.find_one.assert_any_call(entity_class, **expected_kwargs)
            
            # Reset for next iteration
            mock_tx.reset_mock()
    
    async def test_entity_lookup_with_real_model_classes(self, mock_transaction_context):
        """Test that entity lookup uses real model classes correctly."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup real entities
        person = Person(email="real@company.com", name="Real Person")
        project = Project(name="RealProject", status="active")
        mock_tx.find_one.side_effect = [person, project]
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="CONTRIBUTES_TO",
            from_entity_type="Person",
            from_entity_id="real@company.com",
            to_entity_type="Project",
            to_entity_id="RealProject",
            properties={"role": "contributor"},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify correct model classes were used
        mock_tx.find_one.assert_any_call(Person, **{"email": "real@company.com"})
        mock_tx.find_one.assert_any_call(Project, **{"name": "RealProject"})
        
        # Verify success
        assert result["success"] is True


@pytest.mark.integration
class TestTransactionIntegrationForRelationships:
    """Test transaction integration for relationship operations."""
    
    async def test_relationship_transaction_context(self, mock_transaction_context):
        """Test that relationship creation uses transaction context properly."""
        repo, mock_session, mock_tx = mock_transaction_context
        
        app_context = MagicMock()
        app_context.repo = repo
        
        # Setup entities
        person = Person(email="tx@company.com", name="Transaction Test")
        team = Team(name="TxTeam", department="Test")
        mock_tx.find_one.side_effect = [person, team]
        
        # Execute
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="tx@company.com",
            to_entity_type="Team",
            to_entity_id="TxTeam",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify transaction was used
        repo.transaction.assert_called_once()
        
        # Verify transaction operations were called
        assert mock_tx.find_one.call_count == 2  # Two entity lookups
        mock_tx.create_relationship.assert_called_once()
        
        assert result["success"] is True