#!/usr/bin/env python
"""
NeoAlchemy MCP Server - Provides API tools for working with graph data models.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Type, TypeVar, Union, get_type_hints

# No need for custom schema function, we'll use the built-in model_json_schema method
# directly on model classes (Pydantic v2 provides this as a class method)
from mcp.server.fastmcp import Context, FastMCP
from neo4j import GraphDatabase

# Import our custom models
# Using sourced models which require source tracking
# Import source tracking functionality
from sources import initialize_sources

from neoalchemy import initialize, setup_constraints
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.repository import Neo4jRepository

# Field expressions and sources will be initialized in app_lifespan

# Define type variables for better type checking
NodeModel = TypeVar("NodeModel", bound=Node)
RelationshipModel = TypeVar("RelationshipModel", bound=Relationship)

# Type alias for model name strings (for documentation purposes)
ModelName = str

# Create a named server with dependencies
mcp = FastMCP("NeoAlchemy", dependencies=["neo4j"])


@dataclass
class AppContext:
    driver: GraphDatabase.driver
    repo: Neo4jRepository


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage Neo4j connection lifecycle with type-safe context"""
    # Initialize on startup
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_secure_password"))
    repo = Neo4jRepository(driver)

    # Initialize field expressions for all models
    initialize()

    # Initialize source mechanism for tracking data lineage
    initialize_sources()

    # Setup constraints for registered models
    setup_constraints(driver)

    try:
        yield AppContext(driver=driver, repo=repo)
    finally:
        # Cleanup on shutdown
        driver.close()


# Pass lifespan to server
mcp = FastMCP("NeoAlchemy", dependencies=["neo4j", "neoalchemy"], lifespan=app_lifespan)

# Access the model registries from the base classes
# These contain all registered subclasses
NODE_MODELS = Node.__registry__
RELATIONSHIP_MODELS = Relationship.__registry__

# Combined model map for all models
MODEL_MAP: Dict[str, Union[Type[Node], Type[Relationship]]] = {**NODE_MODELS, **RELATIONSHIP_MODELS}


def generate_model_docs(model_class: Type) -> Dict[str, Any]:
    """Generate documentation for a model class.

    Args:
        model_class: The model class to generate documentation for

    Returns:
        Dictionary containing the model documentation
    """
    # Determine if this is a Node or Relationship model
    model_type = "Node" if issubclass(model_class, Node) else "Relationship"

    # Get model annotations
    annotations = get_type_hints(model_class)

    # Extract field information
    fields = {}
    for field_name, field_type in annotations.items():
        # Skip private fields
        if field_name.startswith("_"):
            continue

        # Handle Optional types
        origin = getattr(field_type, "__origin__", None)
        args = getattr(field_type, "__args__", [])

        is_optional = origin is Union and type(None) in args
        if is_optional:
            # Get the actual type (first non-None type)
            actual_types = [arg for arg in args if arg is not type(None)]
            if actual_types:
                field_type = actual_types[0]

        # Get type name
        if hasattr(field_type, "__name__"):
            type_name = field_type.__name__
        else:
            type_name = str(field_type).replace("typing.", "")

        # Get default value
        default_value = None
        if hasattr(model_class, field_name) and not field_name.startswith("__"):
            default_value = getattr(model_class, field_name)

        field_info = {
            "type": type_name,
            "required": not is_optional,
        }

        if default_value is not None:
            field_info["default"] = str(default_value)

        fields[field_name] = field_info

    # Build model docs
    model_docs = {
        "type": model_type,
        "description": model_class.__doc__ or f"{model_class.__name__} model",
        "fields": fields,
    }

    # Add Neo4j specific information
    if model_type == "Node":
        model_docs["label"] = getattr(model_class, "__label__", model_class.__name__)
    else:
        model_docs["rel_type"] = getattr(model_class, "__type__", model_class.__name__.upper())

    return model_docs


# Generate documentation for all models
MODEL_DOCS = {name: generate_model_docs(model_class) for name, model_class in MODEL_MAP.items()}

# Extract field lists for each model (required vs optional)
MODEL_FIELDS = {}
for name, docs in MODEL_DOCS.items():
    required_fields = []
    optional_fields = []

    for field_name, field_info in docs["fields"].items():
        if field_info.get("required", False):
            required_fields.append(field_name)
        else:
            optional_fields.append(field_name)

    MODEL_FIELDS[name] = {"required": required_fields, "optional": optional_fields}


# Define server resources and endpoints
@mcp.resource("schema://neoalchemy")
def get_schema() -> Dict[str, Any]:
    """Return NeoAlchemy model documentation."""
    return {
        "description": "NeoAlchemy Models",
        "version": "1.0.0",
        "node_models": {name: MODEL_DOCS[name] for name in NODE_MODELS},
        "relationship_models": {name: MODEL_DOCS[name] for name in RELATIONSHIP_MODELS},
        "documentation": {"fluent_interface": "docs://neoalchemy/fluent-interface"},
    }


@mcp.resource("docs://neoalchemy/fluent-interface")
def get_fluent_interface_docs() -> Dict[str, Any]:
    """Return code examples for NeoAlchemy's fluent interface."""
    return {
        "title": "NeoAlchemy Fluent Interface",
        "examples": [
            {
                "title": "Working with Sources and Entities",
                "code": """
# Note: All queries are automatically wrapped in a transaction context
# with access to the 'tx' variable

# Initialize the sources extension
initialize_sources()

# IMPORTANT: All nodes and relationships must have at least one source
# Create a source for our data
jira_source = tx.create_source(
    name="PROJ-123", 
    type=SourceType.JIRA,
    description="Project planning ticket",
    url="https://company.atlassian.net/browse/PROJ-123"
)

# Create nodes with sources
alice = Person(
    name="Alice", 
    email="alice@example.com", 
    title="Developer",
    sources=[str(jira_source.id)]  # Required for all SourcedNode entities
)
created_alice = tx.create(alice)

# Connect the entity to the source with relationship metadata
tx.add_source(
    created_alice,
    jira_source,
    method="Jira Field Extraction", 
    confidence=0.95,
    primary=True,
    context="Extracted from assignee field"
)

# Create a team with source
team = Team(
    name="Engineering", 
    department="Product",
    sources=[str(jira_source.id)]
)
created_team = tx.create(team)
tx.add_source(created_team, jira_source)

# Create a project with source - using convenience method
project = Project(
    name="API Redesign", 
    status="planning",
    sources=[]  # Will be populated by create_with_source
)
created_project = tx.create_with_source(
    project,
    jira_source,
    method="Jira Fields",
    confidence=0.9
)

# Read nodes
# Find all of a type
all_people = tx.query(Person).find()

# Find with condition
devs = tx.query(Person).where(Person.title == "Developer").find()

# Find entities by their source
jira_entities = tx.find_entities_by_source(jira_source, Person)

# Get sources for an entity
alice_sources = tx.get_sources(created_alice)

# Get primary source
primary_source = tx.get_primary_source(created_project)

# Set the result to return
result = {
    "created": created_alice.model_dump(),
    "found_people": len(all_people),
    "found_devs": len(devs),
    "sources": len(alice_sources)
}
""",
            },
            {
                "title": "Query Options",
                "code": """
# Comparison operators
# Note: All examples are inside the auto-wrapped transaction context

# Greater than
high_risks = tx.query(Risk).where(Risk.impact > 0.7).find()

# Range check (Python's chained comparison)
budget_projects = tx.query(Project).where(10000 <= Project.budget <= 50000).find()

# Logical AND using multiple where() calls
senior_devs = tx.query(Person).where(Person.title == "Developer").where(Person.experience > 5).find()

# Logical AND using comma-separated conditions in a single where()
senior_devs = tx.query(Person).where(
    Person.title == "Developer", 
    Person.experience > 5
).find()

# Membership tests
managers = tx.query(Person).where(Person.title.in_list(["Manager", "Director"])).find()
# Alternative using direct in_list method
managers = tx.query(Person).where(Person.title.one_of("Manager", "Director")).find()

# String operations
a_names = tx.query(Person).where(Person.name.startswith("A")).find()
company_emails = tx.query(Person).where(Person.email.endswith("@company.com")).find()

# Containment - for strings or arrays
smith_people = tx.query(Person).where("Smith" in Person.name).find()
python_devs = tx.query(Person).where("python" in Person.skills).find()

# Date-based queries
from neo4j.time import Date
recent_hires = tx.query(Person).where(Person.hire_date >= Date(2022, 1, 1)).find()

# Sorting & pagination
ordered_people = tx.query(Person).order_by(Person.name).find()
top_risks = tx.query(Risk).order_by(Risk.impact, descending=True).limit(3).find()
page_2 = tx.query(Person).skip(10).limit(10).find()

# Set result to return
result = {
    "high_risks": len(high_risks),
    "budget_projects": len(budget_projects),
    "recent_hires": len(recent_hires),
    "ordered_people": len(ordered_people)
}
""",
            },
            {
                "title": "Working with Relationships and Sources",
                "code": """
# Create and query relationships with source tracking
# Note: All code runs in an auto-wrapped transaction context

# Initialize the sources extension if not already done
initialize_sources()

# First, create a source for our data
slack_source = tx.create_source(
    name="Team Planning", 
    type=SourceType.SLACK,
    description="Team planning discussion in #planning channel"
)

# Find our nodes
alice = tx.query(Person).where(Person.name == "Alice").find_one()
team = tx.query(Team).where(Team.name == "Engineering").find_one()
project = tx.query(Project).where(Project.name == "API Redesign").find_one()

if alice and team and project:
    # Create relationships with sources
    
    # Person belongs to Team
    belongs_rel = BELONGS_TO(
        role="Lead",
        sources=[str(slack_source.id)]  # Required for all SourcedRelationship entities
    )
    created_belongs = tx.relate(alice, belongs_rel, team)
    tx.add_source(
        belongs_rel,
        slack_source,
        method="Slack Message Extraction", 
        confidence=0.9,
        context="Mentioned as team lead in Slack"
    )
    
    # Person manages Team with date - using convenience method
    from neo4j.time import Date
    manages_rel = MANAGES(
        since=Date(2023, 1, 1),
        sources=[]  # Will be populated by relate_with_source
    )
    manages_rel = tx.relate_with_source(
        alice, 
        manages_rel, 
        team,
        slack_source,
        method="Slack Message", 
        confidence=0.85
    )
    
    # Use LLM source for an inferred relationship
    # This is useful when an AI detects or suggests a relationship
    works_rel = WORKS_ON(
        role="Lead",
        allocation_percentage=75,
        sources=[]  # Will be populated by relate_with_llm_source
    )
    works_rel = tx.relate_with_llm_source(
        alice, 
        works_rel, 
        project,
        model_name="claude-3-opus",
        method="Email Content Analysis",
        confidence=0.8,
        context="Inferred from email content"
    )
    
    # Query with relationships
    
    # Find person's team
    teams = tx.query(Team).related_from(alice, BELONGS_TO).find()
    print(f"Alice belongs to {len(teams)} teams")
    
    # Find team members
    members = tx.query(Person).related_to(team, BELONGS_TO).find()
    print(f"Team has {len(members)} members")
    
    # Find with relationship filter
    leads = tx.query(Person).related_to(
        project, WORKS_ON, 
        relationship_filter=WORKS_ON.role == "Lead"
    ).find()
    print(f"Project has {len(leads)} leads")
    
    # Get sources for a relationship
    belongs_sources = tx.get_sources(belongs_rel)
    print(f"Relationship has {len(belongs_sources)} sources")
    
    # Set result to return
    result = {
        "teams": [t.name for t in teams],
        "members": [m.name for m in members],
        "leads": [l.name for l in leads],
        "sources": [s.name for s in belongs_sources]
    }
else:
    print("One or more nodes not found, please create them first")
    result = {"error": "Nodes not found"}
""",
            },
            {
                "title": "Working with Constraints and Merge",
                "code": """
# Demonstrate constraint-based operations
# Note: All code runs in an auto-wrapped transaction context

# Create a new person or update if exists by email (using merge)
person = tx.merge(
    Person,
    name="John Smith",
    email="john.smith@company.com",  # Unique constraint field
    title="Developer",
    department="Engineering"
)

print(f"Created or updated person: {person.name} (id: {person.id})")

# Try to create another with same email (will fail due to constraint)
try:
    # This would fail if run directly with create()
    duplicate_person = Person(
        name="Different Name",
        email="john.smith@company.com",  # Same email
        title="Senior Developer", 
        sources=[]  # Will be populated below
    )
    
    # We'll create a source first
    email_source = tx.create_source(
        name="Email System",
        type=SourceType.EMAIL,
        description="Corporate email system"
    )
    
    # Instead of failing, let's use merge which will update the existing record
    updated_person = tx.merge(
        Person,
        name="John Smith Updated", 
        email="john.smith@company.com",  # Same email
        title="Senior Developer",
        department="R&D"
    )
    
    # Add the source to the merged entity
    updated_person.add_source_id(email_source.id)
    tx.update(updated_person)
    
    print(f"Updated person via merge: {updated_person.name}, title: {updated_person.title}")
    
    # Check how many with this email exist (should be only 1)
    count = tx.query(Person).where(Person.email == "john.smith@company.com").count()
    print(f"Number of people with email john.smith@company.com: {count}")
    
    # Let's try another merge with a team
    team = tx.merge(
        Team,
        name="Engineering Team",  # Team name is unique
        department="Engineering", 
        description="Core engineering team"
    )
    
    # Create a relationship between the person and team
    belongs_rel = BELONGS_TO(
        role="Developer", 
        sources=[str(email_source.id)]
    )
    tx.relate(updated_person, belongs_rel, team)
    
    result = {
        "person": updated_person.model_dump(),
        "team": team.model_dump(),
        "person_count": count,
        "message": "Merge operations completed successfully"
    }
    
except Exception as e:
    print(f"Error: {str(e)}")
    result = {
        "error": str(e),
        "message": "See explanation in error message"
    }
""",
            },
            {
                "title": "Complete Graph Example",
                "code": """
# Create a complete graph structure
# Note: All code runs in an auto-wrapped transaction context

# Import Neo4j date/time types and datetime
from neo4j.time import Date, DateTime
from datetime import datetime

# 1. Create nodes
alice = Person(
    name="Alice", 
    email="alice@company.com", 
    title="Team Lead",
    hire_date=Date(2020, 5, 15)
)
bob = Person(
    name="Bob", 
    email="bob@company.com", 
    title="Developer",
    hire_date=Date(2021, 9, 1)
)
team = Team(
    name="Backend", 
    department="Engineering",
    formation_date=Date(2019, 12, 1)
)
project = Project(
    name="API Redesign", 
    description="Building better APIs with NeoAlchemy",
    status="in_progress",
    start_date=Date(2023, 1, 10),
    end_date=Date(2023, 6, 30),
    budget=75000.0
)
database = Topic(
    name="Neo4j", 
    category="Database",
    description="Graph database technology"
)
risk = Risk(
    name="Performance Issues", 
    description="API might not handle load", 
    level=RiskLevel.HIGH,
    identification_date=DateTime.from_native(datetime.now())
)

# 2. Save all nodes
created_nodes = {}
for node in [alice, bob, team, project, database, risk]:
    created = tx.create(node)
    created_nodes[node.__class__.__name__] = created

# 3. Create relationships
tx.relate(created_nodes["Person"], BELONGS_TO(role="Lead"), created_nodes["Team"])
tx.relate(bob, BELONGS_TO(role="Member"), created_nodes["Team"])
tx.relate(created_nodes["Person"], MANAGES(since=Date(2021, 1, 1)), created_nodes["Team"])
tx.relate(created_nodes["Person"], WORKS_ON(role="Lead", allocation_percentage=75), created_nodes["Project"])
tx.relate(bob, WORKS_ON(role="Developer", allocation_percentage=100), created_nodes["Project"])
tx.relate(bob, HAS_EXPERTISE(level="expert", years_experience=3.5), created_nodes["Topic"])
tx.relate(created_nodes["Project"], INVOLVES(importance=0.7), created_nodes["Topic"])
tx.relate(created_nodes["Risk"], THREATENS(identified_by=created_nodes["Person"].id), created_nodes["Project"])

# Set result to return
result = {
    "created_nodes": {k: v.model_dump() for k, v in created_nodes.items()},
    "message": "Complete graph structure created successfully"
}
""",
            },
            {
                "title": "Searching All Nodes of a Specific Type",
                "code": """
# Find all nodes of a specific model type
# Note: All code runs in an auto-wrapped transaction context

# Find counts of all node types
all_people = tx.query(Person).find()
all_projects = tx.query(Project).find()
all_teams = tx.query(Team).find()
all_topics = tx.query(Topic).find()
all_risks = tx.query(Risk).find()

# Print summary
print(f"Found {len(all_people)} Person nodes")
print(f"Found {len(all_projects)} Project nodes") 
print(f"Found {len(all_teams)} Team nodes")
print(f"Found {len(all_topics)} Topic nodes")
print(f"Found {len(all_risks)} Risk nodes")

# Get details for each person with their relationships
person_details = []
for person in all_people:
    # Basic details
    person_info = {
        "id": str(person.id),
        "name": person.name,
        "email": person.email,
        "title": person.title,
        "hire_date": str(person.hire_date) if person.hire_date else None
    }
    
    # Find related teams
    teams = tx.query(Team).related_from(person, BELONGS_TO).find()
    if teams:
        person_info["teams"] = [team.name for team in teams]
    
    # Find projects this person works on
    projects = tx.query(Project).related_from(person, WORKS_ON).find()
    if projects:
        person_info["projects"] = [project.name for project in projects]
    
    # Find topics of expertise
    expertise = tx.query(Topic).related_from(person, HAS_EXPERTISE).find()
    if expertise:
        person_info["expertise"] = [topic.name for topic in expertise]
        
    person_details.append(person_info)
    
    # Print details to console
    print(f"Person: {person.name} ({person.id})")
    print(f"  Email: {person.email}")
    print(f"  Title: {person.title}")
    print(f"  Hire date: {person.hire_date}")
    
    if teams:
        print(f"  Teams: {', '.join(team.name for team in teams)}")
    if projects:
        print(f"  Projects: {', '.join(project.name for project in projects)}")
    if expertise:
        print(f"  Expertise: {', '.join(topic.name for topic in expertise)}")

# Set result to return
result = {
    "counts": {
        "people": len(all_people),
        "projects": len(all_projects),
        "teams": len(all_teams),
        "topics": len(all_topics),
        "risks": len(all_risks)
    },
    "person_details": person_details
}
""",
            },
        ],
    }


@mcp.tool()
def setup_database_constraints(ctx: Context) -> Dict[str, Any]:
    """Set up all constraints and indexes for registered models.

    This tool sets up database constraints based on model field definitions.
    It creates unique constraints and indexes as defined in the models.

    Args:
        ctx: The MCP context object

    Returns:
        Information about constraints created
    """
    driver = ctx.request_context.lifespan_context.driver

    # Initialize if needed
    initialize()
    initialize_sources()

    # Get all models and their constraints
    node_constraints = {}
    for name, model_class in Node.__registry__.items():
        constraints = model_class.get_constraints()
        indexes = model_class.get_indexes()
        if constraints or indexes:
            node_constraints[name] = {"constraints": constraints, "indexes": indexes}

    relationship_constraints = {}
    for name, model_class in Relationship.__registry__.items():
        constraints = model_class.get_constraints()
        indexes = model_class.get_indexes()
        if constraints or indexes:
            relationship_constraints[name] = {"constraints": constraints, "indexes": indexes}

    # Set up the constraints
    setup_constraints(driver, drop_existing=True)

    return {
        "nodes": node_constraints,
        "relationships": relationship_constraints,
        "message": "Database constraints and indexes set up successfully",
    }


# NeoAlchemy code execution tool
@mcp.tool()
def run_query(ctx: Context, code: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    """Run NeoAlchemy query to interact with the graph database.

    This tool executes NeoAlchemy code to create, read, update or delete nodes
    and relationships in the graph database. Code is automatically wrapped in a
    transaction, so you can directly use the 'tx' variable to execute queries.

    IMPORTANT: All nodes and relationships require at least one source.
    Each entity must track where the data originated from.

    Examples:
        # Find all Projects
        run_query(code='''
        projects = tx.query(Project).find()
        result = projects  # Set the result to return
        ''')

        # Create a new Person with a source
        run_query(code='''
        from neo4j.time import Date

        # First create a source
        jira_source = tx.create_source(
            name="PROJ-123",
            type=SourceType.JIRA,
            description="Team member list",
            url="https://company.atlassian.net/browse/PROJ-123"
        )

        # Create person with required sources list
        person = Person(
            name="Alice",
            email="alice@example.com",
            hire_date=Date(2023, 1, 15),
            sources=[str(jira_source.id)]  # Required by SourcedNode
        )

        # Create the person and add source relationship
        created = tx.create(person)
        tx.add_source(
            created,
            jira_source,
            method="Jira Issue Fields",
            confidence=0.95,
            primary=True
        )

        result = created  # Set the result to return
        ''')

        # Create a person with an LLM source (AI inference)
        run_query(code='''
        # Create person with LLM source in one operation
        person = Person(
            name="Bob Smith",
            email="bob@example.com",
            sources=[]  # Will be populated by create_with_llm_source
        )

        # Convenience method to create entity with LLM source
        created = tx.create_with_llm_source(
            person,
            model_name="claude-3-opus",
            method="Email Content Analysis",
            confidence=0.85,
            context="Inferred from email thread analysis"
        )

        result = created
        ''')

        # Add a relationship with source tracking
        run_query(code='''
        # Find entities
        alice = tx.query(Person).where(Person.name == "Alice").find_one()
        project = tx.query(Project).where(Project.name == "API Project").find_one()

        if alice and project:
            # Create a source for this relationship
            slack_source = tx.create_source(
                name="Team Discussion",
                type=SourceType.SLACK,
                description="Team planning discussion"
            )

            # Create relationship with sources list
            works_on_rel = WORKS_ON(
                role="Developer",
                allocation_percentage=75.0,
                sources=[str(slack_source.id)]  # Required by SourcedRelationship
            )

            # Create the relationship and track the source
            rel = tx.relate(alice, works_on_rel, project)

            result = {"message": "Created relationship with source tracking"}
        else:
            result = {"error": "Entities not found"}
        ''')

        # Use merge to create or update without duplicates
        run_query(code='''
        # Use merge to create or update a person by email
        person = tx.merge(
            Person,
            name="John Smith",
            email="john@example.com",  # Unique constraint field
            title="Developer"
        )

        result = person  # Will be a new or updated entity
        ''')

    Args:
        ctx: The MCP context object containing the request context
        code: Python code using NeoAlchemy's fluent interface with 'tx' variable
        timeout_seconds: Maximum execution time in seconds (default: 10)

    Returns:
        Dictionary containing execution results including:
        - stdout: Any printed output
        - result: The returned value from the code
        - error: Any error message (if execution failed)
    """
    # Get the Neo4j driver from the context
    driver = ctx.request_context.lifespan_context.driver

    # Import the safe execution environment
    from safe_run import run_neoalchemy_code

    # Execute the code safely
    result = run_neoalchemy_code(code=code, driver=driver, timeout_seconds=timeout_seconds)

    return result


if __name__ == "__main__":
    mcp.run()
