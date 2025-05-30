"""
Unit tests for field-level constraints in NeoAlchemy models.

These tests verify that the constraint metadata is properly registered
and accessed in model classes without requiring a Neo4j database.
"""

from typing import Optional

from pydantic import Field

from neoalchemy import initialize
from neoalchemy.orm.fields import IndexedField, UniqueField
from neoalchemy.orm.models import Node, Relationship


class TestFieldConstraints:
    """Test field-level constraint functionality."""

    def test_model_unique_constraints(self):
        """Test unique constraint definition on model fields."""
        # Initialize for field expressions
        initialize()

        class Person(Node):
            """Person model with unique constraint on email."""

            name: "IndexedField[str]"  # type: ignore
            email: "UniqueField[str]"  # type: ignore
            ssn: "UniqueField[str]" = Field(default=None)  # type: ignore

        # Test constraints collection
        unique_fields = Person.get_constraints()
        indexed_fields = Person.get_indexes()

        assert "email" in unique_fields
        assert "ssn" in unique_fields
        assert "name" in indexed_fields
        assert "email" not in indexed_fields  # Should not be in both

    def test_custom_label_with_constraints(self):
        """Test that constraints work with custom labels."""
        # Initialize for field expressions
        initialize()

        class Customer(Node):
            """Customer model with custom label."""

            __label__ = "Client"

            account_id: "UniqueField[str]"  # type: ignore
            name: "IndexedField[str]"  # type: ignore

        # Test constraints collection
        unique_fields = Customer.get_constraints()
        assert "account_id" in unique_fields
        assert Customer.get_label() == "Client"

    def test_multiple_constraints(self):
        """Test multiple constraints on a model."""
        # Initialize for field expressions
        initialize()

        class Product(Node):
            """Product model with multiple constraints."""

            sku: "UniqueField[str]"  # type: ignore
            upc: "UniqueField[str]"  # type: ignore
            name: "IndexedField[str]"  # type: ignore
            price: "IndexedField[float]"  # type: ignore

        # Test constraints collection
        unique_fields = Product.get_constraints()
        indexed_fields = Product.get_indexes()

        assert "sku" in unique_fields
        assert "upc" in unique_fields
        assert "name" in indexed_fields
        assert "price" in indexed_fields

    def test_relationship_constraints(self):
        """Test constraints on relationship models."""
        # Initialize for field expressions
        initialize()

        class TRANSACTION(Relationship):
            """Transaction relationship with constraints."""

            transaction_id: "UniqueField[str]"  # type: ignore
            amount: "IndexedField[float]"  # type: ignore

        # Test constraints collection
        unique_fields = TRANSACTION.get_constraints()
        indexed_fields = TRANSACTION.get_indexes()

        assert "transaction_id" in unique_fields
        assert "amount" in indexed_fields
