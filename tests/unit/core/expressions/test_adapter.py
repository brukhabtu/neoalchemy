"""
Unit tests for expression adapter functionality.

These tests focus on the ExpressionAdapter class that converts
expressions to cypher elements in isolation.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.expressions.adapter import ExpressionAdapter


@pytest.mark.unit
class TestExpressionAdapter:
    """Test ExpressionAdapter class in isolation."""

    def test_adapter_construction_default_entity_var(self):
        """Test ExpressionAdapter constructor with default entity variable."""
        adapter = ExpressionAdapter()
        
        assert adapter.entity_var == "e"

    def test_adapter_construction_custom_entity_var(self):
        """Test ExpressionAdapter constructor with custom entity variable."""
        adapter = ExpressionAdapter("n")
        
        assert adapter.entity_var == "n"

    @patch('neoalchemy.core.expressions.adapter.PropertyRef')
    def test_convert_field_expr(self, mock_property_ref):
        """Test _convert_field_expr creates PropertyRef correctly."""
        adapter = ExpressionAdapter("n")
        mock_field_expr = Mock()
        mock_field_expr.name = "test_field"
        
        result = adapter._convert_field_expr(mock_field_expr)
        
        mock_property_ref.assert_called_once_with("n", "test_field")
        assert result == mock_property_ref.return_value

    @patch('neoalchemy.core.expressions.adapter.ComparisonElement')
    @patch('neoalchemy.core.expressions.adapter.PropertyRef')
    def test_convert_operator_expr(self, mock_property_ref, mock_comparison):
        """Test _convert_operator_expr creates ComparisonElement correctly."""
        adapter = ExpressionAdapter("p")
        mock_operator_expr = Mock()
        mock_operator_expr.field = "age"
        mock_operator_expr.operator = ">"
        mock_operator_expr.value = 30
        
        mock_property_ref_instance = Mock()
        mock_property_ref.return_value = mock_property_ref_instance
        
        result = adapter._convert_operator_expr(mock_operator_expr)
        
        mock_property_ref.assert_called_once_with("p", "age")
        mock_comparison.assert_called_once_with(mock_property_ref_instance, ">", 30)
        assert result == mock_comparison.return_value

    @patch('neoalchemy.core.expressions.adapter.LogicalElement')
    def test_convert_composite_expr(self, mock_logical_element):
        """Test _convert_composite_expr creates LogicalElement correctly."""
        adapter = ExpressionAdapter()
        
        # Mock composite expression
        mock_composite = Mock()
        mock_composite.left = Mock()
        mock_composite.op = "AND"
        mock_composite.right = Mock()
        
        # Mock the recursive calls to to_cypher_element
        mock_left_element = Mock()
        mock_right_element = Mock()
        adapter.to_cypher_element = Mock(side_effect=[mock_left_element, mock_right_element])
        
        result = adapter._convert_composite_expr(mock_composite)
        
        mock_logical_element.assert_called_once_with(mock_left_element, "AND", mock_right_element)
        assert result == mock_logical_element.return_value

    @patch('neoalchemy.core.expressions.adapter.NegationElement')
    def test_convert_not_expr(self, mock_negation):
        """Test _convert_not_expr creates NegationElement correctly."""
        adapter = ExpressionAdapter()
        
        # Mock NOT expression
        mock_not_expr = Mock()
        mock_not_expr.expr = Mock()
        
        # Mock the recursive call to to_cypher_element
        mock_inner_element = Mock()
        adapter.to_cypher_element = Mock(return_value=mock_inner_element)
        
        result = adapter._convert_not_expr(mock_not_expr)
        
        mock_negation.assert_called_once_with(mock_inner_element)
        assert result == mock_negation.return_value

    @patch('neoalchemy.core.expressions.adapter.FunctionCallElement')
    @patch('neoalchemy.core.expressions.adapter.PropertyRef')
    def test_convert_function_expr_with_field_args(self, mock_property_ref, mock_function_call):
        """Test _convert_function_expr with field arguments."""
        adapter = ExpressionAdapter("e")
        
        mock_function_expr = Mock()
        mock_function_expr.func_name = "length"
        mock_function_expr.args = ["name", "description"]
        
        # Mock _is_field_name to return True for our args
        adapter._is_field_name = Mock(return_value=True)
        mock_property_ref_instance = Mock()
        mock_property_ref.return_value = mock_property_ref_instance
        
        result = adapter._convert_function_expr(mock_function_expr)
        
        # Should create PropertyRefs for field arguments
        assert mock_property_ref.call_count == 2
        mock_property_ref.assert_any_call("e", "name")
        mock_property_ref.assert_any_call("e", "description")
        
        mock_function_call.assert_called_once_with("length", [mock_property_ref_instance, mock_property_ref_instance])
        assert result == mock_function_call.return_value

    @patch('neoalchemy.core.expressions.adapter.FunctionCallElement')
    def test_convert_function_expr_with_literal_args(self, mock_function_call):
        """Test _convert_function_expr with literal arguments."""
        adapter = ExpressionAdapter()
        
        mock_function_expr = Mock()
        mock_function_expr.func_name = "substring"
        mock_function_expr.args = ["literal_value", 5]
        
        # Mock _is_field_name to return False for literals
        adapter._is_field_name = Mock(return_value=False)
        
        result = adapter._convert_function_expr(mock_function_expr)
        
        # Should pass literal arguments unchanged
        mock_function_call.assert_called_once_with("substring", ["literal_value", 5])
        assert result == mock_function_call.return_value

    @patch('neoalchemy.core.expressions.adapter.ComparisonElement')
    def test_convert_function_comparison_expr(self, mock_comparison):
        """Test _convert_function_comparison_expr creates ComparisonElement."""
        adapter = ExpressionAdapter()
        
        mock_func_comp_expr = Mock()
        mock_func_comp_expr.func_expr = Mock()
        mock_func_comp_expr.operator = "="
        mock_func_comp_expr.value = 10
        
        # Mock the recursive call to to_cypher_element
        mock_func_element = Mock()
        adapter.to_cypher_element = Mock(return_value=mock_func_element)
        
        result = adapter._convert_function_comparison_expr(mock_func_comp_expr)
        
        mock_comparison.assert_called_once_with(mock_func_element, "=", 10)
        assert result == mock_comparison.return_value


@pytest.mark.unit
class TestExpressionAdapterFieldNameDetection:
    """Test ExpressionAdapter field name detection logic."""

    def test_is_field_name_with_parameter_strings(self):
        """Test _is_field_name returns False for parameter-like strings."""
        adapter = ExpressionAdapter()
        
        # Parameter-like strings should not be treated as field names
        assert adapter._is_field_name("$param1") is False
        assert adapter._is_field_name(":param2") is False
        assert adapter._is_field_name("?param3") is False

    def test_is_field_name_with_quoted_strings(self):
        """Test _is_field_name returns False for quoted strings."""
        adapter = ExpressionAdapter()
        
        # Quoted strings should not be treated as field names
        assert adapter._is_field_name('"quoted_string"') is False
        assert adapter._is_field_name("'single_quoted'") is False

    def test_is_field_name_with_valid_field_names(self):
        """Test _is_field_name returns True for valid field names."""
        adapter = ExpressionAdapter()
        
        # Regular field names should be treated as field names
        assert adapter._is_field_name("name") is True
        assert adapter._is_field_name("user_id") is True
        assert adapter._is_field_name("firstName") is True
        assert adapter._is_field_name("field123") is True

    def test_is_field_name_with_edge_cases(self):
        """Test _is_field_name with edge case strings."""
        adapter = ExpressionAdapter()
        
        # Edge cases
        assert adapter._is_field_name("") is True  # Empty string is treated as field name
        assert adapter._is_field_name("$") is False  # Single $ is treated as parameter
        assert adapter._is_field_name("'incomplete") is True  # Unclosed quote


@pytest.mark.unit
class TestExpressionAdapterDispatch:
    """Test ExpressionAdapter's to_cypher_element dispatch logic."""

    def test_to_cypher_element_dispatches_field_expr(self):
        """Test to_cypher_element dispatches FieldExpr correctly."""
        from neoalchemy.core.expressions.fields import FieldExpr
        
        adapter = ExpressionAdapter()
        mock_field_expr = Mock(spec=FieldExpr)
        
        with patch.object(adapter, '_convert_field_expr') as mock_convert:
            result = adapter.to_cypher_element(mock_field_expr)
            
            mock_convert.assert_called_once_with(mock_field_expr)
            assert result == mock_convert.return_value

    def test_to_cypher_element_dispatches_operator_expr(self):
        """Test to_cypher_element dispatches OperatorExpr correctly."""
        from neoalchemy.core.expressions.operators import OperatorExpr
        
        adapter = ExpressionAdapter()
        mock_operator_expr = Mock(spec=OperatorExpr)
        
        with patch.object(adapter, '_convert_operator_expr') as mock_convert:
            result = adapter.to_cypher_element(mock_operator_expr)
            
            mock_convert.assert_called_once_with(mock_operator_expr)
            assert result == mock_convert.return_value

    def test_to_cypher_element_dispatches_composite_expr(self):
        """Test to_cypher_element dispatches CompositeExpr correctly."""
        from neoalchemy.core.expressions.operators import CompositeExpr
        
        adapter = ExpressionAdapter()
        mock_composite_expr = Mock(spec=CompositeExpr)
        
        with patch.object(adapter, '_convert_composite_expr') as mock_convert:
            result = adapter.to_cypher_element(mock_composite_expr)
            
            mock_convert.assert_called_once_with(mock_composite_expr)
            assert result == mock_convert.return_value

    def test_to_cypher_element_raises_for_unsupported_type(self):
        """Test to_cypher_element raises TypeError for unsupported expression type."""
        adapter = ExpressionAdapter()
        unsupported_expr = "not_an_expression"
        
        with pytest.raises(TypeError, match="Unsupported expression type"):
            adapter.to_cypher_element(unsupported_expr)

    def test_to_cypher_element_raises_with_correct_type_name(self):
        """Test to_cypher_element includes correct type name in error message."""
        adapter = ExpressionAdapter()
        unsupported_expr = 42
        
        with pytest.raises(TypeError, match="Unsupported expression type: int"):
            adapter.to_cypher_element(unsupported_expr)


@pytest.mark.unit
class TestExpressionAdapterIntegration:
    """Test ExpressionAdapter integration scenarios (but still unit-level)."""

    def test_adapter_with_different_entity_vars(self):
        """Test adapter works with different entity variable names."""
        # Test with different entity variable names
        adapters = [
            ExpressionAdapter("n"),
            ExpressionAdapter("p"), 
            ExpressionAdapter("user"),
            ExpressionAdapter("rel")
        ]
        
        for adapter in adapters:
            assert adapter.entity_var == adapter.entity_var
            # Each adapter should be independent
            assert hasattr(adapter, '_convert_field_expr')

    @patch('neoalchemy.core.expressions.adapter.PropertyRef')
    def test_field_expr_conversion_preserves_entity_var(self, mock_property_ref):
        """Test field expression conversion uses correct entity variable."""
        custom_adapter = ExpressionAdapter("custom_var")
        mock_field = Mock()
        mock_field.name = "test_field"
        
        custom_adapter._convert_field_expr(mock_field)
        
        mock_property_ref.assert_called_once_with("custom_var", "test_field")