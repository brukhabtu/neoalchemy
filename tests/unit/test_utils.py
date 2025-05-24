"""
Test utilities for NeoAlchemy.

This module provides utility functions and classes for testing NeoAlchemy.
"""

from typing import Dict, Type, List, Set, Any
import pytest

from neoalchemy.orm.models import Node, Relationship
from neoalchemy.core.expressions import FieldExpr


class ModelTestHelper:
    """Helper class for testing model functionality."""

    @staticmethod
    def save_registries():
        """Save the current model registries.

        Returns:
            Tuple of (node_registry, relationship_registry)
        """
        return (Node.__registry__.copy(), Relationship.__registry__.copy())

    @staticmethod
    def restore_registries(node_registry, relationship_registry):
        """Restore model registries to a previous state.

        Args:
            node_registry: Node registry to restore
            relationship_registry: Relationship registry to restore
        """
        Node.__registry__ = node_registry
        Relationship.__registry__ = relationship_registry

    @staticmethod
    def register_field_expressions(model_class):
        """Manually register field expressions for a model class.

        This is useful for testing when the automatic registration might not be triggered.

        Args:
            model_class: The model class to register field expressions for
        """
        if hasattr(model_class, "__annotations__"):
            array_fields = []

            # Find array fields
            for field_name, field_type in model_class.__annotations__.items():
                # Check if it's a List type
                origin = getattr(field_type, "__origin__", None)
                if origin is list or origin is List:
                    array_fields.append(field_name)

            # Create field expressions
            for field_name in model_class.__annotations__:
                field_expr = FieldExpr(field_name, array_fields)
                setattr(model_class, field_name, field_expr)

    @staticmethod
    def get_test_array_fields() -> List[str]:
        """Get a list of common array field names for testing.

        Returns:
            List of common array field names
        """
        return ["tags", "participants", "items", "projects", "keywords"]


@pytest.fixture
def model_helper():
    """Fixture that provides a ModelTestHelper instance."""
    return ModelTestHelper


@pytest.fixture
def isolated_registry():
    """Fixture that provides an isolated model registry for tests.

    This ensures that model registry changes in one test don't affect others.
    """
    # Save original registries
    original_node_registry = Node.__registry__.copy()
    original_rel_registry = Relationship.__registry__.copy()

    # Clear registries
    Node.__registry__.clear()
    Relationship.__registry__.clear()

    try:
        # Run the test
        yield
    finally:
        # Restore original registries
        Node.__registry__ = original_node_registry
        Relationship.__registry__ = original_rel_registry
