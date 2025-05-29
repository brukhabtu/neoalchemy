"""Helper utilities for integration tests."""
from typing import Dict, List, Any


class CypherAssertions:
    """Helper class for asserting Cypher query structure."""
    
    @staticmethod
    def assert_cypher_contains(cypher: str, *expected_parts: str) -> None:
        """Assert that Cypher contains all expected parts."""
        for part in expected_parts:
            assert part in cypher, f"Expected '{part}' in Cypher: {cypher}"
    
    @staticmethod
    def assert_cypher_structure(cypher: str, **expected: Any) -> None:
        """Assert Cypher has expected structure."""
        cypher_upper = cypher.upper()
        
        if "match" in expected:
            assert "MATCH" in cypher_upper
            if expected["match"]:
                assert expected["match"].upper() in cypher_upper
        
        if "where" in expected:
            if expected["where"]:
                assert "WHERE" in cypher_upper
            else:
                assert "WHERE" not in cypher_upper
        
        if "return" in expected:
            assert "RETURN" in cypher_upper
            if expected["return"]:
                assert expected["return"].upper() in cypher_upper
        
        if "order_by" in expected:
            if expected["order_by"]:
                assert "ORDER BY" in cypher_upper
            else:
                assert "ORDER BY" not in cypher_upper
        
        if "limit" in expected:
            if expected["limit"]:
                assert f"LIMIT {expected['limit']}" in cypher_upper
            else:
                assert "LIMIT" not in cypher_upper
    
    @staticmethod
    def assert_cypher_order(cypher: str, *clauses: str) -> None:
        """Assert that Cypher clauses appear in the expected order."""
        indices = []
        cypher_upper = cypher.upper()
        
        for clause in clauses:
            clause_upper = clause.upper()
            index = cypher_upper.find(clause_upper)
            assert index >= 0, f"Clause '{clause}' not found in Cypher: {cypher}"
            indices.append(index)
        
        for i in range(1, len(indices)):
            assert indices[i-1] < indices[i], \
                f"Clause '{clauses[i-1]}' should appear before '{clauses[i]}' in Cypher"


class MockAssertions:
    """Helper class for common mock assertions."""
    
    @staticmethod
    def assert_transaction_committed(mock_tx) -> None:
        """Assert that transaction was committed and cleaned up properly."""
        mock_tx.commit.assert_called_once()
        mock_tx.rollback.assert_not_called()
        mock_tx.close.assert_called_once()
    
    @staticmethod
    def assert_transaction_rolled_back(mock_tx) -> None:
        """Assert that transaction was rolled back and cleaned up properly."""
        mock_tx.rollback.assert_called_once()
        mock_tx.commit.assert_not_called()
        mock_tx.close.assert_called_once()
    
    @staticmethod
    def assert_query_executed_with(mock_tx, expected_keyword: str) -> str:
        """Assert that a query was executed containing the expected keyword."""
        mock_tx.run.assert_called()
        executed_query = mock_tx.run.call_args[0][0]
        assert expected_keyword in executed_query, \
            f"Expected '{expected_keyword}' in executed query: {executed_query}"
        return executed_query


def create_mock_records(data_dicts: List[Dict[str, Any]]) -> List[Any]:
    """Create mock Neo4j records from dictionaries."""
    from unittest.mock import MagicMock
    
    records = []
    for data in data_dicts:
        record = MagicMock()
        record.__getitem__.side_effect = lambda key, d=data: d[key]
        record.data.return_value = data
        records.append(record)
    return records