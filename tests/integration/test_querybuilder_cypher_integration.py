"""Integration tests for QueryBuilder → Cypher generation.

Tests the complete query building pipeline from API calls to Cypher generation
without hitting the database.
"""
import pytest
from unittest.mock import MagicMock

from neoalchemy.orm.repository import Neo4jRepository
from neoalchemy.orm.models import Node, Relationship
from neoalchemy.orm.query import QueryBuilder

from .shared_models import Person, Company, Product, WorksAt
from .test_helpers import CypherAssertions, MockAssertions

# Use consistent naming
PersonModel = Person
CompanyModel = Company
WorksAtModel = WorksAt


@pytest.mark.integration
class TestQueryBuilderCypherIntegration:
    """Test QueryBuilder and Cypher generation working together."""

    def test_simple_match_query_generation(self, neo4j_transaction):
        """Test that simple match queries generate correct Cypher."""
        repo, _, _ = neo4j_transaction
        
        with repo.transaction() as tx:
            query = tx.query(PersonModel)
            
            # Build the Cypher query
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate basic MATCH query
            CypherAssertions.assert_cypher_contains(
                cypher_str,
                "MATCH (e:Person)",
                "RETURN e"
            )

    def test_where_clause_generation_with_equality(self, mock_driver):
        """Test WHERE clause generation with equality conditions."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            query = tx.query(PersonModel).where(name="Alice")
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate WHERE clause
            assert "WHERE" in cypher_str
            assert "e.name = $" in cypher_str
            assert any("Alice" in str(v) for v in params.values())

    def test_complex_where_conditions_generation(self, mock_driver):
        """Test complex WHERE conditions with multiple operators."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # Use field expressions for complex conditions
            query = tx.query(PersonModel).where(
                PersonModel.field("age") >= 18,
                PersonModel.field("age") <= 65,
                PersonModel.field("active") == True
            )
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate multiple conditions
            assert "WHERE" in cypher_str
            assert ">=" in cypher_str
            assert "<=" in cypher_str
            assert "AND" in cypher_str

    def test_order_by_clause_generation(self, mock_driver):
        """Test ORDER BY clause generation."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            query = tx.query(PersonModel).order_by("name", "DESC")
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate ORDER BY clause
            assert "ORDER BY" in cypher_str
            assert "e.name DESC" in cypher_str

    def test_limit_clause_generation(self, mock_driver):
        """Test LIMIT clause generation."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            query = tx.query(PersonModel).limit(10)
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate LIMIT clause
            assert "LIMIT 10" in cypher_str

    def test_combined_query_features_generation(self, neo4j_transaction):
        """Test query with all features combined."""
        repo, _, _ = neo4j_transaction
        
        with repo.transaction() as tx:
            query = (tx.query(PersonModel)
                    .where(PersonModel.field("age") > 25)
                    .order_by("name")
                    .limit(5))
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should have all clauses in correct order
            CypherAssertions.assert_cypher_order(
                cypher_str,
                "MATCH",
                "WHERE",
                "RETURN",
                "ORDER BY",
                "LIMIT"
            )
            
            # Verify specific content
            CypherAssertions.assert_cypher_structure(
                cypher_str,
                match="(e:Person)",
                where=True,
                order_by=True,
                limit=5
            )

    def test_create_query_generation(self, mock_driver):
        """Test CREATE query generation for new nodes."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            person = PersonModel(name="Bob", age=30, email="bob@example.com", tags=["developer"])
            
            # Mock the create operation to capture the query
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.__getitem__.return_value = {"name": "Bob", "age": 30, "email": "bob@example.com", "tags": ["developer"]}
            mock_result.single.return_value = mock_record
            mock_tx.run.return_value = mock_result
            
            tx.create(person)
            
            # Verify CREATE query was generated
            assert mock_tx.run.called
            executed_query = mock_tx.run.call_args[0][0]
            assert "CREATE" in executed_query
            assert ":Person" in executed_query

    def test_update_query_generation(self, mock_driver):
        """Test UPDATE query generation for existing nodes."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # First get a person
            query_result = MagicMock()
            query_result.data.return_value = [{"name": "Alice", "age": 25, "email": "alice@example.com"}]
            mock_tx.run.return_value = query_result
            
            persons = tx.query(PersonModel).find()
            
            # Now update
            if persons:
                person = persons[0]
                person.age = 26
                
                # Mock the update
                update_result = MagicMock()
                update_record = MagicMock()
                update_record.__getitem__.return_value = {"name": "Alice", "age": 26, "email": "alice@example.com"}
                update_result.single.return_value = update_record
                mock_tx.run.return_value = update_result
                
                tx.update(person)
                
                # Verify SET query was generated
                calls = mock_tx.run.call_args_list
                update_call = calls[-1]
                executed_query = update_call[0][0]
                assert "MATCH" in executed_query
                assert "SET" in executed_query

    def test_delete_query_generation(self, mock_driver):
        """Test DELETE query generation."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # Mock finding a person
            query_result = MagicMock()
            query_result.data.return_value = [{"name": "Charlie", "age": 35, "email": "charlie@example.com"}]
            mock_tx.run.return_value = query_result
            
            persons = tx.query(PersonModel).find()
            
            if persons:
                person = persons[0]
                
                # Mock the delete
                delete_result = MagicMock()
                mock_tx.run.return_value = delete_result
                
                tx.delete(person)
                
                # Verify DELETE query was generated
                calls = mock_tx.run.call_args_list
                delete_call = calls[-1]
                executed_query = delete_call[0][0]
                assert "MATCH" in executed_query
                assert "DELETE" in executed_query

    def test_array_field_contains_query_generation(self, mock_driver):
        """Test query generation for array contains operations."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # Query for tags containing a value
            query = tx.query(PersonModel).where_contains("tags", "python")
            
            cypher_query = query._build_query()
            params = {}
            cypher_str, _ = cypher_query.to_cypher(params)
            
            # Should generate array contains condition
            assert "WHERE" in cypher_str
            # The actual Cypher uses ANY() function for array contains
            assert "ANY" in cypher_str
            assert "e.tags" in cypher_str
            assert any("python" in str(v) for v in params.values())

    def test_multiple_model_types_query_coordination(self, mock_driver):
        """Test that different model types generate correct label-specific queries."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # Query PersonModel
            person_query = tx.query(PersonModel)
            person_cypher = person_query._build_query()
            person_params = {}
            person_str, _ = person_cypher.to_cypher(person_params)
            
            assert ":Person" in person_str
            
            # Query CompanyModel
            company_query = tx.query(CompanyModel)
            company_cypher = company_query._build_query()
            company_params = {}
            company_str, _ = company_cypher.to_cypher(company_params)
            
            assert ":Company" in company_str
            assert ":Person" not in company_str

    def test_query_parameter_isolation(self, mock_driver):
        """Test that query parameters are properly isolated between queries."""
        repo = Neo4jRepository(driver=mock_driver)
        
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        with repo.transaction() as tx:
            # Create two queries with different parameters
            query1 = tx.query(PersonModel).where(name="Alice")
            query2 = tx.query(PersonModel).where(name="Bob")
            
            # Generate Cypher for both
            cypher1 = query1._build_query()
            params1 = {}
            str1, _ = cypher1.to_cypher(params1)
            
            cypher2 = query2._build_query()
            params2 = {}
            str2, _ = cypher2.to_cypher(params2)
            
            # Parameters should be isolated
            assert any("Alice" in str(v) for v in params1.values())
            assert any("Bob" in str(v) for v in params2.values())
            assert not any("Bob" in str(v) for v in params1.values())
            assert not any("Alice" in str(v) for v in params2.values())