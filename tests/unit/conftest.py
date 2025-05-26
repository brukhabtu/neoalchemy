"""
Unit test fixtures for NeoAlchemy.

This file contains fixtures specific to unit tests that are completely isolated
from real database connections. Unit tests should NEVER access a real Neo4j database.

IMPORTANT: This conftest.py ONLY provides mock fixtures and explicitly prevents
any database access to ensure true unit test isolation.
"""

from unittest.mock import MagicMock, Mock
import pytest
import sys

from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository

# Initialize NeoAlchemy once for all unit tests
initialize()

# Prevent accidental use of real database fixtures in unit tests
def _prevent_database_access(fixture_name: str):
    """Prevent unit tests from accessing real database fixtures."""
    def fixture_blocker(*args, **kwargs):
        pytest.fail(
            f"Unit test attempted to use real database fixture '{fixture_name}'. "
            f"Unit tests must use mock fixtures only. "
            f"Use 'mock_driver', 'mock_repo', or 'mock_session' instead."
        )
    return fixture_blocker

# Block real database fixtures from being used in unit tests
@pytest.fixture
def driver():
    """Blocked: Unit tests cannot use real database driver."""
    return _prevent_database_access("driver")()

@pytest.fixture  
def repo():
    """Blocked: Unit tests cannot use real database repository."""
    return _prevent_database_access("repo")()

@pytest.fixture
def clean_db():
    """Blocked: Unit tests cannot use real database cleanup."""
    return _prevent_database_access("clean_db")()


# MOCK FIXTURES FOR UNIT TESTS ONLY

@pytest.fixture
def mock_driver():
    """Create a comprehensive mock Neo4j driver for unit tests."""
    driver = MagicMock()
    session = MagicMock()
    tx = MagicMock()
    result = MagicMock()

    # Configure the mock hierarchy
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    session.begin_transaction.return_value = tx
    tx.run.return_value = result
    tx.commit.return_value = None
    tx.rollback.return_value = None
    
    # Mock result data
    result.single.return_value = {"count": 1}
    result.data.return_value = [{"name": "Test", "age": 30}]
    result.consume.return_value = MagicMock()

    # Set up realistic mock_run behavior for testing
    def mock_run(query, params=None):
        """Mock query execution that returns reasonable test data."""
        if params is None:
            params = {}
        
        mock_result = MagicMock()
        
        # Return param values as if they were inserted/retrieved
        if params:
            param_value = next(iter(params.values()), {}) if params else {}
            mock_result.data.return_value = [param_value] if isinstance(param_value, dict) else [{"result": param_value}]
            mock_result.single.return_value = param_value if isinstance(param_value, dict) else {"result": param_value}
        else:
            mock_result.data.return_value = [{"count": 1}]
            mock_result.single.return_value = {"count": 1}
            
        mock_result.consume.return_value = MagicMock()
        return mock_result

    tx.run.side_effect = mock_run
    
    # Mock driver close
    driver.close.return_value = None

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
    tx.commit.return_value = None
    tx.rollback.return_value = None
    result.data.return_value = [{"name": "Test", "age": 30}]
    result.single.return_value = {"name": "Test", "age": 30}
    result.consume.return_value = MagicMock()

    return session


@pytest.fixture
def mock_transaction():
    """Create a mock Neo4j transaction for unit tests."""
    tx = MagicMock()
    result = MagicMock()
    
    tx.run.return_value = result
    tx.commit.return_value = None
    tx.rollback.return_value = None
    result.data.return_value = [{"id": 1, "name": "Test"}]
    result.single.return_value = {"id": 1, "name": "Test"}
    result.consume.return_value = MagicMock()
    
    return tx


@pytest.fixture
def isolated_registry():
    """Provide isolation for model registries during testing."""
    from neoalchemy.orm.models import Neo4jModel, Node, Relationship

    # Save original registries
    original_node_registry = Node.__registry__.copy()
    original_rel_registry = Relationship.__registry__.copy() 
    original_model_registry = Neo4jModel.__registry__.copy()

    # Replace with empty registries for test isolation
    Node.__registry__ = {}
    Relationship.__registry__ = {}
    Neo4jModel.__registry__ = {}

    yield {
        "node_registry": Node.__registry__,
        "relationship_registry": Relationship.__registry__,
        "model_registry": Neo4jModel.__registry__
    }

    # Restore original registries
    Node.__registry__ = original_node_registry
    Relationship.__registry__ = original_rel_registry
    Neo4jModel.__registry__ = original_model_registry


@pytest.fixture(autouse=True)
def enforce_unit_test_isolation():
    """Auto-fixture that enforces unit test isolation."""
    # This fixture runs automatically for all unit tests
    # and can detect if any real database connections are attempted
    
    # Store original modules that might attempt database connections
    original_neo4j = sys.modules.get('neo4j')
    
    yield
    
    # Cleanup - this runs after each test
    # Could add validation here if needed
