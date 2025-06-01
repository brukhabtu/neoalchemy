"""End-to-end test fixtures for NeoAlchemy.

These fixtures provide complete system setup including real Neo4j database,
constraint setup, and realistic test data for full workflow testing.
"""
import os
import subprocess
import time
import pytest
from neo4j import GraphDatabase

from neoalchemy import initialize
from neoalchemy.orm import Neo4jRepository
from neoalchemy.constraints import setup_constraints


def pytest_addoption(parser):
    """Add custom pytest command line options."""
    parser.addoption(
        "--neo4j-auto-start",
        action="store_true",
        default=False,
        help="Automatically start Neo4j service before running E2E tests"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: end-to-end test that requires Neo4j database"
    )


@pytest.fixture(scope="session", autouse=True)
def initialize_neoalchemy():
    """Initialize NeoAlchemy field expressions once for all E2E tests."""
    initialize()


@pytest.fixture(scope="session")
def neo4j_service(request):
    """Start Neo4j service if --neo4j-auto-start flag is provided."""
    if not request.config.getoption("--neo4j-auto-start"):
        yield  # Always yield, even if we don't start the service
        return
    
    # Detect environment and start appropriate service
    if os.path.exists("/.dockerenv"):
        # Inside devcontainer
        compose_cmd = ["docker-compose", "up", "-d", "neo4j"]
        cleanup_cmd = ["docker-compose", "down"]
    else:
        # Local host - use simple docker run for testing
        compose_cmd = [
            "docker", "run", "-d", "--name", "neoalchemy-neo4j-test", 
            "-p", "7687:7687", "-p", "7474:7474",
            "-e", "NEO4J_AUTH=neo4j/password",
            "-e", "NEO4J_ACCEPT_LICENSE_AGREEMENT=yes",
            "neo4j:4.4"
        ]
        cleanup_cmd = ["docker", "rm", "-f", "neoalchemy-neo4j-test"]
    
    print("🚀 Starting Neo4j service...")
    try:
        subprocess.run(compose_cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to start Neo4j service: {e}")
    
    # Wait for Neo4j to be ready
    _wait_for_neo4j_ready()
    
    yield
    
    print("🧹 Stopping Neo4j service...")
    subprocess.run(cleanup_cmd, check=False)  # Don't fail if already stopped


@pytest.fixture(scope="session")
def neo4j_driver(neo4j_service):
    """Create a real Neo4j driver for E2E tests."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # Verify connection - fail fast if not available
    driver.verify_connectivity()
    
    yield driver
    driver.close()


def _wait_for_neo4j_ready():
    """Wait for Neo4j to be ready using Neo4j driver with exponential backoff."""
    from neo4j import GraphDatabase
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print("⏳ Waiting for Neo4j to be ready...")
    max_wait = 60  # seconds
    start_time = time.time()
    wait_time = 1  # start with 1 second
    
    while time.time() - start_time < max_wait:
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            
            # Additional check: can we run a simple query?
            with driver.session() as session:
                session.run("RETURN 1").single()
            
            driver.close()
            elapsed = time.time() - start_time
            print(f"✅ Neo4j ready after {elapsed:.1f} seconds")
            return
            
        except Exception as e:
            elapsed = time.time() - start_time
            # Log progress every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"   Still waiting... ({elapsed:.1f}s elapsed, last error: {type(e).__name__})")
            time.sleep(wait_time)
            wait_time = min(wait_time * 1.5, 5)  # Exponential backoff, max 5s
    
    elapsed = time.time() - start_time
    raise TimeoutError(f"Neo4j not ready after {elapsed:.1f} seconds")


@pytest.fixture
def clean_db_with_constraints(neo4j_driver):
    """Provide a clean database with constraints and indexes set up."""
    # Clear the database completely
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        # Drop existing constraints and indexes (Neo4j 4.4 syntax)
        try:
            constraints = session.run("SHOW CONSTRAINTS").data()
            for constraint in constraints:
                constraint_name = constraint.get("name")
                if constraint_name:
                    session.run(f"DROP CONSTRAINT {constraint_name}")
        except Exception:
            pass  # Constraints might not exist
        
        try:
            indexes = session.run("SHOW INDEXES").data()
            for index in indexes:
                index_name = index.get("name")
                if index_name and not index.get("type", "").startswith("BTREE-"):  # Skip system indexes
                    session.run(f"DROP INDEX {index_name}")
        except Exception:
            pass  # Indexes might not exist
        
    # Set up constraints and indexes
    setup_constraints(neo4j_driver)
    
    yield neo4j_driver
    
    # Clean up after test
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture
def repo(clean_db_with_constraints):
    """Provide a Neo4jRepository with clean database and constraints."""
    return Neo4jRepository(clean_db_with_constraints)


@pytest.fixture
def sample_dataset(repo):
    """Create a realistic sample dataset for testing complete workflows."""
    with repo.transaction() as tx:
        # Import here to avoid circular imports
        from .shared_models import Person, Company, Product, WorksAt, Uses
        
        # Create people
        alice = tx.create(Person(
            email="alice@techcorp.com",
            name="Alice Johnson",
            age=28,
            active=True,
            tags=["engineer", "python", "ml"],
            score=95.5
        ))
        
        bob = tx.create(Person(
            email="bob@startupco.com", 
            name="Bob Smith",
            age=32,
            active=True,
            tags=["manager", "product", "strategy"],
            score=88.0
        ))
        
        charlie = tx.create(Person(
            email="charlie@freelance.com",
            name="Charlie Brown",
            age=45,
            active=False,
            tags=["consultant", "architecture"],
            score=92.5
        ))
        
        # Create companies
        techcorp = tx.create(Company(
            name="TechCorp",
            founded=2015,
            industry="Technology"
        ))
        
        startupco = tx.create(Company(
            name="StartupCo",
            founded=2020,
            industry="SaaS"
        ))
        
        # Create products
        ml_platform = tx.create(Product(
            sku="ML-PLAT-001",
            name="ML Platform",
            price=299.99,
            category="Software"
        ))
        
        data_tool = tx.create(Product(
            sku="DATA-TOOL-002",
            name="Data Analysis Tool",
            price=149.99,
            category="Analytics"
        ))
        
        # Create relationships
        tx.relate(alice, WorksAt(role="Senior Engineer", since=2021, salary=120000), techcorp)
        tx.relate(bob, WorksAt(role="Product Manager", since=2022, salary=110000), startupco)
        tx.relate(charlie, WorksAt(role="Consultant", since=2023, salary=150000), techcorp)
        
        tx.relate(alice, Uses(since=2021, frequency="daily"), ml_platform)
        tx.relate(bob, Uses(since=2022, frequency="weekly"), data_tool)
        tx.relate(charlie, Uses(since=2023, frequency="monthly"), ml_platform)
        
    return {
        "people": {"alice": alice, "bob": bob, "charlie": charlie},
        "companies": {"techcorp": techcorp, "startupco": startupco},
        "products": {"ml_platform": ml_platform, "data_tool": data_tool}
    }


@pytest.fixture
def large_dataset(repo):
    """Create a larger dataset for performance testing."""
    with repo.transaction() as tx:
        from .shared_models import Person, Company, WorksAt
        
        # Create multiple companies
        companies = []
        for i in range(10):
            company = tx.create(Company(
                name=f"Company_{i:02d}",
                founded=2000 + i,
                industry=["Technology", "Finance", "Healthcare", "Education"][i % 4]
            ))
            companies.append(company)
        
        # Create many people
        people = []
        for i in range(100):
            person = tx.create(Person(
                email=f"employee_{i:03d}@company.com",
                name=f"Employee {i:03d}",
                age=25 + (i % 40),
                active=(i % 10) != 0,  # 90% active
                tags=[f"skill_{j}" for j in range(i % 5)],
                score=60.0 + (i % 40)
            ))
            people.append(person)
            
            # Connect to random company
            company = companies[i % len(companies)]
            roles = ["Engineer", "Manager", "Analyst", "Designer", "Sales"]
            tx.relate(person, WorksAt(
                role=roles[i % len(roles)],
                since=2018 + (i % 5),
                salary=50000 + (i * 1000)
            ), company)
        
    return {"people": people, "companies": companies}


@pytest.fixture
def performance_timer():
    """Fixture to measure test execution time."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()