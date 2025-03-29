"""
Common test fixtures and data for NeoAlchemy tests.
"""

import pytest
from neo4j import GraphDatabase

from neoalchemy.repository import Neo4jRepository

# Import models from the models module
# No model definitions here - they're all in models.py

# Connection details - hardcoded values
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_secure_password"


@pytest.fixture
def driver():
    """Create a Neo4j driver instance."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        session.run("RETURN 1")

    yield driver
    driver.close()


@pytest.fixture
def repo(driver):
    """Create a repository instance."""
    return Neo4jRepository(driver)


@pytest.fixture
def clean_db(driver):
    """Clean the database before and after tests."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    yield
    
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")