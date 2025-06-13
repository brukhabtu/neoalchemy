"""Integration test fixtures for graph_mcp with minimal mocking.

Only mocks external Neo4j database boundary to enable real component integration testing.
All internal component interactions use real objects and real method calls.
"""
import pytest
from unittest.mock import MagicMock
from pathlib import Path

from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository

# Import graph_mcp models
from graph_mcp.models.entities import Person, Team, Project, Service, Repository
from graph_mcp.models.sources import Source, SourceType


@pytest.fixture
def mock_model_map():
    """Create a mock MODEL_MAP for integration tests."""
    return {
        "Person": Person,
        "Team": Team, 
        "Project": Project,
        "Service": Service,
        "Repository": Repository,
        "Source": Source,
    }


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
def mock_repo(mock_driver):
    """Create a real repository with mocked driver."""
    return Neo4jRepository(driver=mock_driver)


@pytest.fixture
def mock_transaction_context(mock_driver):
    """Provides a mocked transaction context for testing MCP tools."""
    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_session.begin_transaction.return_value = mock_tx
    mock_driver.session.return_value = mock_session
    
    repo = Neo4jRepository(driver=mock_driver)
    return repo, mock_session, mock_tx


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for testing real file generation."""
    output_dir = tmp_path / "generated_crud"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_entities():
    """Create sample entity instances for testing."""
    return {
        "person": Person(
            email="alice@company.com",
            name="Alice Smith",
            title="Senior Engineer"
        ),
        "team": Team(
            name="Engineering",
            department="Product",
            description="Product engineering team"
        ),
        "project": Project(
            name="API Redesign",
            status="active",
            description="Redesigning the core API"
        ),
        "source": Source(
            name="PROJ-123",
            type=SourceType.JIRA,
            description="Project planning ticket",
            url="https://company.atlassian.net/browse/PROJ-123"
        )
    }


@pytest.fixture
def mock_query_result():
    """Provides a mock query result builder for database operations."""
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