# NeoAlchemy Testing Levels

## Overview
NeoAlchemy uses a 4-tier testing strategy to ensure code quality at different levels of abstraction. Each level serves a specific purpose and has distinct characteristics.

## Test Levels

### 1. Unit Tests (`@pytest.mark.unit`)
**Purpose**: Test individual functions/methods in complete isolation

**Characteristics**:
- All dependencies are mocked (including other NeoAlchemy components)
- No external services (database, filesystem, network)
- Test a single unit of code behavior
- Extremely fast execution (<100ms per test)
- Located in `tests/unit/`

**Example Scenarios**:
- Test that `FieldExpr.__eq__()` returns correct expression object
- Test that `Neo4jModel.get_constraints()` parses field metadata correctly
- Test that `CypherQuery.to_cypher()` generates correct string format

**Mocking Strategy**:
```python
# Mock everything except the unit under test
def test_field_expr_equality():
    field = FieldExpr("name")
    expr = field == "value"  # Only this operation is real
    assert isinstance(expr, EqualityExpr)
```

### 2. Integration Tests (`@pytest.mark.integration`)
**Purpose**: Test how NeoAlchemy components work together

**Characteristics**:
- Only external boundaries are mocked (Neo4j driver, filesystem)
- Real NeoAlchemy components interact with each other
- Test component contracts and interfaces
- Fast execution (<5 seconds total for all integration tests)
- Located in `tests/integration/`

**Example Scenarios**:
- Test that `QueryBuilder` correctly calls `Repository._process_nodes()`
- Test that `Repository` correctly uses `Model` validation before operations
- Test that `Transaction` properly coordinates with `Repository` for rollbacks

**Mocking Strategy**:
```python
# Only mock the Neo4j driver (external boundary)
def test_repository_querybuilder_integration(mock_driver):
    repo = Neo4jRepository(mock_driver)  # Real repository
    with repo.transaction() as tx:       # Real transaction
        query = tx.query(PersonModel)    # Real query builder
        query.find()                     # Real method calls between components
```

### 3. Functional Tests (`@pytest.mark.functional`)
**Purpose**: Test complete features/subsystems without external dependencies

**Characteristics**:
- No external services (all boundaries mocked)
- Test entire feature implementations
- Multiple components working together for a complete feature
- Fast execution (no external I/O)
- Located in `tests/functional/`

**Example Scenarios**:
- Test complete query building feature from API to Cypher generation
- Test entire model validation and serialization pipeline
- Test full constraint management workflow (parsing, collecting, generating DDL)

**Mocking Strategy**:
```python
# Mock only external boundaries, test complete features
def test_complete_query_feature(mock_driver):
    repo = Neo4jRepository(mock_driver)  # Mock driver only
    with repo.transaction() as tx:
        # Test complete feature: build query → compile → execute → process results
        results = (tx.query(Person)
                    .where(age__gte=18)
                    .order_by("name")
                    .limit(10)
                    .find())
        # Verify entire feature pipeline worked correctly
```

### 4. End-to-End Tests (`@pytest.mark.e2e`)
**Purpose**: Test complete user workflows with real external dependencies

**Characteristics**:
- Real Neo4j database connection required
- Test entire user scenarios with actual database
- Verify real-world behavior including database constraints
- Slower execution (real I/O operations)
- Located in `tests/e2e/`

**Example Scenarios**:
- Create models → apply constraints → insert data → query → update → verify (with real Neo4j)
- Test that unique constraints are actually enforced by Neo4j
- Test that transactions actually rollback in the database
- Complete MCP server workflow: AI request → MCP tool → NeoAlchemy → Neo4j → response

**Complete Workflow with Real Database**:
```python
def test_user_registration_workflow(neo4j_driver):
    # 1. Setup constraints in real Neo4j
    setup_constraints(neo4j_driver, [User, Profile])
    
    # 2. Create user with profile (real database writes)
    repo = Neo4jRepository(neo4j_driver)
    with repo.transaction() as tx:
        user = tx.create(User(email="user@example.com"))
        profile = tx.create(Profile(user_id=user.id))
        tx.create_relationship(user, "HAS_PROFILE", profile)
    
    # 3. Query and verify from real database
    with repo.transaction() as tx:
        result = tx.query(User).with_related("profile").find_one()
        assert result.profile is not None
```

## Key Differences

| Aspect | Unit | Integration | Functional | E2E |
|--------|------|-------------|------------|-----|
| **Scope** | Single method/function | Component interactions | Complete features | User workflows |
| **Dependencies** | All mocked | External mocked | External mocked | Nothing mocked |
| **Database** | No | No | No | Yes |
| **Speed** | <100ms | <500ms | <1s | <10s |
| **Purpose** | Correctness | Contracts | Features | Real-world behavior |

## When to Use Each Level

### Unit Tests
- Algorithm correctness
- Edge cases and error handling
- Data transformation logic
- Pure functions

### Integration Tests  
- Component API contracts
- Inter-component communication
- Dependency injection verification
- Interface compatibility

### Functional Tests
- Complete feature workflows work correctly
- Complex multi-component scenarios
- Feature-level API testing
- End-to-end feature validation (without external dependencies)

### E2E Tests
- Complete user stories work with real database
- Database constraints and features work correctly
- Real transaction behavior is verified
- System integrates properly with Neo4j

## Test Isolation

### Unit Test Isolation
```python
# Everything except the unit under test is mocked
@patch('neoalchemy.orm.repository.Neo4jRepository')
@patch('neoalchemy.orm.query.QueryBuilder')
def test_unit_isolation(mock_qb, mock_repo):
    # Test single unit behavior
```

### Integration Test Isolation
```python
# Only external boundaries mocked
def test_integration(mock_driver):
    # Real components interact
    repo = Neo4jRepository(mock_driver)  # Real repo
    # ... real component interactions
```

### Functional Test Isolation
```python
# Mock external boundaries - test complete features
def test_functional(mock_driver):
    # Test complete feature without external dependencies
    repo = Neo4jRepository(mock_driver)
    # ... test entire feature workflow
```

### E2E Test Isolation  
```python
# No mocks - real database cleaned between tests
def test_e2e(neo4j_driver, clean_database):
    # Test with real database
```