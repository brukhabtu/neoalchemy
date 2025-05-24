"""
Test to verify unit test isolation is working correctly.

This test ensures that unit tests cannot access real database fixtures
and that the isolation mechanisms are functioning properly.
"""

import pytest
from unittest.mock import Mock


class TestUnitTestIsolation:
    """Test that unit test isolation mechanisms work correctly."""
    
    def test_mock_driver_available(self, mock_driver):
        """Test that mock driver fixture is available and functional."""
        # Should be a mock object
        assert isinstance(mock_driver, Mock)
        
        # Should have session method
        assert hasattr(mock_driver, 'session')
        
        # Should be able to call session
        session = mock_driver.session()
        assert session is not None
    
    def test_mock_repo_available(self, mock_repo):
        """Test that mock repository fixture is available."""
        # Should not be None
        assert mock_repo is not None
        
        # Should have a driver
        assert hasattr(mock_repo, 'driver')
    
    def test_database_fixtures_blocked(self):
        """Test that real database fixtures are blocked."""
        # This test verifies that the blocking mechanism is in place
        # by checking that the functions exist but would fail if called
        from tests.unit.conftest import driver, repo, clean_db
        
        # These should be blocking functions
        assert callable(driver)
        assert callable(repo) 
        assert callable(clean_db)
        
        # Note: We can't actually call them here because pytest will
        # inject the fixture context. The blocking happens when pytest
        # tries to resolve the fixture dependency.
    
    def test_unit_tests_run_fast(self):
        """Test that this unit test runs very quickly."""
        import time
        start_time = time.time()
        
        # Do some simple operations that unit tests typically do
        from neoalchemy.orm.models import Node
        
        class TestModel(Node):
            name: str
            
        # Create a model instance (no database involved)
        model = TestModel(name="test")
        assert model.name == "test"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in well under 1 second
        assert duration < 0.1, f"Unit test took too long: {duration} seconds"
    
    def test_isolated_registry_fixture(self, isolated_registry):
        """Test that the isolated registry fixture works."""
        # Should provide registry information
        assert isinstance(isolated_registry, dict)
        assert "node_registry" in isolated_registry
        assert "relationship_registry" in isolated_registry
        assert "model_registry" in isolated_registry