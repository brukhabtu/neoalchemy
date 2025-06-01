"""Simple end-to-end test for basic NeoAlchemy functionality.

This is a minimal E2E test to verify the testing infrastructure works
before running the more complex workflow tests.
"""
import pytest
from .shared_models import Person


@pytest.mark.e2e
class TestSimpleE2E:
    """Simple E2E test to verify basic functionality."""

    def test_basic_create_and_read(self, repo):
        """Test basic create and read operations."""
        # Create a simple person
        with repo.transaction() as tx:
            person = tx.create(Person(
                email="test@example.com",
                name="Test User",
                age=30,
                active=True,
                tags=["test"],
                score=85.0
            ))
            
            # Verify the person was created with an ID
            assert person.email == "test@example.com"
            assert person.name == "Test User"
            assert person.age == 30
        
        # Read the person back
        with repo.transaction() as tx:
            found_person = tx.query(Person).where(
                Person.email == "test@example.com"
            ).find_one()
            
            assert found_person is not None
            assert found_person.name == "Test User"
            assert found_person.age == 30
            assert found_person.active is True
            assert "test" in found_person.tags
            assert found_person.score == 85.0
            
        print("✅ Simple E2E test passed!")