# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About NeoAlchemy

NeoAlchemy is a SQLAlchemy-inspired Python ORM for Neo4j graph databases. It provides a high-level, Pythonic API for working with Neo4j using Pydantic models, type-safe query building, and transaction-based database operations.

## Architecture Overview

**Layered Architecture (Bottom-up):**
- **Database Layer**: Neo4j Python driver
- **Core Layer**: Expression system, Cypher compiler, field registration (`neoalchemy/core/`)
- **ORM Layer**: Models, query building, repository pattern (`neoalchemy/orm/`)
- **MCP Layer**: FastMCP server for AI integration (`graph-mcp/`)

**Key Patterns:**
- **Expression System**: Uses operator overloading for Pythonic queries (`Person.age > 25`)
- **Metaclass Field Access**: `Person.name` returns `FieldExpr` for queries vs field values for instances
- **Transaction Repository**: All database operations happen within transaction contexts
- **Registry Pattern**: Automatic model registration for MCP tools via `Node.__registry__`

## Development Commands

### Package Management (UV)
```bash
# Add dependencies
uv add package-name
uv add --dev dev-package-name

# Sync and update
uv sync
```

### Testing (4-tier Strategy)
```bash
# Default: Unit + Integration tests (fast)
uv run pytest

# Individual test levels
uv run pytest tests/unit/          # Unit tests only (mocked dependencies)
uv run pytest tests/integration/   # Integration tests (real components, mocked DB)
uv run pytest tests/e2e/          # E2E tests (requires running Neo4j)

# Using markers
uv run pytest -m "not e2e"        # Exclude E2E tests (default)
uv run pytest -m e2e             # E2E tests only

# Single test
uv run pytest tests/unit/core/test_state.py::TestState::test_method
```

### Code Quality
```bash
# Linting and formatting
uv run ruff check .               # Check linting
uv run ruff format .              # Format code
uv run ruff check . --fix         # Auto-fix issues

# Type checking
uv run mypy .                     # Type check entire codebase
```

### MCP Server
```bash
# Start MCP server for AI integration
cd graph-mcp && uv run python mcp_server.py
```

## Core Components

### Expression System (`neoalchemy/core/expressions/`)
- **Base expressions** (`base.py`): Foundation for all query expressions
- **Field expressions** (`fields.py`): Property access and operations
- **Operators** (`operators.py`): Comparison and arithmetic operations  
- **Logical operations** (`logical.py`): AND, OR, NOT logic
- **Functions** (`functions.py`): Neo4j function calls
- **Adapter** (`adapter.py`): Central configuration for expression compilation

### Cypher Compiler (`neoalchemy/core/cypher/`)
- **Elements** (`elements/`): Modular query components (patterns, clauses)
- **Keywords** (`core/keywords.py`): Cypher keyword constants
- **Query** (`query.py`): Top-level query compilation

### ORM Layer (`neoalchemy/orm/`)
- **Models** (`models.py`): Base `Node` and `Relationship` classes with Pydantic
- **Fields** (`fields.py`): `PrimaryField`, `UniqueField`, `IndexedField` types
- **Query building** (`query.py`): High-level query API with Python syntax
- **Repository** (`repository.py`): Transaction-based database interface
- **Source tracking** (`tracking/`): Data lineage and MCP integration

## Testing Conventions

### Test Structure
- **Unit tests**: Mock all external dependencies, focus on business logic
- **Integration tests**: Test component boundaries with real NeoAlchemy objects
- **E2E tests**: Full workflows against real Neo4j database

### Key Test Patterns
- Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e` markers
- E2E tests excluded by default (require `-m e2e` or explicit inclusion)
- Shared models in `tests/e2e/shared_models.py` and `tests/integration/shared_models.py`
- Database setup via `conftest.py` fixtures at each level

## Development Workflow

### Field Expression Registration
Fields automatically register with the expression system via `neoalchemy/core/field_registration.py`. New field types should follow this pattern.

### Query Building Pattern
```python
# Repository transaction pattern
with repo.transaction() as tx:
    query = tx.query(Model).where(condition)
    results = query.all()
    # Auto-commit on context exit
```

### Operator Overloading for Queries
- Comparison: `>`, `>=`, `<`, `<=`, `==`, `!=`
- Logical: `&` (AND), `|` (OR), `~` (NOT)
- Container: `in_()` method for membership
- String: `.startswith()`, `.endswith()`, `.contains()`

### MCP Integration
The `graph-mcp/` module provides 11 MCP tools for AI-driven database operations:
- Entity CRUD: `create_entity`, `update_entity`, `get_entity`, `delete_entity`
- Relationships: `create_relationship`
- Querying: `query_entities`
- Schema: `get_available_types`, `get_entity_schema`
- Source Context: `set_data_source_context`, `set_reasoning_context`, `start_analysis_session`, `get_session_info`

**Automatic Source Tracking:**
- LLMs can specify `source_id` (e.g., "PROJ-123", "confluence-page-456") for automatic source type inference
- Zero cognitive overhead - source tracking happens automatically behind the scenes
- Full audit trail maintained with native system IDs

**MCP Best Practices Reference:**
- [FastMCP Documentation](https://gofastmcp.com/llms-full.txt) - Comprehensive guide for MCP tool design patterns, naming conventions, and implementation best practices

## Configuration

### Ruff (pyproject.toml)
- Line length: 100 characters
- Target: Python 3.10+
- Linting: pycodestyle (E), pyflakes (F), isort (I)

### MyPy
- Strict configuration with special handling for expression operator overloading
- Custom type checking for the metaclass-based field access system

## Important Notes

- **No automatic initialization**: Users must call `initialize()` explicitly
- **Expression compilation**: Centralized via adapter pattern in `expressions/adapter.py`
- **Pydantic v2**: Modern validation with JSON schema support
- **Neo4j native types**: Built-in support for temporal and spatial data types
- **Venusian integration**: Used for advanced registration patterns