"""
Integration tests for Neo4j constraints and indexes.

These tests verify that database constraints and indexes are properly
created and enforced by the Neo4j database.
"""

import pytest
from pydantic import Field

from neoalchemy import initialize
from neoalchemy.orm.constraints import setup_constraints
from neoalchemy.orm.models import Node


class ConstrainedPerson(Node):
    """Test model with constraints."""
    __label__ = "ConstrainedPerson"
    
    name: str = Field(description="Person's name")
    email: str = Field(unique=True, description="Email address")
    department: str = Field(default="", index=True, description="Department")


class ConstrainedProduct(Node):
    """Test model with multiple constraints."""
    __label__ = "ConstrainedProduct"
    
    sku: str = Field(unique=True, description="Stock keeping unit")
    name: str = Field(index=True, description="Product name")
    price: float = Field(index=True, description="Product price")


@pytest.mark.integration
def test_constraint_creation(driver, clean_db, initialized_neoalchemy):
    """Test that constraints are properly created in Neo4j."""
    # Set up constraints for our test models
    setup_constraints(driver, model_classes=[ConstrainedPerson, ConstrainedProduct])
    
    with driver.session() as session:
        # Check that constraints were created
        constraints_result = session.run("SHOW CONSTRAINTS")
        constraint_records = list(constraints_result)
        
        # Verify email uniqueness constraint exists
        email_constraint_found = False
        for record in constraint_records:
            record_data = record.data()
            constraint_str = str(record_data)
            if "ConstrainedPerson" in constraint_str and "email" in constraint_str:
                email_constraint_found = True
                break
        
        assert email_constraint_found, f"Email constraint not found. Constraints: {constraint_records}"


@pytest.mark.integration
def test_index_creation(driver, clean_db, initialized_neoalchemy):
    """Test that indexes are properly created in Neo4j."""
    # Set up constraints and indexes
    setup_constraints(driver, model_classes=[ConstrainedPerson, ConstrainedProduct])
    
    with driver.session() as session:
        # Check that indexes were created
        indexes_result = session.run("SHOW INDEXES")
        index_records = list(indexes_result)
        
        # Verify department index exists
        department_index_found = False
        for record in index_records:
            record_data = record.data()
            index_str = str(record_data)
            if "ConstrainedPerson" in index_str and "department" in index_str:
                department_index_found = True
                break
        
        assert department_index_found, f"Department index not found. Indexes: {index_records}"


@pytest.mark.integration
def test_uniqueness_enforcement(repo, clean_db, driver, initialized_neoalchemy):
    """Test that uniqueness constraints are enforced."""
    # Set up constraints
    setup_constraints(driver, model_classes=[ConstrainedPerson])
    
    with repo.transaction() as tx:
        # Create first person with unique email
        person1 = ConstrainedPerson(name="John Doe", email="john@example.com")
        created = tx.create(person1)
        assert created.email == "john@example.com"
    
    # Try to create another person with same email - should fail
    with pytest.raises(Exception) as exc_info:
        with repo.transaction() as tx:
            person2 = ConstrainedPerson(name="Jane Doe", email="john@example.com")
            tx.create(person2)
    
    # Verify it's a constraint-related error
    error_message = str(exc_info.value).lower()
    assert any(word in error_message for word in ["constraint", "unique", "already exists", "duplicate"])


@pytest.mark.integration
def test_merge_with_unique_constraint(repo, clean_db, driver, initialized_neoalchemy):
    """Test merge operations work correctly with unique constraints."""
    # Set up constraints
    setup_constraints(driver, model_classes=[ConstrainedPerson])
    
    with repo.transaction() as tx:
        # First merge - creates new entity
        person = tx.merge(
            ConstrainedPerson,
            name="Test User",
            email="test@example.com",
            department="IT"
        )
        original_id = person.id
        assert person.name == "Test User"
        assert person.department == "IT"
        
        # Second merge with same email - should update existing
        updated = tx.merge(
            ConstrainedPerson,
            name="Updated User",
            email="test@example.com",  # Same email
            department="Engineering"
        )
        
        # Should be the same entity, just updated
        assert updated.id == original_id
        assert updated.name == "Updated User"
        assert updated.department == "Engineering"
        
        # Verify only one person exists
        all_persons = tx.query(ConstrainedPerson).find()
        assert len(all_persons) == 1


@pytest.mark.integration
def test_constraint_drop_and_recreate(driver, clean_db, initialized_neoalchemy):
    """Test dropping and recreating constraints."""
    # Create constraints
    setup_constraints(driver, model_classes=[ConstrainedPerson])
    
    # Drop and recreate
    setup_constraints(driver, model_classes=[ConstrainedPerson], drop_existing=True)
    
    # Verify constraints still exist after recreation
    with driver.session() as session:
        constraints_result = session.run("SHOW CONSTRAINTS")
        constraint_records = list(constraints_result)
        
        # Should still have email constraint
        email_constraint_found = False
        for record in constraint_records:
            record_data = record.data()
            if "ConstrainedPerson" in str(record_data) and "email" in str(record_data):
                email_constraint_found = True
                break
        
        assert email_constraint_found