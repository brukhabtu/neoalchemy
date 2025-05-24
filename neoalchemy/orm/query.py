"""
Query builder implementation using the Cypher element architecture.

This module provides a new implementation of the query builder that uses
the Cypher element architecture to generate Cypher queries. It maintains
the same fluent interface but uses a more modular and composable approach
to query generation.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from neoalchemy.core.cypher import (
    CypherQuery,
    LimitClause,
    MatchClause,
    NodePattern,
    OrderByClause,
    ReturnClause,
    WhereClause,
)
from neoalchemy.core.expressions import Expr, ExpressionAdapter, FieldExpr, OperatorExpr

# Generic type variables for models
M = TypeVar("M")
T = TypeVar("T")


class QueryBuilder(Generic[M]):
    """A fluent interface for building Neo4j queries using the CypherCompiler."""

    def __init__(self, repo: Any, model_class: Type[M], entity_var: str = "e"):
        """Initialize a query builder.

        Args:
            repo: The repository to execute queries against
            model_class: The model class to query
            entity_var: The variable name to use for entities in Cypher
        """
        self.repo = repo
        self.model_class = model_class
        self.node_label = getattr(model_class, "__label__", model_class.__name__)
        self.conditions: List[Expr] = []
        self.order_by_field: Optional[str] = None
        self.order_direction = "ASC"
        self.limit_value: Optional[int] = None
        self.entity_var = entity_var

        # Configure the expression adapter to use our entity variable
        Expr.set_adapter(ExpressionAdapter(entity_var=self.entity_var))

    def where(self, *conditions, **kwargs) -> "QueryBuilder[M]":
        """Add where conditions to the query.

        This method handles various types of conditions including special Pythonic
        expressions captured by the expression state system.

        Args:
            *conditions: Various types of conditions:
                - Expression objects (e.g., Person.age > 30)
                - Boolean values from "in" operator evaluations
            **kwargs: Field and value pairs to filter on

        Returns:
            Self for method chaining
        """
        from neoalchemy.core.state import expression_state

        # Special case for in-operator expressions (True with a captured expression)
        if len(conditions) == 1 and conditions[0] is True:
            # We need to check if there's a captured expression from an in-operator
            if expression_state.last_expr is not None:
                # Use the stored expression and clear it
                expr = expression_state.last_expr
                self.conditions.append(expr)
                expression_state.last_expr = None
                return self
            # If we get True but there's no stored expression, treat it as a condition
            self.conditions.append(OperatorExpr("active", "=", True))
            return self

        # Handle regular expressions
        for condition in conditions:
            if isinstance(condition, Expr):
                # Expression object
                self.conditions.append(condition)
            elif isinstance(condition, tuple) and len(condition) == 3:
                # Legacy tuple support (field, operator, value)
                field, operator, value = condition
                self.conditions.append(OperatorExpr(field, operator, value))
            else:
                raise ValueError(f"Invalid condition: {condition}")

        # Handle keyword arguments for backward compatibility
        for field, value in kwargs.items():
            self.conditions.append(OperatorExpr(field, "=", value))

        return self

    def where_contains(self, field_or_expr, value: Optional[str] = None) -> "QueryBuilder[M]":
        """Add a contains condition to the query.

        For string fields, checks if the field contains the value as a substring.
        For array fields, checks if the array contains the value as an element.

        Args:
            field_or_expr: Field name, field expression, or FieldExpr object
            value: Value to search for (not needed if field_or_expr is an expression)

        Returns:
            Self for method chaining
        """
        # Handle FieldExpr object
        if isinstance(field_or_expr, FieldExpr):
            if value is not None:
                # For FieldExpr objects, we can use the is_array_field method
                if field_or_expr.is_array_field():
                    # For arrays, use ANY IN for Neo4j
                    self.conditions.append(OperatorExpr(field_or_expr.name, "ANY IN", value))
                else:
                    # For strings, use CONTAINS
                    self.conditions.append(OperatorExpr(field_or_expr.name, "CONTAINS", value))
            else:
                raise ValueError("Value must be provided when using FieldExpr")

        # Handle old-style tuple expression
        elif isinstance(field_or_expr, tuple) and len(field_or_expr) == 3:
            field, _, search_value = field_or_expr
            # Create a temporary FieldExpr to use is_array_field
            field_expr = FieldExpr(field)
            if field_expr.is_array_field():
                self.conditions.append(OperatorExpr(field, "ANY IN", search_value))
            else:
                self.conditions.append(OperatorExpr(field, "CONTAINS", search_value))

        # Handle string field name
        elif isinstance(field_or_expr, str):
            if value is not None:
                # Create a temporary FieldExpr to use is_array_field
                field_expr = FieldExpr(field_or_expr)
                if field_expr.is_array_field():
                    self.conditions.append(OperatorExpr(field_or_expr, "ANY IN", value))
                else:
                    self.conditions.append(OperatorExpr(field_or_expr, "CONTAINS", value))
            else:
                raise ValueError("Value must be provided when using field name string")
        else:
            raise ValueError(f"Invalid field expression: {field_or_expr}")

        return self

    def limit(self, count: int) -> "QueryBuilder[M]":
        """Limit the number of results.

        Args:
            count: Maximum number of results to return

        Returns:
            Self for method chaining
        """
        self.limit_value = count
        return self

    def order_by(self, field_or_expr, descending: bool = False) -> "QueryBuilder[M]":
        """Order results by a field.

        Args:
            field_or_expr: Field name or field expression
            descending: Whether to order in descending order

        Returns:
            Self for method chaining
        """
        # Handle field expressions
        if isinstance(field_or_expr, FieldExpr):
            self.order_by_field = field_or_expr.name
        # Handle string field names
        else:
            self.order_by_field = field_or_expr

        self.order_direction = "DESC" if descending else "ASC"
        return self

    def _build_query(self) -> CypherQuery:
        """Build a CypherQuery object from the builder state.

        Returns:
            CypherQuery object ready for compilation
        """
        # Reset any lingering expression state
        from neoalchemy.core.state import reset_expression_state

        reset_expression_state()

        # Create the basic node pattern
        node_pattern = NodePattern(self.entity_var, [self.node_label])

        # Create the MATCH clause
        match_clause = MatchClause(node_pattern)

        # Create the WHERE clause if we have conditions
        # Pass Expr objects directly - WhereClause will handle the conversion
        where_clause = WhereClause(self.conditions) if self.conditions else None

        # Create the RETURN clause
        return_clause = ReturnClause([self.entity_var])

        # Create the ORDER BY clause if specified
        order_by = None
        if self.order_by_field:
            # Create a property reference using the adapter pattern for consistency
            from neoalchemy.core.expressions import FieldExpr

            field_expr = FieldExpr(self.order_by_field)
            property_ref = field_expr.to_cypher_element()

            order_by = OrderByClause([(property_ref, self.order_direction == "DESC")])

        # Create the LIMIT clause if specified
        limit = LimitClause(self.limit_value) if self.limit_value is not None else None

        # Create the complete query
        query = CypherQuery(
            match=match_clause,
            where=where_clause,
            return_clause=return_clause,
            order_by=order_by,
            limit=limit,
        )

        return query

    def find(self) -> List[M]:
        """Execute the query and return results.

        This method must be called within a transaction context.

        Returns:
            List of model instances matching the query
        """
        # Build the query
        query = self._build_query()
        parameters: Dict[str, Any] = {}
        cypher_query, _ = query.to_cypher(parameters)

        # Get the current transaction
        tx = getattr(self.repo, "_current_tx", None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")

        # Execute the query
        result = tx._tx.run(cypher_query, parameters)
        data_list = self.repo._process_multiple_nodes(result)

        # Convert results to model instances
        return [self.model_class(**data) for data in data_list]

    def find_one(self) -> Optional[M]:
        """Execute the query and return a single result.

        This method must be called within a transaction context.

        Returns:
            Model instance if found, None otherwise
        """
        # Limit to one result
        self.limit(1)

        # Build and execute the query
        query = self._build_query()
        parameters: Dict[str, Any] = {}
        cypher_query, _ = query.to_cypher(parameters)

        # Get the current transaction
        tx = getattr(self.repo, "_current_tx", None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")

        # Execute the query
        result = tx._tx.run(cypher_query, parameters)
        data = self.repo._process_single_node(result)

        # Convert result to model instance
        if data is None:
            return None
        return self.model_class(**data)

    def count(self) -> int:
        """Count the number of matching records without fetching full objects.

        This method must be called within a transaction context.

        Returns:
            Number of matching records
        """
        # Create a new query for counting
        node_pattern = NodePattern(self.entity_var, [self.node_label])
        match_clause = MatchClause(node_pattern)

        # Pass Expr objects directly - WhereClause will handle the conversion
        where_clause = WhereClause(self.conditions) if self.conditions else None

        # Use a COUNT function in the return clause
        return_clause = ReturnClause([(f"count({self.entity_var})", "count")])

        count_query = CypherQuery(
            match=match_clause, where=where_clause, return_clause=return_clause
        )

        # Convert the query to Cypher using to_cypher
        parameters: Dict[str, Any] = {}
        cypher_query, _ = count_query.to_cypher(parameters)

        # Get the current transaction
        tx = getattr(self.repo, "_current_tx", None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")

        # Execute the query
        result = tx._tx.run(cypher_query, parameters)
        record = result.single()

        # Return the count
        if record:
            return record["count"]
        return 0
