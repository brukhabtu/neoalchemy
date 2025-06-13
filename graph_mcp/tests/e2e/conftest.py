"""E2E test fixtures for graph_mcp with real Neo4j database.

These fixtures provide real database connections and complete system setup
for end-to-end testing of graph_mcp functionality.
"""
import pytest
import os
from pathlib import Path
from neo4j import GraphDatabase

from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository

# Import graph_mcp models for database setup
from graph_mcp.models.entities import Person, Team, Project, Service, Repository
from graph_mcp.models.sources import Source, SourceType, SourceMethod


# Connection details - try environment variables first
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "your_secure_password")


@pytest.fixture(scope="session", autouse=True)
def initialize_neoalchemy():
    """Initialize NeoAlchemy field expressions once for all E2E tests."""
    initialize()


@pytest.fixture(scope="session")
def neo4j_driver():
    """Create a real Neo4j driver for E2E tests."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Verify connection works
    try:
        with driver.session() as session:
            session.run("RETURN 1")
    except Exception as e:
        pytest.skip(f"Neo4j database not available: {e}")
    
    yield driver
    driver.close()


@pytest.fixture
def repo(neo4j_driver):
    """Create a real repository instance for E2E tests."""
    return Neo4jRepository(neo4j_driver)


@pytest.fixture
def clean_database(neo4j_driver):
    """Clean the database before and after E2E tests."""
    def _clean():
        try:
            with neo4j_driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        except Exception:
            pytest.skip("Skipping test that requires database cleanup")
    
    # Clean before test
    _clean()
    yield
    # Clean after test  
    _clean()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for testing real file generation."""
    output_dir = tmp_path / "e2e_generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_database_entities(repo, clean_database):
    """Create sample entities in the real database for E2E testing."""
    entities = {}
    
    with repo.transaction() as tx:
        # Create sample entities
        person = Person(
            email="alice.smith@company.com",
            name="Alice Smith", 
            title="Senior Engineer"
        )
        entities["person"] = tx.create(person)
        
        team = Team(
            name="Engineering",
            department="Product",
            description="Product engineering team"
        )
        entities["team"] = tx.create(team)
        
        project = Project(
            name="API Redesign",
            status="active",
            description="Redesigning the core API"
        )
        entities["project"] = tx.create(project)
        
        service = Service(
            name="User Service",
            type="microservice",
            description="Handles user management"
        )
        entities["service"] = tx.create(service)
        
        repository = Repository(
            name="user-service-repo",
            url="https://github.com/company/user-service",
            description="User service repository"
        )
        entities["repository"] = tx.create(repository)
        
        source = Source(
            name="PROJ-123",
            type=SourceType.JIRA,
            description="Project planning ticket",
            url="https://company.atlassian.net/browse/PROJ-123"
        )
        entities["source"] = tx.create(source)
    
    return entities


@pytest.fixture
def app_context(repo):
    """Create a real app context for E2E testing."""
    class AppContext:
        def __init__(self, repo):
            self.repo = repo
    
    return AppContext(repo)


@pytest.fixture
def verify_generated_files():
    """Helper fixture to verify generated files are valid Python."""
    def _verify_file(file_path: Path):
        """Verify a generated Python file is syntactically correct."""
        assert file_path.exists(), f"Generated file {file_path} does not exist"
        assert file_path.suffix == ".py", f"Generated file {file_path} is not a Python file"
        
        # Read and verify syntax
        content = file_path.read_text()
        assert len(content) > 0, f"Generated file {file_path} is empty"
        
        # Basic syntax check by attempting to compile
        try:
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated file {file_path} has syntax error: {e}")
        
        # Check for expected content patterns
        assert "async def" in content, f"Generated file {file_path} missing async functions"
        assert "from graph_mcp.models" in content, f"Generated file {file_path} missing imports"
        
        return content
    
    return _verify_file