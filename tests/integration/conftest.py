"""Integration test fixtures with minimal mocking.

Only mocks external Neo4j database boundary to enable real component integration testing.
All internal component interactions use real objects and real method calls.
"""
import pytest
from unittest.mock import MagicMock
from neoalchemy.orm.repository import Neo4jRepository
from neoalchemy import initialize

# Import shared models
from .shared_models import Person, Company, Product, User, WorksAt


@pytest.fixture(scope="session", autouse=True)
def initialize_neoalchemy():
    """Initialize NeoAlchemy field expressions once for all tests."""
    initialize()


@pytest.fixture
def mock_driver():
    """Mock Neo4j driver - only external boundary mock needed for integration tests."""
    driver = MagicMock()
    
    # Configure minimal realistic Neo4j session behavior
    mock_session = MagicMock()
    mock_transaction = MagicMock()
    
    # Mock successful transaction lifecycle
    mock_session.begin_transaction.return_value = mock_transaction
    mock_transaction.commit.return_value = None
    mock_transaction.rollback.return_value = None
    mock_transaction.close.return_value = None
    mock_session.close.return_value = None
    
    driver.session.return_value = mock_session
    return driver


@pytest.fixture
def neo4j_transaction(mock_driver):
    """Provides a ready-to-use Neo4j transaction context."""
    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_session.begin_transaction.return_value = mock_tx
    mock_driver.session.return_value = mock_session
    
    repo = Neo4jRepository(driver=mock_driver)
    return repo, mock_session, mock_tx


@pytest.fixture
def mock_query_result():
    """Provides a mock query result builder."""
    def _create_result(data_list):
        mock_result = MagicMock()
        mock_result.data.return_value = data_list
        return mock_result
    return _create_result


@pytest.fixture
def mock_single_result():
    """Provides a mock single record result builder."""
    def _create_result(data_dict):
        mock_result = MagicMock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = data_dict
        mock_result.single.return_value = mock_record
        return mock_result
    return _create_result


# Legacy model definitions for backward compatibility
# TODO: Remove these once all tests are updated
PersonModel = Person
CompanyModel = Company
WorksAtModel = WorksAt