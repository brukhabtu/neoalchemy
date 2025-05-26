"""
Integration tests for Neo4j repository operations.

These tests verify that the repository correctly performs CRUD operations
against a real Neo4j database.
"""

from uuid import UUID

import pytest

from tests.models import WORKS_FOR, Company, Person


@pytest.mark.integration
def test_create_and_retrieve(repo, clean_db):
    """Test creating and retrieving entities."""
    with repo.transaction() as tx:
        # Create a person
        person = Person(name="Alice", age=30, tags=["developer", "python"])
        created_person = tx.create(person)
        
        # Verify creation
        assert isinstance(created_person.id, UUID)
        assert created_person.name == "Alice"
        assert created_person.age == 30
        assert created_person.tags == ["developer", "python"]
        
        # Retrieve the person
        retrieved_person = tx.get(Person, str(created_person.id))
        assert retrieved_person is not None
        assert retrieved_person.name == "Alice"
        assert retrieved_person.age == 30


@pytest.mark.integration
def test_update_entity(repo, clean_db):
    """Test updating entities."""
    with repo.transaction() as tx:
        # Create and update
        person = tx.create(Person(name="Bob", age=25))
        person.age = 26
        updated_person = tx.update(person)
        
        assert updated_person.age == 26
        
        # Verify persistence
        retrieved = tx.get(Person, str(person.id))
        assert retrieved.age == 26


@pytest.mark.integration
def test_delete_entity(repo, clean_db):
    """Test deleting entities."""
    with repo.transaction() as tx:
        # Create and delete
        person = tx.create(Person(name="Charlie", age=35))
        person_id = str(person.id)
        
        result = tx.delete(person)
        assert result is True
        
        # Verify deletion
        assert tx.get(Person, person_id) is None


@pytest.mark.integration
def test_create_relationships(repo, clean_db):
    """Test creating relationships between entities."""
    with repo.transaction() as tx:
        # Create entities
        person = tx.create(Person(name="David", age=28))
        company = tx.create(Company(name="TechCorp", founded=2000))
        
        # Create relationship
        relationship = WORKS_FOR(role="Engineer")
        tx.relate(person, relationship, company)
        
        # Verify relationship exists via Cypher query
        query = """
        MATCH (p:Person)-[r:WORKS_FOR]->(c:Company)
        WHERE p.id = $person_id AND c.id = $company_id
        RETURN r.role as role
        """
        
        result = tx._tx.run(query, {
            "person_id": str(person.id), 
            "company_id": str(company.id)
        })
        
        record = result.single()
        assert record is not None
        assert record["role"] == "Engineer"


@pytest.mark.integration
def test_transaction_rollback(repo, clean_db):
    """Test that transaction rollback works correctly."""
    person_name = "RollbackTest"
    
    try:
        with repo.transaction() as tx:
            tx.create(Person(name=person_name, age=30))
            # Force an error to trigger rollback
            raise Exception("Intentional error for rollback test")
    except Exception:
        pass  # Expected
    
    # Verify the person was not created due to rollback
    with repo.transaction() as tx:
        query_result = tx._tx.run(
            "MATCH (p:Person {name: $name}) RETURN p", 
            {"name": person_name}
        )
        assert query_result.single() is None


@pytest.mark.integration
def test_query_basic_operations(repo, sample_data):
    """Test basic query operations."""
    # sample_data fixture creates Alice, Bob, and TechCorp with relationships
    
    with repo.transaction() as tx:
        # Find all persons
        all_persons = tx.query(Person).find()
        assert len(all_persons) == 2
        
        # Find specific person by name
        alice_results = tx.query(Person).where(Person.name == "Alice").find()
        assert len(alice_results) == 1
        assert alice_results[0].name == "Alice"
        
        # Find companies by industry
        tech_companies = tx.query(Company).where(Company.industry == "Technology").find()
        assert len(tech_companies) == 1
        assert tech_companies[0].name == "TechCorp"


@pytest.mark.integration 
def test_merge_operations(repo, clean_db):
    """Test merge operations for create-or-update behavior."""
    with repo.transaction() as tx:
        # First merge - should create
        person = tx.merge(Person, name="MergeTest", age=25)
        assert person.name == "MergeTest"
        assert person.age == 25
        person_id = person.id
        
        # Second merge with same name - should update
        updated = tx.merge(Person, name="MergeTest", age=26, tags=["updated"])
        assert updated.id == person_id  # Same entity
        assert updated.age == 26
        assert updated.tags == ["updated"]
        
        # Verify only one entity exists
        all_persons = tx.query(Person).find()
        assert len(all_persons) == 1