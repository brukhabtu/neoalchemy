"""
Cypher query construction and compilation for Neo4j.

This module provides the CypherQuery class for assembling and compiling
complete Cypher queries from individual elements and clauses.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from neoalchemy.core.cypher.elements.clauses import (
    LimitClause,
    MatchClause,
    OrderByClause,
    ReturnClause,
    SkipClause,
    WhereClause,
    WithClause,
)
from neoalchemy.core.cypher.elements.element import CypherElement


class CypherQuery(CypherElement):
    """Represents a complete Cypher query.

    A Cypher query consists of multiple clauses that together form a complete
    query that can be executed against a Neo4j database. It implements the CypherElement
    interface for consistency with other elements.
    """

    def __init__(
        self,
        match: Union[MatchClause, List[MatchClause]],
        where: Optional[WhereClause] = None,
        with_clauses: Optional[List[WithClause]] = None,
        return_clause: Optional[ReturnClause] = None,
        order_by: Optional[OrderByClause] = None,
        limit: Optional[LimitClause] = None,
        skip: Optional[SkipClause] = None,
    ):
        """Initialize a Cypher query.

        Args:
            match: The MATCH clause(s) for the query
            where: Optional WHERE clause
            with_clauses: Optional list of WITH clauses for multi-part queries
            return_clause: Optional RETURN clause
            order_by: Optional ORDER BY clause
            limit: Optional LIMIT clause
            skip: Optional SKIP clause
        """
        self.match_clauses = [match] if not isinstance(match, list) else match
        self.where = where
        self.with_clauses = with_clauses or []
        self.return_clause = return_clause
        self.order_by = order_by
        self.limit = limit
        self.skip = skip

    def to_cypher(self, params: Dict[str, Any], param_index: int = 0) -> Tuple[str, int]:
        """Convert to Cypher query string.

        This method is consistent with the CypherElement interface but also
        serves as the main compilation entry point for queries.

        Args:
            params: Parameters dictionary to populate with values
            param_index: Current parameter index for generating unique parameter names

        Returns:
            Tuple of (cypher_expr, next_param_index)
        """

        # Compile all clauses and collect parameters
        query_parts = []

        # Process MATCH clauses
        for match_clause in self.match_clauses:
            part, param_index = match_clause.to_cypher(params, param_index)
            query_parts.append(part)

        # Process WHERE clause
        if self.where:
            part, param_index = self.where.to_cypher(params, param_index)
            if part:  # Only add if not empty
                query_parts.append(part)

        # Process WITH clauses (for multi-part queries)
        for with_clause in self.with_clauses:
            part, param_index = with_clause.to_cypher(params, param_index)
            query_parts.append(part)

        # Process RETURN clause
        if self.return_clause:
            part, param_index = self.return_clause.to_cypher(params, param_index)
            query_parts.append(part)

        # Process ORDER BY clause
        if self.order_by:
            part, param_index = self.order_by.to_cypher(params, param_index)
            query_parts.append(part)

        # Process SKIP clause
        if self.skip:
            part, param_index = self.skip.to_cypher(params, param_index)
            query_parts.append(part)

        # Process LIMIT clause
        if self.limit:
            part, param_index = self.limit.to_cypher(params, param_index)
            query_parts.append(part)

        # Join all parts with spaces
        query = " ".join(query_parts)

        # Return the query string and the next parameter index
        # The params dictionary is modified in-place
        return query, param_index
