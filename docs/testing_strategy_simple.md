# NeoAlchemy Testing Strategy (Simplified)

## Three Test Types

### 1. Unit Tests
**What**: Test one thing in isolation  
**Mock**: Everything except what you're testing  
**Example**: Test that `field == "value"` creates the right expression object  
**Location**: `tests/unit/`

### 2. Integration Tests  
**What**: Test that our components work together  
**Mock**: Only the database driver  
**Example**: Test that QueryBuilder calls Repository methods correctly  
**Location**: `tests/integration/`

### 3. E2E Tests
**What**: Test real workflows with real database  
**Mock**: Nothing  
**Example**: Create a node, query it, update it, delete it  
**Location**: `tests/e2e/`

## That's It!

- **Unit** = Mock everything, test one thing
- **Integration** = Mock database, test our code working together  
- **E2E** = Real database, test it actually works

## Running Tests

```bash
# Fast tests (no database needed)
pytest tests/unit tests/integration -v

# All tests (requires Neo4j)
pytest -v
```