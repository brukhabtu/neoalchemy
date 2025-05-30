"""
Tests for the Cypher query system.

This test suite verifies that the Cypher element architecture correctly generates
Cypher queries from high-level query representations.
"""


import pytest

from neoalchemy.core.cypher import (
    CypherQuery,
    LimitClause,
    MatchClause,
    NodePattern,
    OrderByClause,
    PathPattern,
    RelationshipPattern,
    ReturnClause,
    SkipClause,
    WhereClause,
    WithClause,
)
from neoalchemy.core.expressions import OperatorExpr


@pytest.mark.unit
class TestCypherQuery:
    """Test suite for the Cypher query system."""

    def test_simple_node_pattern(self):
        """Test compiling a simple node pattern."""
        pattern = NodePattern("n", ["Person"])
        params = {}
        cypher, _ = pattern.to_cypher(params, 0)
        assert cypher == "(n:Person)"
        assert params == {}

    def test_node_pattern_with_properties(self):
        """Test compiling a node pattern with properties."""
        pattern = NodePattern("p", ["Person"], {"name": "Alice", "age": 30})
        params = {}

        cypher, param_index = pattern.to_cypher(params, 0)
        assert cypher == "(p:Person {$p0})"
        assert params["p0"] == {"name": "Alice", "age": 30}

    def test_relationship_pattern(self):
        """Test compiling a relationship pattern."""
        pattern = RelationshipPattern("r", ["KNOWS"], direction="->")
        params = {}

        cypher, param_index = pattern.to_cypher(params, 0)
        assert cypher == "-[r:KNOWS]->"
        # params remain empty because there are no properties
        assert params == {}

    def test_path_pattern(self):
        """Test compiling a path pattern."""
        node1 = NodePattern("a", ["Person"])
        rel = RelationshipPattern("r", ["KNOWS"], direction="->")
        node2 = NodePattern("b", ["Person"])

        path = PathPattern(node1, rel, node2)
        params = {}

        cypher, param_index = path.to_cypher(params, 0)
        assert cypher == "(a:Person)-[r:KNOWS]->(b:Person)"
        assert params == {}

    def test_match_clause(self):
        """Test compiling a MATCH clause."""
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)
        params = {}

        cypher, param_index = match.to_cypher(params, 0)
        assert cypher == "MATCH (n:Person)"
        assert params == {}

    def test_match_with_path(self):
        """Test compiling a MATCH clause with a path pattern."""
        node1 = NodePattern("a", ["Person"])
        rel = RelationshipPattern("r", ["KNOWS"], direction="->")
        node2 = NodePattern("b", ["Person"])

        path = PathPattern(node1, rel, node2)
        match = MatchClause(path)
        params = {}

        cypher, param_index = match.to_cypher(params, 0)
        assert cypher == "MATCH (a:Person)-[r:KNOWS]->(b:Person)"
        assert params == {}

    def test_where_clause(self):
        """Test compiling a WHERE clause."""
        # Create conditions using OperatorExpr
        condition1 = OperatorExpr("age", ">", 30)
        condition2 = OperatorExpr("name", "=", "Alice")

        where = WhereClause([condition1, condition2])
        params = {}

        cypher, param_index = where.to_cypher(params, 0)
        assert "WHERE" in cypher
        assert "e.age > $p0" in cypher
        assert "e.name = $p1" in cypher
        assert "AND" in cypher
        assert params.get("p0") == 30
        assert params.get("p1") == "Alice"

    def test_return_clause(self):
        """Test compiling a RETURN clause."""
        ret = ReturnClause(["n", "r"])
        params = {}

        cypher, param_index = ret.to_cypher(params, 0)
        assert cypher == "RETURN n, r"
        assert params == {}

    def test_return_clause_with_alias(self):
        """Test compiling a RETURN clause with aliases."""
        ret = ReturnClause([("n.name", "name"), ("n.age", "age")])
        params = {}

        cypher, param_index = ret.to_cypher(params, 0)
        assert cypher == "RETURN n.name AS name, n.age AS age"
        assert params == {}

    def test_order_by_clause(self):
        """Test compiling an ORDER BY clause."""
        order = OrderByClause([("n.age", True), "n.name"])
        params = {}

        cypher, param_index = order.to_cypher(params, 0)
        assert cypher == "ORDER BY n.age DESC, n.name"
        assert params == {}

    def test_limit_clause(self):
        """Test compiling a LIMIT clause."""
        limit = LimitClause(10)
        params = {}

        cypher, param_index = limit.to_cypher(params, 0)
        assert cypher == "LIMIT 10"
        assert params == {}

    def test_complete_query(self):
        """Test compiling a complete Cypher query."""
        # Create the query components
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)

        condition = OperatorExpr("age", ">", 30)
        where = WhereClause([condition])

        ret = ReturnClause(["n"])
        order = OrderByClause([("n.name", False)])
        limit = LimitClause(5)

        # Create the complete query
        query = CypherQuery(
            match=match, where=where, return_clause=ret, order_by=order, limit=limit
        )

        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)

        # Verify the generated Cypher
        assert "MATCH (n:Person)" in cypher
        assert "WHERE e.age > $p0" in cypher
        assert "RETURN n" in cypher
        assert "ORDER BY n.name" in cypher
        assert "LIMIT 5" in cypher
        assert params.get("p0") == 30

    def test_multiple_match_clauses(self):
        """Test compiling a query with multiple MATCH clauses."""
        person = NodePattern("p", ["Person"])
        person_match = MatchClause(person)

        company = NodePattern("c", ["Company"])
        company_match = MatchClause(company)

        condition = OperatorExpr("industry", "=", "Technology")
        where = WhereClause([condition])

        ret = ReturnClause(["p", "c"])

        # Create the complete query
        query = CypherQuery(match=[person_match, company_match], where=where, return_clause=ret)

        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)

        # Verify the generated Cypher
        assert "MATCH (p:Person)" in cypher
        assert "MATCH (c:Company)" in cypher
        assert "WHERE e.industry = $p0" in cypher
        assert "RETURN p, c" in cypher
        assert params.get("p0") == "Technology"


@pytest.mark.unit
class TestComplexQueries:
    """Test suite for more complex Cypher queries."""

    def test_variable_length_relationship(self):
        """Test compiling a query with a variable-length relationship."""
        # Create patterns for a path with variable length relationship
        person1 = NodePattern("p1", ["Person"])
        # Variable length relationships aren't supported in the current implementation
        rel = RelationshipPattern("r", ["KNOWS"], direction="->")
        person2 = NodePattern("p2", ["Person"])

        path = PathPattern(person1, rel, person2)
        match = MatchClause(path)

        ret = ReturnClause(["p1", "r", "p2"])

        # Create the complete query
        query = CypherQuery(match=match, return_clause=ret)

        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)

        # Verify the generated Cypher
        assert "(p1:Person)" in cypher
        assert "(p2:Person)" in cypher
        assert "-[r:KNOWS]->" in cypher
        assert "RETURN p1, r, p2" in cypher
        assert params == {}

    def test_multiple_relationship_types(self):
        """Test compiling a query with multiple relationship types."""
        # Create patterns for a path with multiple relationship types
        person = NodePattern("p", ["Person"])
        rel = RelationshipPattern("r", ["KNOWS", "WORKS_WITH"], direction="->")
        colleague = NodePattern("c", ["Person"])

        path = PathPattern(person, rel, colleague)
        match = MatchClause(path)

        ret = ReturnClause(["p", "r", "c"])

        # Create the complete query
        query = CypherQuery(match=match, return_clause=ret)

        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)

        # Verify the generated Cypher
        assert "(p:Person)" in cypher
        assert "(c:Person)" in cypher
        assert "-[r:KNOWS|WORKS_WITH]->" in cypher
        assert "RETURN p, r, c" in cypher
        assert params == {}

    def test_relationship_with_properties(self):
        """Test compiling a query with relationship properties."""
        # Create patterns for a path with relationship properties
        person = NodePattern("p", ["Person"])
        rel = RelationshipPattern(
            "r", ["WORKS_FOR"], properties={"role": "Developer", "since": 2020}, direction="->"
        )
        company = NodePattern("c", ["Company"])

        path = PathPattern(person, rel, company)
        match = MatchClause(path)

        ret = ReturnClause(["p", "r", "c"])

        # Create the complete query
        query = CypherQuery(match=match, return_clause=ret)

        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)

        # Verify the generated Cypher
        assert "(p:Person)" in cypher
        assert "(c:Company)" in cypher
        assert "-[r:WORKS_FOR" in cypher
        assert "{$p0}" in cypher  # Properties are passed as a single parameter
        assert "]->" in cypher
        assert "RETURN p, r, c" in cypher
        # Check that the properties were added to params correctly
        assert "p0" in params
        assert params["p0"] == {"role": "Developer", "since": 2020}


@pytest.mark.unit  
class TestCypherQueryMissingCoverage:
    """Test cases to cover missing lines in CypherQuery."""
    
    def test_query_with_with_clauses(self):
        """Test CypherQuery with WITH clauses (covers lines 89-90)."""
        # Create basic components
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)
        
        # Create WITH clause
        with_clause = WithClause(["n"])
        
        ret = ReturnClause(["n"])
        
        # Create query with WITH clauses
        query = CypherQuery(
            match=match,
            with_clauses=[with_clause],
            return_clause=ret
        )
        
        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)
        
        # Verify WITH clause is included
        assert "MATCH (n:Person)" in cypher
        assert "WITH n" in cypher
        assert "RETURN n" in cypher
        assert params == {}
    
    def test_query_with_skip_clause(self):
        """Test CypherQuery with SKIP clause (covers lines 104-105)."""
        # Create basic components
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)
        
        ret = ReturnClause(["n"])
        skip = SkipClause(10)
        
        # Create query with SKIP clause
        query = CypherQuery(
            match=match,
            return_clause=ret,
            skip=skip
        )
        
        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)
        
        # Verify SKIP clause is included
        assert "MATCH (n:Person)" in cypher
        assert "RETURN n" in cypher
        assert "SKIP 10" in cypher
        assert params == {}
    
    def test_query_with_multiple_with_clauses(self):
        """Test CypherQuery with multiple WITH clauses."""
        # Create basic components
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)
        
        # Create multiple WITH clauses
        with1 = WithClause(["n"])
        with2 = WithClause([("n.name", "name")])
        
        ret = ReturnClause(["name"])
        
        # Create query with multiple WITH clauses
        query = CypherQuery(
            match=match,
            with_clauses=[with1, with2],
            return_clause=ret
        )
        
        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)
        
        # Verify both WITH clauses are included
        assert "MATCH (n:Person)" in cypher
        assert "WITH n" in cypher
        assert "WITH n.name AS name" in cypher
        assert "RETURN name" in cypher
        assert params == {}
    
    def test_query_with_skip_and_limit(self):
        """Test CypherQuery with both SKIP and LIMIT clauses."""
        # Create basic components
        node = NodePattern("n", ["Person"])
        match = MatchClause(node)
        
        ret = ReturnClause(["n"])
        skip = SkipClause(5)
        limit = LimitClause(10)
        
        # Create query with both SKIP and LIMIT
        query = CypherQuery(
            match=match,
            return_clause=ret,
            skip=skip,
            limit=limit
        )
        
        # Compile the query
        params = {}
        cypher, param_index = query.to_cypher(params)
        
        # Verify both SKIP and LIMIT clauses are included (SKIP should come before LIMIT)
        assert "MATCH (n:Person)" in cypher
        assert "RETURN n" in cypher
        assert "SKIP 5" in cypher
        assert "LIMIT 10" in cypher
        
        # Verify order: SKIP should come before LIMIT in the query
        skip_pos = cypher.index("SKIP 5")
        limit_pos = cypher.index("LIMIT 10")
        assert skip_pos < limit_pos
        
        assert params == {}


