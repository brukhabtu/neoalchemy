# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# NeoAlchemy Development Guidelines

## Project Overview
This repository contains two main components:

1. **NeoAlchemy ORM** (`neoalchemy/`) - A SQLAlchemy-inspired ORM for Neo4j that provides a Pythonic API for working with Neo4j graph databases using Pydantic models with a transaction-based interface.

2. **MCP Server** (`graph-mcp/`) - A Model Context Protocol server that provides AI agents (like Claude) with structured access to Neo4j operations through the NeoAlchemy ORM.

Both components share the same Neo4j database and work together to provide both programmatic access (via NeoAlchemy) and AI agent access (via MCP) to graph data.

## Testing & Development
- Install dev dependencies: `uv pip install -e ".[dev]"`
- Run all tests: `python -m pytest`
- Run unit tests only: `python -m pytest tests/unit/`
- Run e2e tests only: `python -m pytest tests/e2e/`
- Single test: `python -m pytest tests/unit/test_models.py::TestNodeModel::test_basic_node -v`
- Type checking: `mypy neoalchemy/`
- Linting: `ruff check neoalchemy/`
- Formatting: `ruff format neoalchemy/`
- Test coverage: `python -m pytest --cov=neoalchemy tests/`
- Use uv to run python commands

## Testing Strategy
The repository has dual-component testing requirements:

### **NeoAlchemy ORM Testing**
- **Unit tests**: Core expressions, cypher compilation, model logic (no database)
- **Integration tests**: Repository operations, transactions, constraints (with database)
- **E2E tests**: Complete ORM workflows and complex graph operations

### **MCP Server Testing**
- **Unit tests**: MCP tool logic, request handling (mocked NeoAlchemy)
- **Integration tests**: MCP server + Neo4j operations (real database)
- **E2E tests**: Full MCP workflows including AI agent interactions

### **Cross-Component Testing**
- Integration tests verifying MCP server correctly uses NeoAlchemy ORM
- E2E tests for complete workflows (AI agent → MCP → NeoAlchemy → Neo4j)

### **Database Environment**
Tests leverage the existing devcontainer setup:
- Neo4j 4.4 container with proper configuration
- Environment variables: `NEO4J_URI=bolt://neo4j:7687`
- Same database instance serves both components
- Test isolation through database cleanup between runs

## CLI Tools
- Show database info: `neoalchemy info [--uri URI --user USER]`
- Clear database: `neoalchemy clear [--uri URI --user USER]`
- Default connection: `bolt://localhost:7687` with user `neo4j`

## Test Environment
- E2E tests require running Neo4j database
- Configure via environment variables: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Unit tests run without database (fast, isolated component testing)
- E2E tests validate full integration with Neo4j

## Code Style
- **PEP 8** compliant with 100-character line length
- **Imports**: Group by standard library, third-party, internal; alphabetized within groups
- **Typing**: Full type annotations required for all functions and methods
- **Strings**: Double quotes preferred (`"text"` not `'text'`)
- **Docstrings**: Google style with Args, Returns, Raises sections
- **Naming**: 
  - Classes: `PascalCase`, Functions/variables: `snake_case`, Constants: `UPPER_SNAKE_CASE`
  - Private attributes: Leading underscore `_private`
  - Class variables: Double underscores for internal attributes `__registry__`

## Error Handling
- Catch specific exceptions (not broad `except:`)
- Include meaningful error messages
- Preserve original exceptions with `from` when re-raising

## Neo4j Integration
- Tests require a running Neo4j instance (default: bolt://localhost:7687)
- Always use transactions for database operations

## Architecture Overview
NeoAlchemy follows a layered architecture inspired by SQLAlchemy:

### Core Layer (`neoalchemy/core/`)
- **Expressions** (`expressions/`): Field expressions, operators, and logical operations for query building
- **Cypher** (`cypher/`): Modular Cypher query compiler with elements (patterns, clauses) and query assembly
- **Field Registration** (`field_registration.py`): Dynamic field expression registration system using venusian
- **State Management** (`state.py`): Query compilation state and parameter tracking

### ORM Layer (`neoalchemy/orm/`)
- **Models** (`models.py`): Base classes `Neo4jModel`, `Node`, `Relationship` with Pydantic integration
- **Repository** (`repository.py`): Transaction-based database interface `Neo4jRepository` and `Neo4jTransaction`
- **Query Builder** (`query.py`): High-level query building API `QueryBuilder` 
- **Fields** (`fields.py`): Custom field types `UniqueField`, `IndexedField`
- **Constraints** (`constraints.py`): Database constraint management

### Key Patterns
- **Transaction-first**: All operations require explicit transaction context
- **Expression system**: Python operators automatically compile to Cypher via registered field expressions
- **Type safety**: Comprehensive type annotations and Pydantic model validation
- **Modular compilation**: Cypher queries built from composable elements and clauses

## Initialization Requirements
- **Critical**: Always call `initialize()` from `neoalchemy` before using models to register field expressions
- This populates the dynamic expression system that enables `Model.field` syntax

## Component Architecture

### **NeoAlchemy ORM** (`neoalchemy/`)
Core Layer (`neoalchemy/core/`):
- **Expressions** (`expressions/`): Field expressions, operators, and logical operations for query building
- **Cypher** (`cypher/`): Modular Cypher query compiler with elements (patterns, clauses) and query assembly
- **Field Registration** (`field_registration.py`): Dynamic field expression registration system using venusian
- **State Management** (`state.py`): Query compilation state and parameter tracking

ORM Layer (`neoalchemy/orm/`):
- **Models** (`models.py`): Base classes `Neo4jModel`, `Node`, `Relationship` with Pydantic integration
- **Repository** (`repository.py`): Transaction-based database interface `Neo4jRepository` and `Neo4jTransaction`
- **Query Builder** (`query.py`): High-level query building API `QueryBuilder` 
- **Fields** (`fields.py`): Custom field types `UniqueField`, `IndexedField`
- **Constraints** (`constraints.py`): Database constraint management

### **MCP Server** (`graph-mcp/`)
- Model Context Protocol server implementation
- Provides granular, type-safe MCP tools for Neo4j operations
- Tools include entity management, source management, relationship management, and queries
- Uses FastMCP framework with proper type validation and error handling
- Built on top of NeoAlchemy ORM for all database operations

## Best Practices
- Follow existing patterns in the codebase
- Use f-strings for string formatting
- Avoid wildcard imports
- Use Python's latest language features wherever appropriate
- Use optional parameters with default values instead of multiple methods