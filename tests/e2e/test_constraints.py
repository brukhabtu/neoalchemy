"""
End-to-end tests for Neo4j constraints created from model field definitions.

These tests verify that the constraints are properly created in the Neo4j database.
"""


import pytest
from pydantic import Field

from neoalchemy import initialize
from neoalchemy.constraints import setup_constraints
from neoalchemy.orm.fields import IndexedField, UniqueField
from neoalchemy.orm.models import Node


class ConstrainedPerson(Node):
    """Person model with constraints for testing."""

    name: str = Field(description="Person's name")
    email: UniqueField(str, description="Email address")
    department: IndexedField(str, default="")


class ConstrainedProduct(Node):
    """Product model with constraints for testing."""

    sku: UniqueField(str, description="Stock keeping unit")
    name: IndexedField(str, description="Product name")
    price: IndexedField(float, description="Product price")


@pytest.mark.e2e
def test_constraint_creation(driver, clean_db):
    """Test that constraints are created correctly in Neo4j."""
    # Initialize NeoAlchemy
    initialize()

    # Set up constraints
    setup_constraints(driver)

    # Verify constraints were created
    with driver.session() as session:
        # Check for constraints
        constraints_result = session.run("SHOW CONSTRAINTS")
        constraint_records = list(constraints_result)

        # Verify that the email constraint exists
        email_constraint_exists = False
        for record in constraint_records:
            record_data = record.data()
            # Format depends on Neo4j version - adapt as needed
            if "ConstrainedPerson" in str(record_data) and "email" in str(record_data):
                email_constraint_exists = True
                break

        assert email_constraint_exists, "Email uniqueness constraint not found"

        # Check for indexes
        indexes_result = session.run("SHOW INDEXES")
        index_records = list(indexes_result)

        # Verify the department index exists
        department_index_exists = False
        for record in index_records:
            record_data = record.data()
            if "ConstrainedPerson" in str(record_data) and "department" in str(record_data):
                department_index_exists = True
                break

        assert department_index_exists, "Department index not found"


@pytest.mark.e2e
def test_uniqueness_enforcement(repo, clean_db, driver):
    """Test that uniqueness constraints are enforced when creating entities."""
    # Initialize NeoAlchemy
    initialize()

    # Set up constraints
    setup_constraints(driver)

    # Create an entity with a unique field
    with repo.transaction() as tx:
        person = ConstrainedPerson(name="John Doe", email="john@example.com")
        created_person = tx.create(person)

        # Verify it was created
        assert created_person.email == "john@example.com"

    # Try to create another entity with the same unique field
    with pytest.raises(Exception) as exc_info:
        with repo.transaction() as tx:
            duplicate = ConstrainedPerson(
                name="John Smith",  # Different name
                email="john@example.com",  # Same email
            )
            tx.create(duplicate)

    # Verify the correct constraint error was raised
    error_text = str(exc_info.value)
    assert "already exists" in error_text.lower() or "constraint" in error_text.lower()


@pytest.mark.e2e
def test_merge_with_constraints(repo, clean_db, driver):
    """Test merging entities based on unique constraints."""
    # Initialize NeoAlchemy
    initialize()

    # Set up constraints
    setup_constraints(driver)

    # Create initial entity
    with repo.transaction() as tx:
        person = tx.merge(
            ConstrainedPerson, name="Test Person", email="test@example.com", department="IT"
        )
        assert person.name == "Test Person"
        assert person.email == "test@example.com"

    # Update with merge
    with repo.transaction() as tx:
        updated = tx.merge(
            ConstrainedPerson,
            name="Updated Name",
            email="test@example.com",  # Same email
            department="Engineering",
        )

        # Verify it's the same entity but updated
        assert updated.name == "Updated Name"
        assert updated.department == "Engineering"

        # Check that only one entity exists
        all_persons = tx.query(ConstrainedPerson).find()
        assert len(all_persons) == 1, "Should only have one person entity"
