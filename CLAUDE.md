# NeoAlchemy Development Guidelines

## Project Overview
NeoAlchemy is a SQLAlchemy-inspired ORM for Neo4j that provides a high-level API for working with Neo4j graph databases using Pydantic models with a transaction-based interface.

## Testing & Development
- Install dev dependencies: `pip install -e ".[dev]"`
- Run all tests: `python -m pytest tests/`
- Single test: `python -m pytest tests/test_e2e.py::test_crud_operations -v`
- Type checking: `mypy neoalchemy/`
- Linting: `ruff check neoalchemy/`
- Formatting: `ruff format neoalchemy/`
- Test coverage: `python -m pytest --cov=neoalchemy tests/`

## Code Style
- **PEP 8** compliant with 100-character line length (defined in pyproject.toml)
- **Imports**: Group by standard library, third-party, internal; alphabetized within groups
- **Typing**: Full type annotations for parameters and returns
- **Strings**: Double quotes preferred (`"text"` not `'text'`)
- **Docstrings**: Google style with sections for Args, Returns, Raises
- **Naming**: 
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private attributes: Leading underscore `_private`
  - Class variables: Double underscores for internal attributes `__registry__`

## Error Handling
- Catch specific exceptions (not broad `except:`)
- Include meaningful error messages
- Preserve original exceptions for debugging when appropriate

## Neo4j Integration
- Tests require a running Neo4j instance (default: bolt://localhost:7687)
- Update connection parameters in tests as needed
- Always use transactions for database operations

## Best Practices
- Follow existing patterns in the codebase
- Document public methods and classes
- Use f-strings for string formatting
- Avoid wildcard imports
- Use optional parameters with default values instead of multiple methods