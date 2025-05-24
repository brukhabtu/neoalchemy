"""
Common test fixtures for both unit and end-to-end tests.

This file contains fixtures that are used by both unit and E2E tests,
such as model setup and tear down.
"""

import pytest
import os
from neo4j import GraphDatabase

from neoalchemy.orm.repository import Neo4jRepository
from neoalchemy import initialize

# Import models from the models module
# No model definitions here - they're all in models.py

# Initialize NeoAlchemy
initialize()

# Connection details - try environment variables first, fallback to hardcoded values
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "your_secure_password")


@pytest.fixture
def driver():
    """Create a Neo4j driver instance.

    This fixture is primarily used by e2e tests but available to all tests.
    """
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
    """Create a repository instance.

    This fixture is used by both e2e and some unit tests that need a repository.
    """
    return Neo4jRepository(driver)


@pytest.fixture
def clean_db(driver):
    """Clean the database before and after tests.

    This fixture ensures tests start with a clean database and clean up after themselves.
    """
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
