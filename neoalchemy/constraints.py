"""
Constraint management for NeoAlchemy models.

This module provides utilities for creating and managing
database constraints based on model field definitions.
"""

import logging
from typing import List, Optional, Type

from neo4j import Driver

from neoalchemy.orm.models import Node, Relationship

logger = logging.getLogger(__name__)


def setup_constraints(
    driver: Driver, model_classes: Optional[List[Type]] = None, drop_existing: bool = False
):
    """Set up constraints and indexes for Neo4j models.

    Args:
        driver: Neo4j driver instance
        model_classes: Optional list of model classes to set up constraints for.
                      If None, all registered models will be used.
        drop_existing: Whether to drop existing constraints first
                      (useful during development)
    """
    # Get all registered models if not specified
    if model_classes is None:
        model_classes = list(Node.__registry__.values())
        # Add relationships only if explicitly supported by your Neo4j version
        # Neo4j 4.4+ supports relationship property indexes and constraints
        import neo4j

        if hasattr(neo4j, "__version__") and tuple(map(int, neo4j.__version__.split("."))) >= (
            4,
            4,
        ):
            model_classes.extend(list(Relationship.__registry__.values()))

    with driver.session() as session:
        if drop_existing:
            _drop_existing_constraints(session)

        for model_class in model_classes:
            # Get label/type
            if hasattr(model_class, "get_label"):
                entity_type = model_class.get_label()
                is_node = True
            elif hasattr(model_class, "get_type"):
                entity_type = model_class.get_type()
                is_node = False
            else:
                logger.warning(f"Model {model_class.__name__} has no label/type method, skipping")
                continue

            # Set up unique constraints
            _setup_unique_constraints(session, model_class, entity_type, is_node)

            # Set up indexes (only for fields that don't have unique constraints)
            _setup_indexes(session, model_class, entity_type, is_node)


def _drop_existing_constraints(session):
    """Drop all existing constraints and indexes.

    This is useful during development to ensure clean state.

    Args:
        session: Neo4j session
    """
    try:
        # Drop constraints
        constraints = session.run("SHOW CONSTRAINTS").data()
        for constraint in constraints:
            name = constraint.get("name")
            if name:
                session.run(f"DROP CONSTRAINT {name} IF EXISTS")

        # Drop indexes
        indexes = session.run("SHOW INDEXES").data()
        for index in indexes:
            name = index.get("name")
            if name:
                session.run(f"DROP INDEX {name} IF EXISTS")

        logger.info(f"Dropped {len(constraints)} constraints and {len(indexes)} indexes")
    except Exception as e:
        logger.warning(f"Error dropping constraints: {e}")


def _setup_unique_constraints(session, model_class, entity_type, is_node):
    """Set up unique constraints for a model.

    Args:
        session: Neo4j session
        model_class: Model class
        entity_type: Neo4j label or relationship type
        is_node: Whether this is a node or relationship
    """
    constraints = model_class.get_constraints()

    for field in constraints:
        entity_var = "n" if is_node else "r"
        entity_type_clause = f":{entity_type}" if is_node else f"[{entity_var}:{entity_type}]"

        # Create constraint name for easier management
        constraint_name = f"{entity_type.lower()}_{field}_unique"

        query = (
            f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
            f"FOR ({entity_var}{entity_type_clause}) "
            f"REQUIRE {entity_var}.{field} IS UNIQUE"
        )

        try:
            session.run(query)
            logger.info(f"Created unique constraint on {entity_type}.{field}")
        except Exception as e:
            logger.error(f"Error creating constraint on {entity_type}.{field}: {e}")


def _setup_indexes(session, model_class, entity_type, is_node):
    """Set up indexes for a model (only for fields without unique constraints).

    Args:
        session: Neo4j session
        model_class: Model class
        entity_type: Neo4j label or relationship type
        is_node: Whether this is a node or relationship
    """
    # Get all indexes and constraints to avoid duplication
    unique_fields = set(model_class.get_constraints())
    index_fields = (
        set(model_class.get_indexes()) - unique_fields
    )  # Don't index fields that already have a unique constraint

    for field in index_fields:
        entity_var = "n" if is_node else "r"
        entity_type_clause = f":{entity_type}" if is_node else f"[{entity_var}:{entity_type}]"

        # Create index name for easier management
        index_name = f"{entity_type.lower()}_{field}_idx"

        query = (
            f"CREATE INDEX {index_name} IF NOT EXISTS "
            f"FOR ({entity_var}{entity_type_clause}) "
            f"ON ({entity_var}.{field})"
        )

        try:
            session.run(query)
            logger.info(f"Created index on {entity_type}.{field}")
        except Exception as e:
            logger.error(f"Error creating index on {entity_type}.{field}: {e}")
