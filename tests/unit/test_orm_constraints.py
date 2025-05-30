"""
Unit tests for ORM constraint functionality.

These tests focus on constraint metadata extraction and processing in isolation.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.orm.constraints import (
    _drop_existing_constraints,
    _setup_unique_constraints, 
    _setup_indexes
)


@pytest.mark.unit
class TestDropExistingConstraints:
    """Test _drop_existing_constraints function in isolation."""

    @patch('neoalchemy.orm.constraints.logger')
    def test_drop_existing_constraints_success(self, mock_logger):
        """Test _drop_existing_constraints drops constraints and indexes successfully."""
        mock_session = Mock()
        
        # Mock constraint and index data
        constraint_data = [{"name": "constraint1"}, {"name": "constraint2"}]
        index_data = [{"name": "index1"}, {"name": "index2"}]
        
        mock_session.run.side_effect = [
            Mock(data=Mock(return_value=constraint_data)),  # SHOW CONSTRAINTS
            None,  # DROP CONSTRAINT constraint1
            None,  # DROP CONSTRAINT constraint2
            Mock(data=Mock(return_value=index_data)),  # SHOW INDEXES
            None,  # DROP INDEX index1
            None,  # DROP INDEX index2
        ]
        
        _drop_existing_constraints(mock_session)
        
        # Should run show and drop commands
        assert mock_session.run.call_count == 6
        
        # Should log success
        mock_logger.info.assert_called()

    @patch('neoalchemy.orm.constraints.logger')
    def test_drop_existing_constraints_handles_exceptions(self, mock_logger):
        """Test _drop_existing_constraints handles exceptions gracefully."""
        mock_session = Mock()
        mock_session.run.side_effect = Exception("Database error")
        
        # Should not raise exception
        _drop_existing_constraints(mock_session)
        
        # Should log warning
        mock_logger.warning.assert_called()

    @patch('neoalchemy.orm.constraints.logger')
    def test_drop_existing_constraints_handles_missing_names(self, mock_logger):
        """Test _drop_existing_constraints handles constraints/indexes without names."""
        mock_session = Mock()
        
        # Mock data with missing names
        constraint_data = [{"name": "constraint1"}, {"other_field": "no_name"}]
        index_data = [{"name": None}, {"name": "index1"}]
        
        mock_session.run.side_effect = [
            Mock(data=Mock(return_value=constraint_data)),
            None,  # DROP valid constraint
            Mock(data=Mock(return_value=index_data)),
            None,  # DROP valid index
        ]
        
        _drop_existing_constraints(mock_session)
        
        # Should only drop items with valid names
        assert mock_session.run.call_count == 4


@pytest.mark.unit
class TestSetupUniqueConstraints:
    """Test _setup_unique_constraints function in isolation."""

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_unique_constraints_for_node(self, mock_logger):
        """Test _setup_unique_constraints creates node constraints correctly."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["email", "username"]
        
        _setup_unique_constraints(mock_session, mock_model, "User", True)
        
        # Should create constraints for each field
        assert mock_session.run.call_count == 2
        
        # Check constraint queries contain correct syntax for nodes
        calls = mock_session.run.call_args_list
        for call in calls:
            query = call[0][0]
            assert "CREATE CONSTRAINT" in query
            assert "FOR (n:User)" in query
            assert "IS UNIQUE" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_unique_constraints_for_relationship(self, mock_logger):
        """Test _setup_unique_constraints creates relationship constraints correctly."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["transaction_id"]
        
        _setup_unique_constraints(mock_session, mock_model, "PAYMENT", False)
        
        # Should create constraint for relationship
        mock_session.run.assert_called_once()
        
        # Check constraint query contains correct syntax for relationships
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        assert "CREATE CONSTRAINT" in query
        assert "FOR (r[r:PAYMENT])" in query
        assert "IS UNIQUE" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_unique_constraints_handles_exceptions(self, mock_logger):
        """Test _setup_unique_constraints handles database exceptions."""
        mock_session = Mock()
        mock_session.run.side_effect = Exception("Constraint creation failed")
        
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["email"]
        
        # Should not raise exception
        _setup_unique_constraints(mock_session, mock_model, "User", True)
        
        # Should log error
        mock_logger.error.assert_called()

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_unique_constraints_with_no_constraints(self, mock_logger):
        """Test _setup_unique_constraints handles models with no constraints."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        
        _setup_unique_constraints(mock_session, mock_model, "User", True)
        
        # Should not create any constraints
        mock_session.run.assert_not_called()


@pytest.mark.unit
class TestSetupIndexes:
    """Test _setup_indexes function in isolation."""

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_indexes_excludes_unique_fields(self, mock_logger):
        """Test _setup_indexes excludes fields that have unique constraints."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["email"]  # Unique constraint
        mock_model.get_indexes.return_value = ["email", "name"]  # Both need indexes
        
        _setup_indexes(mock_session, mock_model, "User", True)
        
        # Should only create index for 'name' (not 'email' since it has unique constraint)
        mock_session.run.assert_called_once()
        
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        assert "name" in query
        assert "email" not in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_indexes_for_nodes(self, mock_logger):
        """Test _setup_indexes creates node indexes correctly."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = ["name", "department"]
        
        _setup_indexes(mock_session, mock_model, "Employee", True)
        
        # Should create indexes for both fields
        assert mock_session.run.call_count == 2
        
        # Check index queries contain correct syntax for nodes
        calls = mock_session.run.call_args_list
        for call in calls:
            query = call[0][0]
            assert "CREATE INDEX" in query
            assert "FOR (n:Employee)" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_indexes_for_relationships(self, mock_logger):
        """Test _setup_indexes creates relationship indexes correctly."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = ["amount"]
        
        _setup_indexes(mock_session, mock_model, "TRANSACTION", False)
        
        # Should create index for relationship
        mock_session.run.assert_called_once()
        
        # Check index query contains correct syntax for relationships
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        assert "CREATE INDEX" in query
        assert "FOR (r[r:TRANSACTION])" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_indexes_handles_exceptions(self, mock_logger):
        """Test _setup_indexes handles database exceptions."""
        mock_session = Mock()
        mock_session.run.side_effect = Exception("Index creation failed")
        
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = ["name"]
        
        # Should not raise exception
        _setup_indexes(mock_session, mock_model, "User", True)
        
        # Should log error
        mock_logger.error.assert_called()

    @patch('neoalchemy.orm.constraints.logger')
    def test_setup_indexes_with_no_indexes(self, mock_logger):
        """Test _setup_indexes handles models with no indexes."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = []
        
        _setup_indexes(mock_session, mock_model, "User", True)
        
        # Should not create any indexes
        mock_session.run.assert_not_called()


@pytest.mark.unit
class TestConstraintQueryGeneration:
    """Test constraint and index query generation logic."""

    @patch('neoalchemy.orm.constraints.logger')
    def test_constraint_query_includes_constraint_name(self, mock_logger):
        """Test unique constraint queries include proper constraint names."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["email"]
        
        _setup_unique_constraints(mock_session, mock_model, "User", True)
        
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        
        # Should include constraint name based on entity type and field
        assert "user_email_unique" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_index_query_includes_index_name(self, mock_logger):
        """Test index queries include proper index names."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = ["name"]
        
        _setup_indexes(mock_session, mock_model, "Employee", True)
        
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        
        # Should include index name based on entity type and field
        assert "employee_name_idx" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_constraint_query_uses_proper_node_syntax(self, mock_logger):
        """Test constraint queries use proper Neo4j node syntax."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = ["id"]
        
        _setup_unique_constraints(mock_session, mock_model, "TestNode", True)
        
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        
        # Should use node syntax
        assert "FOR (n:TestNode)" in query
        assert "REQUIRE n.id IS UNIQUE" in query

    @patch('neoalchemy.orm.constraints.logger')
    def test_index_query_uses_proper_relationship_syntax(self, mock_logger):
        """Test index queries use proper Neo4j relationship syntax."""
        mock_session = Mock()
        mock_model = Mock()
        mock_model.get_constraints.return_value = []
        mock_model.get_indexes.return_value = ["amount"]
        
        _setup_indexes(mock_session, mock_model, "PAYMENT", False)
        
        call = mock_session.run.call_args_list[0]
        query = call[0][0]
        
        # Should use relationship syntax
        assert "FOR (r[r:PAYMENT])" in query
        assert "ON (r.amount)" in query