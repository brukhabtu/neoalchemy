"""
Unit tests for expression state management.

These tests focus on the expression state system in isolation.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.state import (
    ExpressionState,
    expression_state,
    expression_capture,
    reset_expression_state,
    capture_expression
)


@pytest.mark.unit
class TestExpressionState:
    """Test ExpressionState class in isolation."""

    def test_expression_state_construction(self):
        """Test ExpressionState constructor sets default values."""
        state = ExpressionState()
        
        assert state.last_expr is None
        assert state.chain_expr is None
        assert state.is_capturing is False

    def test_expression_state_construction_with_values(self):
        """Test ExpressionState constructor with initial values."""
        mock_last = Mock()
        mock_chain = Mock()
        
        state = ExpressionState(
            last_expr=mock_last,
            chain_expr=mock_chain,
            is_capturing=True
        )
        
        assert state.last_expr is mock_last
        assert state.chain_expr is mock_chain
        assert state.is_capturing is True

    def test_expression_state_fields_are_mutable(self):
        """Test ExpressionState fields can be modified."""
        state = ExpressionState()
        
        # Modify fields
        mock_expr = Mock()
        state.last_expr = mock_expr
        state.chain_expr = mock_expr
        state.is_capturing = True
        
        assert state.last_expr is mock_expr
        assert state.chain_expr is mock_expr
        assert state.is_capturing is True


@pytest.mark.unit
class TestExpressionStateGlobal:
    """Test global expression state management."""

    def test_global_expression_state_exists(self):
        """Test that global expression_state exists and is ExpressionState."""
        assert expression_state is not None
        assert isinstance(expression_state, ExpressionState)

    def test_reset_expression_state_clears_all_fields(self):
        """Test reset_expression_state clears all state fields."""
        # Set some state
        mock_expr1 = Mock()
        mock_expr2 = Mock()
        expression_state.last_expr = mock_expr1
        expression_state.chain_expr = mock_expr2
        
        # Reset state
        reset_expression_state()
        
        # Should be cleared
        assert expression_state.last_expr is None
        assert expression_state.chain_expr is None

    def test_reset_expression_state_preserves_capturing_flag(self):
        """Test reset_expression_state doesn't modify is_capturing flag."""
        # Set capturing state
        expression_state.is_capturing = True
        expression_state.last_expr = Mock()
        
        # Reset state
        reset_expression_state()
        
        # Capturing flag should be preserved, but expressions cleared
        assert expression_state.is_capturing is True
        assert expression_state.last_expr is None


@pytest.mark.unit
class TestExpressionCapture:
    """Test expression capture context manager."""

    def test_expression_capture_sets_capturing_flag(self):
        """Test expression_capture sets is_capturing to True."""
        # Start with capturing disabled
        expression_state.is_capturing = False
        
        with expression_capture():
            assert expression_state.is_capturing is True

    def test_expression_capture_restores_previous_flag(self):
        """Test expression_capture restores previous is_capturing value."""
        # Start with capturing enabled
        expression_state.is_capturing = True
        
        with expression_capture():
            # Should still be True inside context
            assert expression_state.is_capturing is True
        
        # Should be restored to True after context
        assert expression_state.is_capturing is True

    def test_expression_capture_restores_flag_from_false(self):
        """Test expression_capture restores False flag correctly."""
        # Start with capturing disabled
        expression_state.is_capturing = False
        
        with expression_capture():
            # Should be True inside context
            assert expression_state.is_capturing is True
        
        # Should be restored to False after context
        assert expression_state.is_capturing is False

    def test_expression_capture_restores_flag_on_exception(self):
        """Test expression_capture restores flag even when exception occurs."""
        # Start with capturing disabled
        expression_state.is_capturing = False
        
        try:
            with expression_capture():
                # Should be True inside context
                assert expression_state.is_capturing is True
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should be restored to False even after exception
        assert expression_state.is_capturing is False

    def test_expression_capture_nested_contexts(self):
        """Test nested expression_capture contexts work correctly."""
        # Start with capturing disabled
        expression_state.is_capturing = False
        
        with expression_capture():
            # First level - should be True
            assert expression_state.is_capturing is True
            
            with expression_capture():
                # Nested level - should still be True
                assert expression_state.is_capturing is True
            
            # Back to first level - should still be True
            assert expression_state.is_capturing is True
        
        # Outside all contexts - should be restored to False
        assert expression_state.is_capturing is False


@pytest.mark.unit
class TestCaptureExpressionDecorator:
    """Test capture_expression decorator."""

    def test_capture_expression_calls_original_function(self):
        """Test capture_expression decorator calls the original function."""
        mock_func = Mock(return_value="test_result")
        decorated = capture_expression(mock_func)
        
        result = decorated("arg1", "arg2", key="value")
        
        mock_func.assert_called_once_with("arg1", "arg2", key="value")
        assert result == "test_result"

    def test_capture_expression_preserves_return_value(self):
        """Test capture_expression decorator preserves return value."""
        def test_func(x, y):
            return x + y
        
        decorated = capture_expression(test_func)
        result = decorated(2, 3)
        
        assert result == 5

    def test_capture_expression_handles_no_args(self):
        """Test capture_expression decorator works with no arguments."""
        mock_func = Mock(return_value=42)
        decorated = capture_expression(mock_func)
        
        result = decorated()
        
        mock_func.assert_called_once_with()
        assert result == 42

    def test_capture_expression_handles_exceptions(self):
        """Test capture_expression decorator handles exceptions."""
        def error_func():
            raise ValueError("Test error")
        
        decorated = capture_expression(error_func)
        
        with pytest.raises(ValueError, match="Test error"):
            decorated()

    def test_capture_expression_preserves_function_metadata(self):
        """Test capture_expression decorator preserves function metadata."""
        def original_func():
            """Original function docstring."""
            return "result"
        
        decorated = capture_expression(original_func)
        
        # Function name and basic attributes should be preserved
        assert decorated.__name__ == "wrapper"  # Wrapper function name
        assert callable(decorated)


@pytest.mark.unit
class TestExpressionStateEdgeCases:
    """Test edge cases and error conditions."""

    def test_expression_state_with_none_expressions(self):
        """Test expression state handles None expressions correctly."""
        state = ExpressionState()
        
        # Setting to None should work
        state.last_expr = None
        state.chain_expr = None
        
        assert state.last_expr is None
        assert state.chain_expr is None

    def test_multiple_reset_calls(self):
        """Test multiple reset_expression_state calls are safe."""
        # Set some state
        expression_state.last_expr = Mock()
        expression_state.chain_expr = Mock()
        
        # Multiple resets should be safe
        reset_expression_state()
        reset_expression_state()
        reset_expression_state()
        
        assert expression_state.last_expr is None
        assert expression_state.chain_expr is None

    def test_expression_capture_with_already_true_flag(self):
        """Test expression_capture when flag is already True."""
        # Start with capturing already enabled
        expression_state.is_capturing = True
        
        with expression_capture():
            assert expression_state.is_capturing is True
        
        # Should remain True (was True before)
        assert expression_state.is_capturing is True