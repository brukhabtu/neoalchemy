# NeoAlchemy

A SQLAlchemy-inspired Pythonic ORM for Neo4j, focused on clean syntax and type safety.

## Overview

NeoAlchemy provides a high-level, intuitive API for working with Neo4j graph databases using Pydantic models with a transaction-based interface. It brings the familiarity of SQLAlchemy-like ORMs to Neo4j, making it easier for Python developers to work with graph databases.

## Features

- **Pydantic Integration**: Built on Pydantic for modern, type-safe data models
- **Pythonic Query API**: Natural Python syntax for query building
- **Transaction-based**: All operations are performed within transaction contexts
- **Type Hinting**: Comprehensive type annotations for better IDE support
- **Expressive Query Language**: Using Python operators for complex query conditions

## Installation

```bash
pip install neoalchemy
```

## Quick Start

### Define Models

```python
from pydantic import Field
from neoalchemy.models import Node, Relationship
from neoalchemy import initialize

# Always call initialize() to register field expressions
initialize()

class Person(Node):
    name: str
    age: int
    email: str = ""
    active: bool = True
    tags: list[str] = []

class Company(Node):
    name: str
    founded: int
    industry: str = ""

class WORKS_FOR(Relationship):
    role: str
    since: int
```

### Connect to Neo4j and Perform Operations

```python
from neo4j import GraphDatabase
from neoalchemy import Neo4jRepository

# Create a Neo4j driver
driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))

# Create a repository
repo = Neo4jRepository(driver)

# All operations must be performed within a transaction
with repo.transaction() as tx:
    # Create entities
    alice = tx.create(Person(name="Alice", age=30, tags=["developer", "python"]))
    acme = tx.create(Company(name="Acme Inc", founded=1990, industry="Technology"))
    
    # Create a relationship
    tx.relate(alice, WORKS_FOR(role="Engineer", since=2020), acme)
    
    # Query with various conditions
    # Standard comparison operators
    adults = tx.query(Person).where(Person.age > 18).find()
    
    # Chained comparisons (Pythonic range operations)
    middle_aged = tx.query(Person).where(25 <= Person.age <= 35).find()
    
    # Using 'in' operator for string/array content
    python_devs = tx.query(Person).where("python" in Person.tags).find()
    
    # String operations - both formats work
    emails1 = tx.query(Person).where(Person.email.ends_with("@example.com")).find()
    emails2 = tx.query(Person).where(Person.email.endswith("@example.com")).find()  # Pythonic form
    
    # Reversed containment check (field in collection)
    managers = tx.query(Person).where(Person.role in ["manager", "director"]).find()
    
    # Ordering and limiting
    top_three = tx.query(Person).order_by(Person.age, descending=True).limit(3).find()
```

## Key Concepts

### Models

Models define the structure of your Neo4j nodes and relationships:

- **Node**: Base class for entities stored as Neo4j nodes
- **Relationship**: Base class for relationships between nodes

### Repository

The `Neo4jRepository` provides a transaction-based interface for all database operations.

### Transactions

All database operations must be performed within a transaction context:

```python
with repo.transaction() as tx:
    # Database operations here
    ...
```

### Expressions

The expression system allows you to build complex query conditions using Python operators:

- **Comparison**: `==`, `!=`, `>`, `<`, `>=`, `<=`
- **Logical**: `&` (AND), `|` (OR), `~` (NOT)
- **Chained comparisons**: `25 <= Person.age <= 35`
- **Containment**: `"Smith" in Person.last_name`
- **Reversed containment**: `Person.role in ["admin", "manager"]`
- **String operations**: 
  - `.starts_with()`, `.ends_with()`
  - `.startswith()`, `.endswith()` (Pythonic aliases matching built-in methods)

## Advanced Features

### Custom Node Labels

```python
class Person(Node):
    __label__ = "User"  # Override the Neo4j label
    name: str
    age: int
```

### Relationship Types

```python
class FOLLOWS(Relationship):
    __type__ = "FOLLOWS_USER"  # Override the relationship type
    since: int
```

### Functional Queries

```python
# String length operations
long_names = tx.query(Person).where(Person.name.len() > 10).find()

# Case-insensitive search
case_insensitive = tx.query(Person).where(Person.name.lower() == "alice").find()
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.