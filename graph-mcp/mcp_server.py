#!/usr/bin/env python
"""
NeoAlchemy MCP Server - Provides API tools for working with graph data models.
"""
from typing import Any, Dict, List, Optional, Type, Union, AsyncIterator, get_type_hints, TypeVar
from contextlib import asynccontextmanager
from dataclasses import dataclass
import inspect
from enum import Enum
from pydantic import BaseModel

# No need for custom schema function, we'll use the built-in model_json_schema method
# directly on model classes (Pydantic v2 provides this as a class method)

from mcp.server.fastmcp import FastMCP, Context
from neo4j import GraphDatabase
from neo4j.time import Date, DateTime
from datetime import datetime

# Import our custom models 
# Using models which require source tracking
from models import (
    Person, Project, Team, Account, 
    ConfluenceAttachment, ConfluenceComment, ConfluenceEntity, ConfluencePage, ConfluenceSpace,
    WORKS_ON, BELONGS_TO, MANAGES, HAS_ACCOUNT, AUTHORED, MODIFIED, PARENT_OF, 
    HAS_ATTACHMENT, MENTIONED_IN
)

# Import source tracking functionality
from sources import Source, SourceType, SOURCED_FROM, initialize_sources

from neoalchemy import initialize, setup_constraints
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.repository import Neo4jRepository

# Field expressions and sources will be initialized in app_lifespan

# Define type variables for better type checking
NodeModel = TypeVar('NodeModel', bound=Node)
RelationshipModel = TypeVar('RelationshipModel', bound=Relationship)

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
MODEL_MAP: Dict[str, Union[Type[Node], Type[Relationship]]] = {
    **NODE_MODELS,
    **RELATIONSHIP_MODELS
}

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
        "fields": fields
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
    
    MODEL_FIELDS[name] = {
        "required": required_fields,
        "optional": optional_fields
    }

# Define server resources and endpoints
@mcp.resource("schema://neoalchemy")
def get_schema() -> Dict[str, Any]:
    """Return NeoAlchemy model documentation."""
    return {
        "description": "NeoAlchemy Models",
        "version": "1.0.0",
        "node_models": {name: MODEL_DOCS[name] for name in NODE_MODELS},
        "relationship_models": {name: MODEL_DOCS[name] for name in RELATIONSHIP_MODELS},
        "documentation": {
            "fluent_interface": "docs://neoalchemy/fluent-interface"
        }
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
            }
        ]
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
            node_constraints[name] = {
                "constraints": constraints,
                "indexes": indexes
            }
            
    relationship_constraints = {}
    for name, model_class in Relationship.__registry__.items():
        constraints = model_class.get_constraints()
        indexes = model_class.get_indexes()
        if constraints or indexes:
            relationship_constraints[name] = {
                "constraints": constraints,
                "indexes": indexes
            }
    
    # Set up the constraints
    setup_constraints(driver, drop_existing=True)
    
    return {
        "nodes": node_constraints,
        "relationships": relationship_constraints,
        "message": "Database constraints and indexes set up successfully"
    }

@mcp.tool()
def create_person(
    ctx: Context,
    name: str,
    email: str,
    title: Optional[str] = None,
    phone: Optional[str] = None,
    hire_date: Optional[str] = None,  # ISO date string
    department: str = "",
    primary_location: str = "",
    employee_id: Optional[str] = None,
    source_ids: List[str] = []
) -> Dict[str, Any]:
    """Create a new Person entity with source tracking.
    
    Args:
        ctx: MCP context
        name: Person's full name
        email: Email address (unique identifier)
        title: Job title
        phone: Contact phone number
        hire_date: Date of hire (ISO format: YYYY-MM-DD)
        department: Department name
        primary_location: Primary office location
        employee_id: Employee ID number
        source_ids: List of source IDs to associate with this person
    
    Returns:
        Dictionary containing the created person data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            parsed_hire_date = None
            if hire_date:
                try:
                    year, month, day = hire_date.split('-')
                    parsed_hire_date = Date(int(year), int(month), int(day))
                except ValueError:
                    return {"error": f"Invalid hire_date format. Use YYYY-MM-DD, got: {hire_date}"}
            
            # Create the person
            person = Person(
                name=name,
                email=email,
                title=title,
                phone=phone,
                hire_date=parsed_hire_date,
                department=department,
                primary_location=primary_location,
                employee_id=employee_id,
                sources=source_ids
            )
            
            created_person = tx.create(person)
            
            for source_id in source_ids:
                try:
                    source = tx.query(Source).where(Source.id == source_id).find_one()
                    if source:
                        tx.add_source(created_person, source)
                except Exception:
                    pass  # Continue if source not found
            
            return {
                "success": True,
                "person": created_person.model_dump(),
                "id": str(created_person.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def create_team(
    ctx: Context,
    name: str,
    description: Optional[str] = None,
    department: Optional[str] = None,
    formation_date: Optional[str] = None,  # ISO date string
    source_ids: List[str] = []
) -> Dict[str, Any]:
    """Create a new Team entity with source tracking.
    
    Args:
        ctx: MCP context
        name: Team name (unique identifier)
        description: Team description
        department: Department name
        formation_date: Date when team was formed (ISO format: YYYY-MM-DD)
        source_ids: List of source IDs to associate with this team
    
    Returns:
        Dictionary containing the created team data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            parsed_formation_date = None
            if formation_date:
                try:
                    year, month, day = formation_date.split('-')
                    parsed_formation_date = Date(int(year), int(month), int(day))
                except ValueError:
                    return {"error": f"Invalid formation_date format. Use YYYY-MM-DD, got: {formation_date}"}
            
            # Create the team
            team = Team(
                name=name,
                description=description,
                department=department,
                formation_date=parsed_formation_date,
                sources=source_ids
            )
            
            created_team = tx.create(team)
            
            for source_id in source_ids:
                try:
                    source = tx.query(Source).where(Source.id == source_id).find_one()
                    if source:
                        tx.add_source(created_team, source)
                except Exception:
                    pass  # Continue if source not found
            
            return {
                "success": True,
                "team": created_team.model_dump(),
                "id": str(created_team.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def create_project(
    ctx: Context,
    name: str,
    description: Optional[str] = None,
    start_date: Optional[str] = None,  # ISO date string
    end_date: Optional[str] = None,  # ISO date string
    budget: Optional[float] = None,
    status: str = "planning",
    source_ids: List[str] = []
) -> Dict[str, Any]:
    """Create a new Project entity with source tracking.
    
    Args:
        ctx: MCP context
        name: Project name (unique identifier)
        description: Project description
        start_date: Project start date (ISO format: YYYY-MM-DD)
        end_date: Project end date (ISO format: YYYY-MM-DD)
        budget: Project budget
        status: Current project status
        source_ids: List of source IDs to associate with this project
    
    Returns:
        Dictionary containing the created project data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            parsed_start_date = None
            parsed_end_date = None
            
            if start_date:
                try:
                    year, month, day = start_date.split('-')
                    parsed_start_date = Date(int(year), int(month), int(day))
                except ValueError:
                    return {"error": f"Invalid start_date format. Use YYYY-MM-DD, got: {start_date}"}
            
            if end_date:
                try:
                    year, month, day = end_date.split('-')
                    parsed_end_date = Date(int(year), int(month), int(day))
                except ValueError:
                    return {"error": f"Invalid end_date format. Use YYYY-MM-DD, got: {end_date}"}
            
            # Create the project
            project = Project(
                name=name,
                description=description,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                budget=budget,
                status=status,
                sources=source_ids
            )
            
            created_project = tx.create(project)
            
            for source_id in source_ids:
                try:
                    source = tx.query(Source).where(Source.id == source_id).find_one()
                    if source:
                        tx.add_source(created_project, source)
                except Exception:
                    pass  # Continue if source not found
            
            return {
                "success": True,
                "project": created_project.model_dump(),
                "id": str(created_project.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def create_source(
    ctx: Context,
    name: str,
    type: str,  # SourceType enum value
    description: Optional[str] = None,
    url: Optional[str] = None,
    identifier: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new Source entity for tracking data lineage.
    
    Args:
        ctx: MCP context
        name: Source name
        type: Source type (jira, confluence, slack, teams, email, github, etc.)
        description: Optional description
        url: Optional URL to the source
        identifier: Optional identifier (e.g., Jira issue key)
    
    Returns:
        Dictionary containing the created source data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            try:
                source_type = SourceType(type.lower())
            except ValueError:
                valid_types = [t.value for t in SourceType]
                return {"error": f"Invalid source type '{type}'. Valid types: {valid_types}"}
            
            # Create the source
            source = Source(
                name=name,
                type=source_type,
                description=description,
                url=url,
                identifier=identifier
            )
            
            created_source = tx.create(source)
            
            return {
                "success": True,
                "source": created_source.model_dump(),
                "id": str(created_source.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def create_llm_source(
    ctx: Context,
    name: str,
    model_name: str,
    description: Optional[str] = None,
    prompt_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new LLM Source entity for tracking AI-generated data.
    
    Args:
        ctx: MCP context
        name: Source name
        model_name: Name of the LLM model used (e.g., "claude-3-opus")
        description: Optional description
        prompt_id: Optional identifier for the prompt used
    
    Returns:
        Dictionary containing the created LLM source data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            # Create the LLM source
            source = Source(
                name=name,
                type=SourceType.LLM,
                description=description or f"Generated by {model_name}",
                identifier=prompt_id,
                url=None
            )
            
            # This is a bit of a hack, but allows storing the model name
            source.timestamp = DateTime.from_native(datetime.now())
            
            created_source = tx.create(source)
            
            return {
                "success": True,
                "source": created_source.model_dump(),
                "id": str(created_source.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def add_source_relationship(
    ctx: Context,
    entity_id: str,
    source_id: str,
    method: Optional[str] = None,
    confidence: float = 1.0,
    primary: bool = False,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """Add a source relationship to an existing entity.
    
    Args:
        ctx: MCP context
        entity_id: ID of the entity to link to source
        source_id: ID of the source
        method: Method used to extract/infer the data
        confidence: Confidence level (0.0 to 1.0)
        primary: Whether this is the primary source for the entity
        context: Additional context about the relationship
    
    Returns:
        Dictionary containing operation result
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            entity = None
            for model_class in [Person, Team, Project]:
                try:
                    entity = tx.query(model_class).where(model_class.id == entity_id).find_one()
                    if entity:
                        break
                except Exception:
                    continue
            
            if not entity:
                return {"error": f"Entity with ID {entity_id} not found"}
            
            source = tx.query(Source).where(Source.id == source_id).find_one()
            if not source:
                return {"error": f"Source with ID {source_id} not found"}
            
            # Add the source relationship
            relationship = tx.add_source(
                entity, source, method=method, confidence=confidence, 
                primary=primary, context=context
            )
            
            return {
                "success": True,
                "message": f"Added source relationship between entity {entity_id} and source {source_id}"
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def create_relationship(
    ctx: Context,
    from_entity_id: str,
    to_entity_id: str,
    relationship_type: str,
    properties: Dict[str, Any] = {},
    source_ids: List[str] = []
) -> Dict[str, Any]:
    """Create a relationship between two entities.
    
    Args:
        ctx: MCP context
        from_entity_id: ID of the source entity
        to_entity_id: ID of the target entity
        relationship_type: Type of relationship (WORKS_ON, BELONGS_TO, MANAGES, HAS_ACCOUNT)
        properties: Additional properties for the relationship
        source_ids: List of source IDs for the relationship
    
    Returns:
        Dictionary containing the created relationship data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            # Find the entities
            from_entity = None
            to_entity = None
            
            for model_class in [Person, Team, Project]:
                if not from_entity:
                    try:
                        from_entity = tx.query(model_class).where(model_class.id == from_entity_id).find_one()
                    except Exception:
                        continue
                if not to_entity:
                    try:
                        to_entity = tx.query(model_class).where(model_class.id == to_entity_id).find_one()
                    except Exception:
                        continue
            
            if not from_entity:
                return {"error": f"From entity with ID {from_entity_id} not found"}
            if not to_entity:
                return {"error": f"To entity with ID {to_entity_id} not found"}
            
            # Create the appropriate relationship type
            relationship = None
            if relationship_type.upper() == "WORKS_ON":
                relationship = WORKS_ON(
                    role=properties.get("role", ""),
                    joined_date=properties.get("joined_date"),
                    allocation_percentage=properties.get("allocation_percentage", 100.0),
                    sources=source_ids
                )
            elif relationship_type.upper() == "BELONGS_TO":
                relationship = BELONGS_TO(
                    role=properties.get("role"),
                    joined_date=properties.get("joined_date"),
                    sources=source_ids
                )
            elif relationship_type.upper() == "MANAGES":
                relationship = MANAGES(
                    since=properties.get("since"),
                    sources=source_ids
                )
            elif relationship_type.upper() == "HAS_ACCOUNT":
                relationship = HAS_ACCOUNT(
                    is_primary=properties.get("is_primary", False),
                    verified=properties.get("verified", False),
                    sources=source_ids
                )
            else:
                return {"error": f"Unsupported relationship type: {relationship_type}"}
            
            # Create the relationship
            created_relationship = tx.relate(from_entity, relationship, to_entity)
            
            for source_id in source_ids:
                try:
                    source = tx.query(Source).where(Source.id == source_id).find_one()
                    if source:
                        tx.add_source(relationship, source)
                except Exception:
                    pass  # Continue if source not found
            
            return {
                "success": True,
                "relationship": {
                    "type": relationship_type,
                    "from": str(from_entity_id),
                    "to": str(to_entity_id),
                    "properties": properties
                }
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def query_entities(
    ctx: Context,
    entity_type: str,
    filters: Dict[str, Any] = {},
    limit: int = 100
) -> Dict[str, Any]:
    """Query entities of a specific type with optional filters.
    
    Args:
        ctx: MCP context
        entity_type: Type of entity to query (Person, Team, Project)
        filters: Dictionary of field filters (e.g., {"name": "Alice", "department": "Engineering"})
        limit: Maximum number of results to return
    
    Returns:
        Dictionary containing the query results
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            # Get the model class
            model_class = None
            if entity_type.lower() == "person":
                model_class = Person
            elif entity_type.lower() == "team":
                model_class = Team
            elif entity_type.lower() == "project":
                model_class = Project
            else:
                return {"error": f"Unsupported entity type: {entity_type}"}
            
            query = tx.query(model_class)
            
            for field, value in filters.items():
                if hasattr(model_class, field):
                    field_expr = getattr(model_class, field)
                    query = query.where(field_expr == value)
            
            results = query.limit(limit).find()
            
            serialized_results = []
            for result in results:
                serialized_results.append(result.model_dump())
            
            return {
                "success": True,
                "entity_type": entity_type,
                "count": len(serialized_results),
                "results": serialized_results
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_entity_sources(
    ctx: Context,
    entity_id: str
) -> Dict[str, Any]:
    """Get all sources associated with an entity.
    
    Args:
        ctx: MCP context
        entity_id: ID of the entity
    
    Returns:
        Dictionary containing the entity's sources
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            entity = None
            for model_class in [Person, Team, Project]:
                try:
                    entity = tx.query(model_class).where(model_class.id == entity_id).find_one()
                    if entity:
                        break
                except Exception:
                    continue
            
            if not entity:
                return {"error": f"Entity with ID {entity_id} not found"}
            
            # Get sources for this entity
            sources = tx.get_sources(entity)
            
            serialized_sources = []
            for source in sources:
                serialized_sources.append(source.model_dump())
            
            return {
                "success": True,
                "entity_id": entity_id,
                "sources": serialized_sources
            }
            
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def merge_entity(
    ctx: Context,
    entity_type: str,
    **properties
) -> Dict[str, Any]:
    """Create or update an entity based on unique constraints.
    
    This tool uses the merge operation to create a new entity if it doesn't exist,
    or update an existing entity if one with the same unique constraint value exists.
    
    Args:
        ctx: MCP context
        entity_type: Type of entity to merge (Person, Team, Project)
        **properties: Entity properties as keyword arguments
    
    Returns:
        Dictionary containing the merged entity data
    """
    driver = ctx.request_context.lifespan_context.driver
    repo = ctx.request_context.lifespan_context.repo
    
    try:
        with repo.transaction() as tx:
            # Get the model class
            model_class = None
            if entity_type.lower() == "person":
                model_class = Person
            elif entity_type.lower() == "team":
                model_class = Team
            elif entity_type.lower() == "project":
                model_class = Project
            else:
                return {"error": f"Unsupported entity type: {entity_type}"}
            
            # Handle date fields
            for date_field in ["hire_date", "formation_date", "start_date", "end_date"]:
                if date_field in properties and isinstance(properties[date_field], str):
                    try:
                        year, month, day = properties[date_field].split('-')
                        properties[date_field] = Date(int(year), int(month), int(day))
                    except (ValueError, AttributeError):
                        return {"error": f"Invalid {date_field} format. Use YYYY-MM-DD"}
            
            merged_entity = tx.merge(model_class, **properties)
            
            return {
                "success": True,
                "entity": merged_entity.model_dump(),
                "id": str(merged_entity.id)
            }
            
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
