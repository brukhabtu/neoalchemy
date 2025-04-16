"""
Unit test fixtures for NeoAlchemy.

This file contains fixtures specific to unit tests, particularly mocks
that allow testing without a real Neo4j database connection.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from neoalchemy.orm.repository import Neo4jRepository
from neoalchemy import initialize

# Initialize NeoAlchemy
initialize()


@pytest.fixture
def mock_driver():
    """Create a mock Neo4j driver for unit tests."""
    driver = MagicMock()
    session = MagicMock()
    tx = MagicMock()
    result = MagicMock()
    
    # Configure the mocks
    driver.session.return_value = session
    session.begin_transaction.return_value = tx
    tx.run.return_value = result
    result.single.return_value = {"count": 1}
    
    # Set up a way to convert property params to record data
    def mock_run(query, params=None):
        if params is None:
            params = {}
        result = MagicMock()
        # Extract the first param value if it exists, otherwise use an empty dict
        param_value = next(iter(params.values()), {}) if params else {}
        result.data.return_value = [param_value]
        result.single.return_value = param_value
        return result
    
    tx.run.side_effect = mock_run
    
    return driver


@pytest.fixture
def mock_repo(mock_driver):
    """Create a repository with a mock driver."""
    return Neo4jRepository(mock_driver)


@pytest.fixture
def mock_session():
    """Create a mock Neo4j session for unit tests."""
    session = MagicMock()
    tx = MagicMock()
    result = MagicMock()
    
    # Configure the mocks
    session.begin_transaction.return_value = tx
    tx.run.return_value = result
    result.data.return_value = [{"name": "Test", "age": 30}]
    
    return session


@pytest.fixture
def isolated_registry():
    """Provide isolation for model registries during testing."""
    from neoalchemy.orm.models import Node, Relationship, Neo4jModel
    
    # Save original registries
    original_node_registry = Node.__registry__.copy()
    original_rel_registry = Relationship.__registry__.copy()
    original_model_registry = Neo4jModel.__registry__.copy()
    
    # Replace with empty registries
    Node.__registry__ = {}
    Relationship.__registry__ = {}
    Neo4jModel.__registry__ = {}
    
    yield
    
    # Restore original registries
    Node.__registry__ = original_node_registry
    Relationship.__registry__ = original_rel_registry
    Neo4jModel.__registry__ = original_model_registry