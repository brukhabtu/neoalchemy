"""
Clause element classes for Neo4j Cypher queries.

This module provides element classes for representing the different
clauses in a Cypher query, such as MATCH, WHERE, RETURN, etc.
"""

from abc import ABC
from typing import Any, Dict, List, Tuple, Union

from neoalchemy.core.cypher.core.keywords import CypherKeywords as K
from neoalchemy.core.cypher.elements.element import CypherElement


class CypherClause(CypherElement, ABC):
    """Base class for Cypher query clauses."""

    pass


class MatchClause(CypherClause):
    """Represents a MATCH clause in a Cypher query.

    Examples:
        MATCH (n:Person)
        MATCH (a)-[r:KNOWS]->(b)
    """

    def __init__(self, pattern: Union[CypherElement, List[CypherElement]], optional: bool = False):
        """Initialize a MATCH clause.

        Args:
            pattern: The pattern to match (NodePattern, PathPattern, or list of patterns)
            optional: Whether this is an OPTIONAL MATCH clause
        """
        self.patterns = [pattern] if not isinstance(pattern, list) else pattern
        self.optional = optional

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher MATCH clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        clause_type = K.OPTIONAL_MATCH if self.optional else K.MATCH
        pattern_parts = []

        for pattern in self.patterns:
            part, param_index = pattern.to_cypher(params, param_index)
            pattern_parts.append(part)

        return f"{clause_type} {', '.join(pattern_parts)}", param_index


class WhereClause(CypherClause):
    """Represents a WHERE clause in a Cypher query.

    Examples:
        WHERE n.age > 30
        WHERE n.name = 'Alice' AND n.active = true
    """

    def __init__(self, conditions: List[Any]):
        """Initialize a WHERE clause.

        Args:
            conditions: List of conditions to include in the WHERE clause
                       (can be CypherElements or Expr objects)
        """
        self.conditions = conditions

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher WHERE clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        if not self.conditions:
            return "", param_index

        condition_parts = []
        for condition in self.conditions:
            # Convert Expr objects to CypherElements if needed
            if hasattr(condition, "to_cypher_element"):
                element = condition.to_cypher_element()
                part, param_index = element.to_cypher(params, param_index)
            else:
                # If it's already a CypherElement
                part, param_index = condition.to_cypher(params, param_index)

            condition_parts.append(part)

        return f"{K.WHERE} {' AND '.join(condition_parts)}", param_index


class ReturnClause(CypherClause):
    """Represents a RETURN clause in a Cypher query.

    Examples:
        RETURN n
        RETURN n.name, n.age
        RETURN n.name AS name, count(*)
    """

    def __init__(
        self,
        items: List[Union[str, CypherElement, Tuple[Union[str, CypherElement], str]]],
        distinct: bool = False,
    ):
        """Initialize a RETURN clause.

        Args:
            items: List of items to return. Each item can be:
                  - A string (variable name)
                  - A CypherElement (expression)
                  - A tuple of (item, alias) for AS clauses
            distinct: Whether to use RETURN DISTINCT
        """
        self.items = items
        self.distinct = distinct

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher RETURN clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        distinct_str = " DISTINCT" if self.distinct else ""
        item_parts = []

        for item in self.items:
            if isinstance(item, tuple):
                # Handle items with aliases (AS clause)
                expr, alias = item
                if isinstance(expr, CypherElement):
                    expr_str, param_index = expr.to_cypher(params, param_index)
                else:
                    expr_str = str(expr)
                item_parts.append(f"{expr_str} AS {alias}")
            elif isinstance(item, CypherElement):
                # Handle expression items
                expr_str, param_index = item.to_cypher(params, param_index)
                item_parts.append(expr_str)
            else:
                # Handle string items (variable names)
                item_parts.append(str(item))

        return f"{K.RETURN}{distinct_str} {', '.join(item_parts)}", param_index


class OrderByClause(CypherClause):
    """Represents an ORDER BY clause in a Cypher query.

    Examples:
        ORDER BY n.name
        ORDER BY n.age DESC, n.name ASC
    """

    def __init__(
        self, items: List[Union[str, CypherElement, Tuple[Union[str, CypherElement], bool]]]
    ):
        """Initialize an ORDER BY clause.

        Args:
            items: List of items to order by. Each item can be:
                  - A string (property reference like "n.name")
                  - A CypherElement (expression)
                  - A tuple of (item, descending) where descending is a boolean
        """
        self.items = items

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher ORDER BY clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        item_parts = []

        for item in self.items:
            if isinstance(item, tuple):
                # Handle items with direction
                expr, descending = item
                direction = f" {K.DESC}" if descending else f" {K.ASC}"

                if isinstance(expr, CypherElement):
                    expr_str, param_index = expr.to_cypher(params, param_index)
                else:
                    expr_str = str(expr)

                item_parts.append(f"{expr_str}{direction}")
            elif isinstance(item, CypherElement):
                # Handle expression items (default ascending)
                expr_str, param_index = item.to_cypher(params, param_index)
                item_parts.append(expr_str)
            else:
                # Handle string items (variable or property names, default ascending)
                item_parts.append(str(item))

        return f"{K.ORDER_BY} {', '.join(item_parts)}", param_index


class LimitClause(CypherClause):
    """Represents a LIMIT clause in a Cypher query.

    Examples:
        LIMIT 10
    """

    def __init__(self, count: int):
        """Initialize a LIMIT clause.

        Args:
            count: Maximum number of results to return
        """
        self.count = count

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher LIMIT clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        return f"{K.LIMIT} {self.count}", param_index


class SkipClause(CypherClause):
    """Represents a SKIP clause in a Cypher query.

    Examples:
        SKIP 10
    """

    def __init__(self, count: int):
        """Initialize a SKIP clause.

        Args:
            count: Number of results to skip
        """
        self.count = count

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher SKIP clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        return f"{K.SKIP} {self.count}", param_index


class WithClause(CypherClause):
    """Represents a WITH clause in a Cypher query.

    The WITH clause is used to chain query parts and manipulate results
    between them.

    Examples:
        WITH n, count(r) AS num_relationships
        WITH distinct n.age AS age, collect(n) AS people
    """

    def __init__(
        self,
        items: List[Union[str, CypherElement, Tuple[Union[str, CypherElement], str]]],
        distinct: bool = False,
    ):
        """Initialize a WITH clause.

        Args:
            items: List of items to pass through. Each item can be:
                  - A string (variable name)
                  - A CypherElement (expression)
                  - A tuple of (item, alias) for AS clauses
            distinct: Whether to use WITH DISTINCT
        """
        self.items = items
        self.distinct = distinct

    def to_cypher(self, params: Dict[str, Any], param_index: int) -> Tuple[str, int]:
        """Convert to Cypher WITH clause.

        Args:
            params: Parameters dictionary to populate
            param_index: Current parameter index

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """
        distinct_str = " DISTINCT" if self.distinct else ""
        item_parts = []

        for item in self.items:
            if isinstance(item, tuple):
                # Handle items with aliases (AS clause)
                expr, alias = item
                if isinstance(expr, CypherElement):
                    expr_str, param_index = expr.to_cypher(params, param_index)
                else:
                    expr_str = str(expr)
                item_parts.append(f"{expr_str} AS {alias}")
            elif isinstance(item, CypherElement):
                # Handle expression items
                expr_str, param_index = item.to_cypher(params, param_index)
                item_parts.append(expr_str)
            else:
                # Handle string items (variable names)
                item_parts.append(str(item))

        return f"{K.WITH}{distinct_str} {', '.join(item_parts)}", param_index
