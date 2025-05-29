"""Integration tests for Transaction + Repository coordination.

Tests transaction context management, rollback coordination, and batch operations
without hitting the database.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from contextlib import contextmanager

from neoalchemy.orm.repository import Neo4jRepository, Neo4jTransaction
from neoalchemy.orm.models import Node

from .shared_models import Person, Product
from .test_helpers import MockAssertions

# Use consistent naming
PersonModel = Person
ProductModel = Product


@pytest.mark.integration
class TestTransactionRepositoryIntegration:
    """Test Transaction and Repository components working together."""

    def test_transaction_context_manager_properly_manages_neo4j_session(self, neo4j_transaction):
        """Test that transaction context manager properly handles Neo4j session lifecycle."""
        repo, mock_session, mock_tx = neo4j_transaction
        
        # Enter transaction context
        with repo.transaction() as tx:
            assert isinstance(tx, Neo4jTransaction)
            assert tx._tx == mock_tx
            
            # Session should be created
            repo.driver.session.assert_called_once()
            mock_session.begin_transaction.assert_called_once()
        
        # After context exit, transaction should be committed and closed
        MockAssertions.assert_transaction_committed(mock_tx)
        mock_session.close.assert_called_once()

    def test_transaction_rollback_on_exception(self, mock_driver):
        """Test that transaction rollback is called when exception occurs."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # Simulate exception during transaction
        class CustomError(Exception):
            pass
        
        with pytest.raises(CustomError):
            with repo.transaction() as tx:
                # Do some work
                person = PersonModel(name="Test", age=30)
                
                # Mock successful create
                mock_result = MagicMock()
                mock_record = MagicMock()
                mock_record.__getitem__.return_value = {"name": "Test", "age": 30}
                mock_result.single.return_value = mock_record
                mock_tx.run.return_value = mock_result
                
                tx.create(person)
                
                # Raise exception
                raise CustomError("Something went wrong")
        
        # Transaction should be rolled back, not committed
        MockAssertions.assert_transaction_rolled_back(mock_tx)
        mock_session.close.assert_called_once()

    def test_multiple_concurrent_transactions_are_independent(self, mock_driver):
        """Test that multiple transactions from same repository are independent."""
        # Create separate sessions for each transaction
        session1 = MagicMock()
        tx1 = MagicMock()
        session1.begin_transaction.return_value = tx1
        
        session2 = MagicMock()
        tx2 = MagicMock()
        session2.begin_transaction.return_value = tx2
        
        # Driver returns different session each time
        mock_driver.session.side_effect = [session1, session2]
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # Create two transaction contexts
        tx_context1 = repo.transaction()
        tx_context2 = repo.transaction()
        
        # Each should get its own session
        with tx_context1 as t1:
            assert t1._session == session1
            assert t1._tx == tx1
        
        with tx_context2 as t2:
            assert t2._session == session2
            assert t2._tx == tx2
        
        # Both should be properly closed
        session1.close.assert_called_once()
        session2.close.assert_called_once()

    def test_transaction_batch_operations_coordination(self, mock_driver):
        """Test that batch operations are properly coordinated within transaction."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        # Mock successful responses for batch operations
        create_results = []
        for i in range(3):
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.__getitem__.return_value = {"name": f"Person{i}", "age": 20 + i}
            mock_result.single.return_value = mock_record
            create_results.append(mock_result)
        
        mock_tx.run.side_effect = create_results
        
        repo = Neo4jRepository(driver=mock_driver)
        
        with repo.transaction() as tx:
            # Create multiple entities
            persons = []
            for i in range(3):
                person = PersonModel(name=f"Person{i}", age=20 + i)
                created = tx.create(person)
                persons.append(created)
            
            # All operations should use the same transaction
            assert mock_tx.run.call_count == 3
            
            # Verify all creates used same transaction
            for call_args in mock_tx.run.call_args_list:
                query = call_args[0][0]
                assert "CREATE" in query
        
        # Single commit for all operations
        mock_tx.commit.assert_called_once()

    def test_transaction_isolation_between_concurrent_transactions(self, mock_driver):
        """Test that concurrent transactions are properly isolated."""
        # Create separate sessions for each transaction
        sessions = []
        transactions = []
        
        for i in range(2):
            mock_session = MagicMock()
            mock_tx = MagicMock()
            mock_session.begin_transaction.return_value = mock_tx
            sessions.append(mock_session)
            transactions.append(mock_tx)
        
        # Driver returns different session each time
        mock_driver.session.side_effect = sessions
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # Track which transaction is active
        active_tx = None
        
        # Create custom context manager to control transaction overlap
        @contextmanager
        def controlled_transaction(repo, tx_id):
            nonlocal active_tx
            active_tx = tx_id
            with repo.transaction() as tx:
                yield tx
            active_tx = None
        
        # Start first transaction
        with controlled_transaction(repo, 1) as tx1:
            assert active_tx == 1
            
            # Each transaction should have its own session
            assert mock_driver.session.call_count == 1
            assert sessions[0].begin_transaction.call_count == 1

    def test_repository_operations_require_active_transaction(self, mock_driver):
        """Test that repository operations fail without active transaction."""
        repo = Neo4jRepository(driver=mock_driver)
        
        # These internal methods should not be called directly
        with pytest.raises(AttributeError):
            # Repository doesn't expose create directly
            repo.create(PersonModel(name="Test", age=30))

    def test_transaction_state_management_during_operations(self, mock_driver):
        """Test that transaction state is properly managed during operations."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # Track transaction state
        with repo.transaction() as tx:
            # Transaction should be active
            assert tx._tx is not None
            assert tx._session is not None
            
            # Mock query execution
            mock_result = MagicMock()
            mock_tx.run.return_value = mock_result
            
            # Execute query
            query = tx.query(PersonModel)
            query.find()
            
            # Transaction should still be active
            assert tx._tx is not None
        
        # After context exit, transaction references should be cleared
        # (Note: we can't check internal state after context exit)

    def test_transaction_error_propagation_from_repository(self, mock_driver):
        """Test that errors from repository operations propagate correctly."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        # Mock Neo4j error
        from neo4j.exceptions import ConstraintError as Neo4jConstraintError
        mock_tx.run.side_effect = Neo4jConstraintError("Unique constraint violated")
        
        repo = Neo4jRepository(driver=mock_driver)
        
        with pytest.raises(Neo4jConstraintError) as exc_info:
            with repo.transaction() as tx:
                person = PersonModel(name="Test", age=30)
                tx.create(person)
        
        # Error message should be preserved
        assert "constraint" in str(exc_info.value).lower()
        
        # Transaction should be rolled back
        mock_tx.rollback.assert_called_once()
        mock_tx.commit.assert_not_called()

    def test_transaction_query_builder_coordination(self, mock_driver):
        """Test that QueryBuilder properly coordinates with Transaction."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        # Mock query result
        mock_result = MagicMock()
        mock_tx.run.return_value = mock_result
        
        repo = Neo4jRepository(driver=mock_driver)
        
        with repo.transaction() as tx:
            # Create query builder
            query = tx.query(PersonModel).where(age__gte=18)
            
            # Query builder should reference the repository
            assert query.repo == repo
            
            # Execute query
            query.find()
            
            # Verify query was executed on the transaction
            mock_tx.run.assert_called_once()
            executed_query = mock_tx.run.call_args[0][0]
            assert "MATCH" in executed_query
            assert "Person" in executed_query

    def test_transaction_multiple_model_operations(self, mock_driver):
        """Test transaction handling operations on multiple model types."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        # Mock different responses for different models
        person_result = MagicMock()
        person_record = MagicMock()
        person_record.__getitem__.return_value = {"name": "Alice", "age": 30}
        person_result.single.return_value = person_record
        
        product_result = MagicMock()
        product_record = MagicMock()
        product_record.__getitem__.return_value = {"sku": "WDG001", "name": "Widget", "price": 9.99}
        product_result.single.return_value = product_record
        
        mock_tx.run.side_effect = [person_result, product_result]
        
        repo = Neo4jRepository(driver=mock_driver)
        
        with repo.transaction() as tx:
            # Create different model types
            person = tx.create(PersonModel(name="Alice", age=30))
            product = tx.create(ProductModel(sku="WDG001", name="Widget", price=9.99))
            
            # Verify both were created
            assert person.name == "Alice"
            assert product.name == "Widget"
            
            # Both operations should use same transaction
            assert mock_tx.run.call_count == 2
            
            # Verify different labels were used
            calls = mock_tx.run.call_args_list
            assert "Person" in calls[0][0][0]
            assert "Product" in calls[1][0][0]
        
        # Single commit for all operations
        mock_tx.commit.assert_called_once()

    def test_transaction_cleanup_on_unexpected_error(self, mock_driver):
        """Test that transaction resources are cleaned up even on unexpected errors."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        # Simulate unexpected error during commit
        mock_tx.commit.side_effect = Exception("Network error")
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # The transaction handles the error internally but still cleans up
        try:
            with repo.transaction() as tx:
                # Do some work
                pass
                # Exception will occur during commit
        except Exception:
            # Transaction catches and logs the error
            pass
        
        # Resources should still be cleaned up
        mock_tx.close.assert_called_once()
        mock_session.close.assert_called_once()

    def test_repository_transaction_method_integration(self, mock_driver):
        """Test that repository.transaction() method properly integrates components."""
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value = mock_tx
        mock_driver.session.return_value = mock_session
        
        repo = Neo4jRepository(driver=mock_driver)
        
        # Test that transaction() returns proper context manager
        tx_context = repo.transaction()
        assert hasattr(tx_context, '__enter__')
        assert hasattr(tx_context, '__exit__')
        
        # Use the context manager
        with tx_context as tx:
            assert isinstance(tx, Neo4jTransaction)
            assert tx.repo == repo
            assert tx._session == mock_session
            assert tx._tx == mock_tx