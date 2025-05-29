# Integration Tests

## What Are Integration Tests?
Test that NeoAlchemy components work together correctly. Mock only the database.

## Examples
```python
def test_query_builder_uses_repository(mock_driver):
    """QueryBuilder should call Repository methods correctly"""
    repo = Neo4jRepository(mock_driver)  # Real repository
    with repo.transaction() as tx:        # Real transaction
        query = tx.query(PersonModel)     # Real query builder
        query.find()                      # Should call repo._process_nodes()
```

## What's Done ✅
- Repository + QueryBuilder work together
- Model validation prevents bad data
- Transactions coordinate operations

## What's TODO 🚧  
- Model field constraints and indexes
- Transaction rollback coordination
- Complex query building

## Run Tests
```bash
pytest tests/integration/ -v
```