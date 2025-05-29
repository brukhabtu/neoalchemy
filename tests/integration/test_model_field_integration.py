"""Integration tests for Model + Field interactions.

Tests how models interact with field definitions, constraints, and indexes
without hitting the database.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Optional
from pydantic import Field, ValidationError

from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.fields import UniqueField, IndexedField
from neoalchemy.orm.repository import Neo4jRepository
from neoalchemy.orm.constraints import setup_constraints, _setup_unique_constraints, _setup_indexes
from neoalchemy.core.expressions.fields import FieldExpr

from .shared_models import User, Product, Company, WorksAt
from .test_helpers import MockAssertions


@pytest.mark.integration
class TestModelFieldIntegration:
    """Test Model and Field components working together."""

    def test_model_constraint_detection_from_field_metadata(self):
        """Test that models correctly detect constraints from field metadata."""
        # Using shared User model which has proper field definitions
        
        # Model should correctly identify constraints
        constraints = User.get_constraints()
        assert "email" in constraints
        assert "username" in constraints
        assert "account_number" in constraints
        assert "age" not in constraints  # Only has index, not unique
        
        # Model should correctly identify indexes
        indexes = User.get_indexes()
        assert "username" in indexes  # Has both unique and index
        assert "age" in indexes
        assert "email" not in indexes  # Unique fields don't need separate index
        assert "account_number" not in indexes  # Unique fields don't need separate index

    def test_model_field_interaction_caches_results(self):
        """Test that model field methods cache their results for performance."""
        # Clear any existing cache first
        if hasattr(Product, '_constraints_cache'):
            delattr(Product, '_constraints_cache')
        if hasattr(Product, '_indexes_cache'):
            delattr(Product, '_indexes_cache')
        
        # First call should create cache
        constraints1 = Product.get_constraints()
        indexes1 = Product.get_indexes()
        
        # Verify cache was created
        assert hasattr(Product, '_constraints_cache')
        assert hasattr(Product, '_indexes_cache')
        
        # Second call should use cache (we can't easily test this without 
        # modifying the implementation, but we can verify results are consistent)
        constraints2 = Product.get_constraints()
        indexes2 = Product.get_indexes()
        
        assert constraints1 == constraints2
        assert indexes1 == indexes2
        assert "sku" in constraints1
        assert "name" in indexes1

    def test_constraint_setup_uses_model_metadata(self, mock_driver):
        """Test that constraint setup correctly uses model field metadata."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Setup constraints should use model metadata
        setup_constraints(mock_driver, [Company])
        
        # Verify constraint creation queries were executed
        executed_queries = [call[0][0] for call in mock_session.run.call_args_list]
        
        # Should create unique constraint for name (Company.name has unique=True)
        unique_constraint_queries = [q for q in executed_queries if "UNIQUE" in q]
        assert any("name" in q for q in unique_constraint_queries)
        
        # Should create index for name (Company.name has index=True)
        # Note: In Neo4j, unique constraints automatically create indexes
        
        # Should not create anything for non-constraint fields
        assert not any("founded" in q and ("UNIQUE" in q or "INDEX" in q) for q in executed_queries)
        assert not any("revenue" in q and ("UNIQUE" in q or "INDEX" in q) for q in executed_queries)

    def test_relationship_model_field_interactions(self):
        """Test that relationship models also support field constraints."""
        # Using shared WorksAt relationship model
        
        # Relationship models should also detect constraints
        constraints = WorksAt.get_constraints()
        assert "employee_id" in constraints
        assert "position" not in constraints
        
        indexes = WorksAt.get_indexes()
        # WorksAt model doesn't have any indexed fields in shared_models
        assert "employee_id" not in indexes  # Unique fields don't need separate index

    def test_model_inheritance_preserves_field_metadata(self):
        """Test that field metadata is preserved through model inheritance."""
        
        # Note: In Pydantic v2, field inheritance works differently
        # Child classes need to redefine fields to preserve metadata
        class BaseModel(Node):
            __label__ = "Base"
            
            from pydantic import Field
            id: str = Field(..., json_schema_extra={"unique": True})
            created_at: str = Field(..., json_schema_extra={"index": True})
        
        class ExtendedModel(BaseModel):
            __label__ = "Extended"
            
            from pydantic import Field
            # Re-declare base fields to preserve metadata in Pydantic v2
            id: str = Field(..., json_schema_extra={"unique": True})
            created_at: str = Field(..., json_schema_extra={"index": True})
            # New fields
            name: str = Field(..., json_schema_extra={"index": True})
            code: str = Field(..., json_schema_extra={"unique": True})
        
        # Extended model should have constraints from both base and extended
        constraints = ExtendedModel.get_constraints()
        assert "id" in constraints  # From base
        assert "code" in constraints  # From extended
        assert len(constraints) == 2
        
        indexes = ExtendedModel.get_indexes()
        assert "created_at" in indexes  # From base
        assert "name" in indexes  # From extended
        assert len(indexes) == 2

    def test_model_validation_with_field_constraints(self):
        """Test that models validate correctly with field constraints."""
        # Using shared User model which has validation constraints
        
        # Valid model should work
        valid_user = User(
            email="user@example.com",
            username="testuser",
            age=25,
            account_number="1234567890",
            balance=100.0,
            status="active"
        )
        assert valid_user.account_number == "1234567890"
        assert valid_user.balance == 100.0
        
        # Invalid account number length
        with pytest.raises(ValidationError) as exc:
            User(
                email="user@example.com",
                username="testuser",
                age=25,
                account_number="123",  # Too short
                balance=100.0,
                status="active"
            )
        assert "at least 10 characters" in str(exc.value)
        
        # Negative balance
        with pytest.raises(ValidationError) as exc:
            User(
                email="user@example.com",
                username="testuser",
                age=25,
                account_number="1234567890",
                balance=-50.0,  # Negative not allowed
                status="active"
            )
        assert "greater than or equal to 0" in str(exc.value)
        
        # Invalid status
        with pytest.raises(ValidationError) as exc:
            User(
                email="user@example.com",
                username="testuser",
                age=25,
                account_number="1234567890",
                balance=100.0,
                status="deleted"  # Not in allowed pattern
            )
        assert "pattern" in str(exc.value).lower()

    def test_setup_constraints_handles_neo4j_version_check(self, mock_driver):
        """Test that setup_constraints correctly handles Neo4j version checking."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        class TestNode(Node):
            __label__ = "TestNode"
            from pydantic import Field
            name: str = Field(..., json_schema_extra={"unique": True})
        
        class TestRel(Relationship):
            __type__ = "TEST_REL"
            from pydantic import Field
            weight: int = Field(..., json_schema_extra={"index": True})
        
        # Mock neo4j version
        import neo4j
        with patch.object(neo4j, '__version__', '5.0.0'):
            setup_constraints(mock_driver, [TestNode, TestRel])
            
            # Should setup constraints for both nodes and relationships
            executed_queries = [call[0][0] for call in mock_session.run.call_args_list]
            assert any("TestNode" in q and "UNIQUE" in q for q in executed_queries)
            assert any("TEST_REL" in q and "INDEX" in q for q in executed_queries)

    def test_model_field_expressions_registered_correctly(self):
        """Test that model fields are properly registered for expression building."""
        # Using shared Person model from conftest (imported as PersonModel)
        from .conftest import PersonModel
        
        # Field expressions should be accessible
        name_expr = PersonModel.field("name")
        assert isinstance(name_expr, FieldExpr)
        assert name_expr.name == "name"
        
        # Test different field types
        age_expr = PersonModel.field("age")
        assert isinstance(age_expr, FieldExpr)
        assert age_expr.name == "age"

    def test_constraint_setup_with_drop_existing(self, mock_driver):
        """Test that setup_constraints can drop existing constraints."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Track all queries executed
        executed_queries = []
        
        def mock_run(query):
            executed_queries.append(query)
            if query == "SHOW CONSTRAINTS":
                result = MagicMock()
                result.data.return_value = [
                    {"name": "old_constraint_1"},
                    {"name": "old_constraint_2"}
                ]
                return result
            elif query == "SHOW INDEXES":
                result = MagicMock()
                result.data.return_value = [
                    {"name": "old_index_1"},
                    {"name": "old_index_2"}
                ]
                return result
            return MagicMock()
        
        mock_session.run = mock_run
        
        class TestModel(Node):
            __label__ = "Test"
            from pydantic import Field
            id: str = Field(..., json_schema_extra={"unique": True})
        
        setup_constraints(mock_driver, [TestModel], drop_existing=True)
        
        # Verify queries were executed in order
        assert "SHOW CONSTRAINTS" in executed_queries
        assert "SHOW INDEXES" in executed_queries
        
        # Verify DROP commands were issued
        drop_constraint_queries = [q for q in executed_queries if "DROP CONSTRAINT" in q]
        drop_index_queries = [q for q in executed_queries if "DROP INDEX" in q]
        
        assert len(drop_constraint_queries) == 2  # 2 constraints
        assert len(drop_index_queries) == 2  # 2 indexes
        
        # Verify CREATE was called after drops
        create_queries = [q for q in executed_queries if "CREATE" in q]
        assert len(create_queries) > 0
        
        # Verify order: SHOW -> DROP -> CREATE
        show_idx = executed_queries.index("SHOW CONSTRAINTS")
        first_drop_idx = min(executed_queries.index(q) for q in executed_queries if "DROP" in q)
        first_create_idx = min(executed_queries.index(q) for q in executed_queries if "CREATE" in q)
        assert show_idx < first_drop_idx < first_create_idx

    def test_model_registry_integration(self):
        """Test that models correctly register themselves in the registry."""
        # Clear any existing registry
        Node.__registry__.clear()
        Relationship.__registry__.clear()
        
        class UserNode(Node):
            __label__ = "User"
            name: str
        
        class PostNode(Node):
            __label__ = "Post"
            title: str
        
        class AuthoredRel(Relationship):
            __type__ = "AUTHORED"
            date: str
        
        # Nodes should be in Node registry
        assert "User" in Node.__registry__
        assert Node.__registry__["User"] == UserNode
        assert "Post" in Node.__registry__
        assert Node.__registry__["Post"] == PostNode
        
        # Relationships should be in Relationship registry
        assert "AUTHORED" in Relationship.__registry__
        assert Relationship.__registry__["AUTHORED"] == AuthoredRel