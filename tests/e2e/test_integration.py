"""
End-to-end integration tests for NeoAlchemy against a real Neo4j database.
These tests require a running Neo4j instance.
"""

from uuid import UUID

import pytest

# Import models from the models module
from tests.models import WORKS_FOR, Company, Person

# Import the ORM/Repository


@pytest.mark.e2e
def test_crud_operations(repo, clean_db):
    """Test basic CRUD operations with the repository."""
    # Create a new person
    with repo.transaction() as tx:
        person = Person(name="Alice", age=30, tags=["developer", "python"])
        created_person = tx.create(person)

        # Verify the person was created
        assert isinstance(created_person.id, UUID)
        assert created_person.name == "Alice"
        assert created_person.age == 30
        assert created_person.tags == ["developer", "python"]

        # Retrieve the person
        retrieved_person = tx.get(Person, str(created_person.id))
        assert retrieved_person.name == "Alice"

        # Update the person
        retrieved_person.age = 31
        updated_person = tx.update(retrieved_person)
        assert updated_person.age == 31

        # Delete the person
        result = tx.delete(updated_person)
        assert result is True

        # Verify the person was deleted
        assert tx.get(Person, str(updated_person.id)) is None


@pytest.mark.e2e
def test_relationships(repo, clean_db):
    """Test creating and querying relationships."""
    with repo.transaction() as tx:
        # Create a person and a company
        person = tx.create(Person(name="Bob", age=25))
        company = tx.create(Company(name="Acme Inc", founded=1990))

        # Create a relationship
        relationship = WORKS_FOR(role="Engineer")
        tx.relate(person, relationship, company)

        # Query the person and verify the relationship exists
        query = """
        MATCH (p:Person)-[r:WORKS_FOR]->(c:Company)
        WHERE p.id = $person_id AND c.id = $company_id
        RETURN r.role as role
        """

        result = tx._tx.run(query, {"person_id": str(person.id), "company_id": str(company.id)})

        record = result.single()
        assert record is not None
        assert record["role"] == "Engineer"


@pytest.mark.e2e
def test_basic_query_example(repo, clean_db):
    """Test a basic query for demonstration purposes."""
    with repo.transaction() as tx:
        # Create a simple company
        tx.create(Company(name="TechCorp", founded=2000, industry="Technology"))

        # Basic query
        companies = tx.query(Company).find()
        assert len(companies) == 1
        assert companies[0].name == "TechCorp"

        # Query with condition
        tech_companies = tx.query(Company).where(Company.industry == "Technology").find()
        assert len(tech_companies) == 1
        assert tech_companies[0].name == "TechCorp"
