"""
Query builder implementation for Neo4j queries.

This module provides a fluent interface for building and executing
Neo4j Cypher queries. The query builder handles expression translation,
parameter management, and result conversion.

The query builder works with the expression system to support:
- Standard comparison operators
- Chained comparisons (e.g., 25 <= Person.age <= 35)
- Logical operators (and, or, not)
- Containment checks using 'in' operator
- String operations
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

# Import expression definitions from expressions module
from neoalchemy.expressions import (
    Expr, FieldExpr, OperatorExpr
)
from neoalchemy.state import expression_state

# Generic type variables for models
M = TypeVar("M")
T = TypeVar("T")


class QueryBuilder(Generic[M]):
    """A fluent interface for building Neo4j queries."""

    def __init__(self, repo: Any, model_class: Type[M]):
        """Initialize a query builder.

        Args:
            repo: The repository to execute queries against
            model_class: The model class to query
        """
        self.repo = repo
        self.model_class = model_class
        self.node_label = getattr(model_class, "__label__", model_class.__name__)
        self.conditions: List[Expr] = []  # Now stores Expr objects
        self.parameters: Dict[str, Any] = {}
        self.param_index = 0
        self.limit_value: Optional[int] = None
        self.order_by_field: Optional[str] = None
        self.order_direction = "ASC"

    def where(self, *conditions, **kwargs) -> "QueryBuilder[M]":
        """Add where conditions to the query.

        This method is a key part of the expression system, handling various types
        of conditions including special Pythonic expressions captured by the
        expression state system.
        
        ## Expression State Interaction
        
        This method interacts with the expression state system in several ways:
        
        1. **Clearing chain_expr state**: Before processing conditions, it clears any
           lingering chain_expr state to prevent unintended chaining between separate
           where() calls.
           
        2. **Retrieving 'in' operator expressions**: When it receives a True boolean
           (from an 'in' operator), it checks if there's a captured expression in
           expression_state.last_expr and adds it to the conditions.
           
        3. **Resetting state**: After retrieving a captured expression, it sets
           expression_state.last_expr to None to prevent accidental reuse.
        
        ## Supported Condition Types
        
        The method supports these types of conditions:
        
        - **Expression objects** created by operators: `Person.age > 30`
        - **'in' operator expressions**: `"Smith" in Person.last_name`
        - **Chained comparisons**: `25 <= Person.age <= 35`
        - **Tuples**: `("name", "=", "Alice")` (legacy format)
        - **Keyword arguments**: `name="Alice"` (convenience format)
        
        Args:
            *conditions: Various types of conditions:
                - Expression objects (e.g., Person.age > 30)
                - Tuples of (field, operator, value)
                - Boolean values from "in" operator evaluations
            **kwargs: Field and value pairs to filter on

        Returns:
            Self for method chaining
            
        Examples:
            # Using within a transaction (preferred approach)
            with repo.transaction() as tx:
                # In operator for string/array containment
                results = tx.query(Person).where("Smith" in Person.last_name).find()
                
                # Standard comparison
                adults = tx.query(Person).where(Person.age > 18).find()
                
                # Chained comparison
                middle_aged = tx.query(Person).where(25 <= Person.age <= 35).find()
                
                # Multiple conditions in one query
                query = tx.query(Person).where(
                    Person.age > 25,
                    "Smith" in Person.last_name
                )
                
            # Using field expressions
            query.where(Person.age > 30)
            
            # Using keyword arguments
            query.where(name="Alice")
        """
        # Ensure chain_expr state is reset before we add a new condition
        if expression_state.chain_expr is not None:
            expression_state.chain_expr = None
            
        # If we have a single True boolean, check if it's from an 'in' operation
        if (len(conditions) == 1 and conditions[0] is True and expression_state.last_expr is not None):
            # Use the stored expression from the transaction context
            expr = expression_state.last_expr
            self.conditions.append(expr)
            expression_state.last_expr = None  # Clear for next use
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
            # Check if this is a boolean True from 'in' operator
            elif condition is True and expression_state.last_expr is not None:
                # Use the stored expression from the transaction context
                expr = expression_state.last_expr
                self.conditions.append(expr)
                expression_state.last_expr = None  # Clear for next use
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

    def _build_query(self) -> str:
        """Build the Cypher query from the builder state.
        
        This method translates the query builder's state into a Cypher query string.
        It handles several important tasks:
        
        1. **State Cleanup**: Clears any lingering chain_expr state to prevent
           unexpected chained comparisons between separate queries.
        
        2. **Parameter Reset**: Resets the parameters dictionary for each new query
           to ensure clean parameter generation.
        
        3. **Query Generation**: Builds a Cypher query string from the conditions,
           ordering, and limit values stored in the builder.
        
        ## Expression State Interaction
        
        This method interacts with the expression state system by ensuring any
        remaining chain_expr state is cleared. This is important because:
        
        - Chained comparisons might not complete if an error occurs
        - A previous query might have left state that could affect the next query
        - Query builders might be reused for multiple queries
        
        By clearing the chain_expr state here, we prevent unintended side effects
        between separate query executions.

        Returns:
            Cypher query string
        """
        # Ensure any lingering chain_expr state is cleared to prevent
        # unexpected chaining between separate queries
        if expression_state.chain_expr is not None:
            expression_state.chain_expr = None
            
        query = f"MATCH (e:{self.node_label})"

        # Reset parameters for new query
        self.parameters = {}
        self.param_index = 0
        
        # Build WHERE clause from expressions
        if self.conditions:
            where_clauses = []
            for condition in self.conditions:
                expr_str, self.param_index = condition.to_cypher(self.parameters, self.param_index)
                where_clauses.append(expr_str)
                
            query += f" WHERE {' AND '.join(where_clauses)}"

        query += " RETURN e"

        if self.order_by_field:
            query += f" ORDER BY e.{self.order_by_field} {self.order_direction}"

        if self.limit_value is not None:
            query += f" LIMIT {self.limit_value}"

        return query

    def find(self) -> List[M]:
        """Execute the query and return results.
        
        This method must be called within a transaction context.
        
        Returns:
            List of model instances matching the query
        """
        # Build the query
        query = self._build_query()
        
        # Get the current transaction
        tx = getattr(self.repo, '_current_tx', None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")
        
        # For debugging, you can uncomment these lines:
        # import logging
        # logging.debug(f"QUERY: {query}")
        # logging.debug(f"PARAMS: {self.parameters}")
            
        # Execute the query
        result = tx._tx.run(query, self.parameters)
        data_list = self.repo._process_multiple_nodes(result)
        
        # Convert results to model instances
        return [self.model_class.model_validate(data) for data in data_list]

    def find_one(self) -> Optional[M]:
        """Execute the query and return a single result.
        
        This method must be called within a transaction context.

        Returns:
            Model instance if found, None otherwise
        """
        # Limit to one result
        self.limit(1)
        
        # Build the query
        query = self._build_query()
        
        # Get the current transaction
        tx = getattr(self.repo, '_current_tx', None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")
            
        # Execute the query
        result = tx._tx.run(query, self.parameters)
        data = self.repo._process_single_node(result)
        
        # Convert result to model instance
        if data is None:
            return None
        return self.model_class.model_validate(data)
    
    def count(self) -> int:
        """Count the number of matching records without fetching full objects.
        
        This method must be called within a transaction context.
        
        Returns:
            Number of matching records
        """
        # Start with the basic match clause
        query = f"MATCH (e:{self.node_label})"
        
        # Reset parameters for new query
        self.parameters = {}
        self.param_index = 0
        
        # Build WHERE clause from expressions
        if self.conditions:
            where_clauses = []
            for condition in self.conditions:
                expr_str, self.param_index = condition.to_cypher(self.parameters, self.param_index)
                where_clauses.append(expr_str)
                
            query += f" WHERE {' AND '.join(where_clauses)}"

        # Return count instead of entities
        query += " RETURN count(e) AS count"
        
        # Get the current transaction
        tx = getattr(self.repo, '_current_tx', None)
        if tx is None:
            raise RuntimeError("Query must be executed within a transaction context")
            
        # Execute the query
        result = tx._tx.run(query, self.parameters)
        record = result.single()
        
        # Return the count
        if record:
            return record["count"]
        return 0