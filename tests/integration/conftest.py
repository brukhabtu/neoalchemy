"""
Fixtures for integration tests.

Integration tests use a real Neo4j database but with proper isolation
and cleanup between tests.
"""

import pytest
from neo4j import GraphDatabase

from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository


@pytest.fixture(scope="session")
def neo4j_uri():
    """Neo4j connection URI for integration tests."""
    # Use environment variable or default
    import os
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


@pytest.fixture(scope="session")
def neo4j_auth():
    """Neo4j authentication for integration tests."""
    import os
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return (user, password)


@pytest.fixture(scope="session")
def driver(neo4j_uri, neo4j_auth):
    """Neo4j driver for integration tests."""
    driver_instance = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
    
    # Verify connection
    try:
        driver_instance.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")
    
    yield driver_instance
    driver_instance.close()


@pytest.fixture(scope="session")
def initialized_neoalchemy():
    """Initialize NeoAlchemy for integration tests."""
    initialize()
    return True


@pytest.fixture
def repo(driver, initialized_neoalchemy):
    """Neo4j repository for integration tests."""
    return Neo4jRepository(driver)


@pytest.fixture
def clean_db(driver):
    """Clean database before each test."""
    with driver.session() as session:
        # Clear all data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Clear constraints and indexes (for clean slate)
        try:
            # Get and drop all constraints
            constraints = session.run("SHOW CONSTRAINTS").data()
            for constraint in constraints:
                name = constraint.get("name")
                if name:
                    session.run(f"DROP CONSTRAINT {name} IF EXISTS")
            
            # Get and drop all indexes
            indexes = session.run("SHOW INDEXES").data()
            for index in indexes:
                name = index.get("name")
                if name and not name.startswith("btree"):  # Keep system indexes
                    session.run(f"DROP INDEX {name} IF EXISTS")
        except Exception:
            # Some Neo4j versions might not support SHOW CONSTRAINTS/INDEXES
            # or might have different syntax - that's okay for integration tests
            pass
    
    yield
    
    # Clean up after test
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture
def sample_data(repo, clean_db):
    """Create sample data for integration tests."""
    from tests.models import Person, Company, WORKS_FOR
    
    with repo.transaction() as tx:
        # Create test persons
        alice = tx.create(Person(name="Alice", age=30, tags=["developer", "python"]))
        bob = tx.create(Person(name="Bob", age=25, tags=["manager"]))
        
        # Create test company
        company = tx.create(Company(name="TechCorp", founded=2000, industry="Technology"))
        
        # Create relationships
        alice_works = WORKS_FOR(role="Senior Developer")
        bob_works = WORKS_FOR(role="Project Manager")
        
        tx.relate(alice, alice_works, company)
        tx.relate(bob, bob_works, company)
        
        return {
            "alice": alice,
            "bob": bob,
            "company": company,
            "alice_works": alice_works,
            "bob_works": bob_works
        }