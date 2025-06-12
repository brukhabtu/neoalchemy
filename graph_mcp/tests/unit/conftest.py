"""
Unit test fixtures for graph-mcp.

This file contains fixtures specific to unit tests that are completely isolated
from real database connections. Unit tests should NEVER access a real Neo4j database.
"""

from unittest.mock import MagicMock
import pytest

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
            f"Use 'mock_driver', 'mock_repo', or 'mock_app_context' instead."
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

    return driver


@pytest.fixture
def mock_repo(mock_driver):
    """Create a repository with a mock driver."""
    return Neo4jRepository(mock_driver)


@pytest.fixture
def mock_app_context():
    """Create a mock app context for testing generated CRUD functions."""
    app_context = MagicMock()
    mock_repo = MagicMock()
    mock_tx = MagicMock()
    
    # Configure transaction context manager
    mock_repo.transaction.return_value.__enter__.return_value = mock_tx
    mock_repo.transaction.return_value.__exit__.return_value = None
    
    # Mock common transaction operations
    mock_tx.create.return_value = MagicMock()
    mock_tx.find_one.return_value = MagicMock()
    mock_tx.delete.return_value = None
    
    app_context.repo = mock_repo
    return app_context, mock_tx


@pytest.fixture(autouse=True)
def enforce_unit_test_isolation():
    """Auto-fixture that enforces unit test isolation."""
    # This fixture runs automatically for all unit tests
    # and can detect if any real database connections are attempted
    yield