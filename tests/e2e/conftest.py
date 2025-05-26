"""
Fixtures for end-to-end tests.

E2E tests use the full system stack with real database and
complete component integration.
"""

import pytest

# E2E tests will use the same database fixtures as integration tests
# but will focus on complete user workflows rather than component testing

# For now, we'll inherit from integration fixtures
pytest_plugins = ["tests.integration.conftest"]


@pytest.fixture
def full_system_setup(repo, clean_db, initialized_neoalchemy):
    """Set up complete system for E2E testing."""
    # This fixture can be expanded to set up:
    # - Complete schema/constraints
    # - Sample data for realistic scenarios
    # - Any additional system components
    
    from neoalchemy.orm.constraints import setup_constraints
    from tests.models import Person, Company
    
    # Set up constraints for all models
    setup_constraints(repo._driver)
    
    yield {
        "repo": repo,
        "models": {"Person": Person, "Company": Company}
    }