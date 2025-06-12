"""
Common test fixtures for graph-mcp tests.

This file contains fixtures that are used by both unit and integration tests,
following NeoAlchemy's testing patterns.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from neo4j import GraphDatabase

from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository

# Initialize NeoAlchemy once for all tests
initialize()

# Connection details - try environment variables first, fallback to hardcoded values
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "your_secure_password")


@pytest.fixture
def driver():
    """Create a Neo4j driver instance for E2E tests."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Verify connection
    try:
        with driver.session() as session:
            session.run("RETURN 1")
    except Exception as e:
        pytest.skip(f"Neo4j database not available: {e}")

    yield driver
    driver.close()


@pytest.fixture
def repo(driver):
    """Create a repository instance for integration/E2E tests."""
    return Neo4jRepository(driver)


@pytest.fixture
def clean_db(driver):
    """Clean the database before and after tests."""
    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    except Exception:
        pytest.skip("Skipping test that requires database cleanup")

    yield

    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    except Exception:
        pass  # Best effort cleanup


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for testing file generation."""
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_app_context():
    """Create a mock app context for testing CRUD functions."""
    app_context = MagicMock()
    mock_repo = MagicMock()
    mock_tx = MagicMock()
    
    # Configure transaction context manager
    mock_repo.transaction.return_value.__enter__.return_value = mock_tx
    mock_repo.transaction.return_value.__exit__.return_value = None
    
    app_context.repo = mock_repo
    return app_context, mock_tx