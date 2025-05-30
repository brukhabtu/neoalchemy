"""
Unit tests for field expression functionality.

These tests focus on FieldExpr methods in isolation,
testing their behavior without dependencies on other components.
"""

import pytest
from unittest.mock import Mock, patch

from neoalchemy.core.expressions.fields import FieldExpr


@pytest.mark.unit
class TestFieldExpr:
    """Test FieldExpr class methods in isolation."""

    def test_field_expr_construction(self):
        """Test FieldExpr constructor sets name correctly."""
        field = FieldExpr("name")
        
        assert field.name == "name"
        assert field._array_field_types == []

    def test_field_expr_construction_with_array_types(self):
        """Test FieldExpr constructor with array field types."""
        field = FieldExpr("tags", ["custom_array"])
        
        assert field.name == "tags"
        assert field._array_field_types == ["custom_array"]

    def test_is_array_field_with_known_array_names(self):
        """Test is_array_field returns True for known array field names."""
        # Test built-in array field names
        assert FieldExpr("participants").is_array_field() is True
        assert FieldExpr("keywords").is_array_field() is True
        assert FieldExpr("tags").is_array_field() is True
        assert FieldExpr("sources").is_array_field() is True

    def test_is_array_field_with_custom_array_types(self):
        """Test is_array_field returns True for custom array types."""
        field = FieldExpr("items", ["items"])
        assert field.is_array_field() is True

    def test_is_array_field_with_plural_names(self):
        """Test is_array_field returns True for plural field names."""
        assert FieldExpr("books").is_array_field() is True
        assert FieldExpr("authors").is_array_field() is True
        assert FieldExpr("categories").is_array_field() is True

    def test_is_array_field_excludes_double_s_endings(self):
        """Test is_array_field returns False for words ending in 'ss'."""
        assert FieldExpr("address").is_array_field() is False
        assert FieldExpr("business").is_array_field() is False
        assert FieldExpr("success").is_array_field() is False

    def test_is_array_field_with_singular_names(self):
        """Test is_array_field returns False for singular field names."""
        assert FieldExpr("name").is_array_field() is False
        assert FieldExpr("age").is_array_field() is False
        assert FieldExpr("email").is_array_field() is False

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_eq_with_null_calls_is_null(self, mock_operator):
        """Test __eq__ with None value calls is_null method."""
        field = FieldExpr("name")
        
        with patch.object(field, 'is_null') as mock_is_null:
            result = field.__eq__(None)
            mock_is_null.assert_called_once()
            assert result == mock_is_null.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_eq_creates_operator_expr(self, mock_operator):
        """Test __eq__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("name")
        
        result = field.__eq__("Alice")
        
        mock_operator.assert_called_once_with("name", "=", "Alice")
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ne_with_null_calls_is_not_null(self, mock_operator):
        """Test __ne__ with None value calls is_not_null method."""
        field = FieldExpr("name")
        
        with patch.object(field, 'is_not_null') as mock_is_not_null:
            result = field.__ne__(None)
            mock_is_not_null.assert_called_once()
            assert result == mock_is_not_null.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ne_creates_operator_expr(self, mock_operator):
        """Test __ne__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("name")
        
        result = field.__ne__("Alice")
        
        mock_operator.assert_called_once_with("name", "<>", "Alice")
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_gt_creates_operator_expr(self, mock_operator):
        """Test __gt__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("age")
        
        result = field.__gt__(30)
        
        mock_operator.assert_called_once_with("age", ">", 30)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_lt_creates_operator_expr(self, mock_operator):
        """Test __lt__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("age")
        
        result = field.__lt__(30)
        
        mock_operator.assert_called_once_with("age", "<", 30)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ge_creates_operator_expr(self, mock_operator):
        """Test __ge__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("age")
        
        result = field.__ge__(30)
        
        mock_operator.assert_called_once_with("age", ">=", 30)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_le_creates_operator_expr(self, mock_operator):
        """Test __le__ creates OperatorExpr with correct parameters."""
        field = FieldExpr("age")
        
        result = field.__le__(30)
        
        mock_operator.assert_called_once_with("age", "<=", 30)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_starts_with_creates_operator_expr(self, mock_operator):
        """Test starts_with creates OperatorExpr with correct parameters."""
        field = FieldExpr("name")
        
        result = field.starts_with("Al")
        
        mock_operator.assert_called_once_with("name", "STARTS WITH", "Al")
        assert result == mock_operator.return_value

    def test_startswith_calls_starts_with(self):
        """Test startswith method calls starts_with."""
        field = FieldExpr("name")
        
        with patch.object(field, 'starts_with') as mock_starts_with:
            result = field.startswith("Al")
            mock_starts_with.assert_called_once_with("Al")
            assert result == mock_starts_with.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_ends_with_creates_operator_expr(self, mock_operator):
        """Test ends_with creates OperatorExpr with correct parameters."""
        field = FieldExpr("name")
        
        result = field.ends_with("ice")
        
        mock_operator.assert_called_once_with("name", "ENDS WITH", "ice")
        assert result == mock_operator.return_value

    def test_endswith_calls_ends_with(self):
        """Test endswith method calls ends_with."""
        field = FieldExpr("name")
        
        with patch.object(field, 'ends_with') as mock_ends_with:
            result = field.endswith("ice")
            mock_ends_with.assert_called_once_with("ice")
            assert result == mock_ends_with.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_in_list_creates_operator_expr(self, mock_operator):
        """Test in_list creates OperatorExpr with correct parameters."""
        field = FieldExpr("role")
        values = ["admin", "user"]
        
        result = field.in_list(values)
        
        mock_operator.assert_called_once_with("role", "IN", values)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_one_of_creates_operator_expr(self, mock_operator):
        """Test one_of creates OperatorExpr with correct parameters."""
        field = FieldExpr("role")
        
        result = field.one_of("admin", "user", "guest")
        
        mock_operator.assert_called_once_with("role", "IN", ["admin", "user", "guest"])
        assert result == mock_operator.return_value

    def test_between_creates_range_expression(self):
        """Test between method creates a range expression."""
        field = FieldExpr("age")
        
        # Mock the operator creation
        with patch('neoalchemy.core.expressions.operators.OperatorExpr') as mock_operator:
            # Create mock expressions with proper __and__ method
            mock_ge_expr = Mock()
            mock_le_expr = Mock() 
            mock_and_result = Mock()
            
            # Configure the mocks
            mock_operator.side_effect = [mock_ge_expr, mock_le_expr]
            mock_ge_expr.__and__ = Mock(return_value=mock_and_result)
            
            result = field.between(18, 65)
            
            # Verify >= and <= expressions were created
            assert mock_operator.call_count == 2
            mock_operator.assert_any_call("age", ">=", 18)
            mock_operator.assert_any_call("age", "<=", 65)
            
            # Verify they were combined with AND
            mock_ge_expr.__and__.assert_called_once_with(mock_le_expr)
            assert result == mock_and_result

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_is_null_creates_operator_expr(self, mock_operator):
        """Test is_null creates OperatorExpr with correct parameters."""
        field = FieldExpr("email")
        
        result = field.is_null()
        
        mock_operator.assert_called_once_with("email", "IS NULL", None)
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_is_not_null_creates_operator_expr(self, mock_operator):
        """Test is_not_null creates OperatorExpr with correct parameters."""
        field = FieldExpr("email")
        
        result = field.is_not_null()
        
        mock_operator.assert_called_once_with("email", "IS NOT NULL", None)
        assert result == mock_operator.return_value

    def test_ror_with_list_calls_in_list(self):
        """Test __ror__ with list calls in_list method."""
        field = FieldExpr("role")
        values = ["admin", "user"]
        
        with patch.object(field, 'in_list') as mock_in_list:
            result = field.__ror__(values)
            mock_in_list.assert_called_once_with(values)
            assert result == mock_in_list.return_value

    def test_ror_with_tuple_calls_in_list(self):
        """Test __ror__ with tuple calls in_list method."""
        field = FieldExpr("role")
        values = ("admin", "user")
        
        with patch.object(field, 'in_list') as mock_in_list:
            result = field.__ror__(values)
            mock_in_list.assert_called_once_with(["admin", "user"])
            assert result == mock_in_list.return_value

    def test_ror_with_set_calls_in_list(self):
        """Test __ror__ with set calls in_list method."""
        field = FieldExpr("role")
        values = {"admin", "user"}
        
        with patch.object(field, 'in_list') as mock_in_list:
            result = field.__ror__(values)
            # Sets are unordered, so we need to check the call was made with a list containing the same elements
            mock_in_list.assert_called_once()
            called_args = mock_in_list.call_args[0][0]
            assert set(called_args) == {"admin", "user"}
            assert result == mock_in_list.return_value

    def test_ror_with_invalid_type_raises_error(self):
        """Test __ror__ with invalid type raises TypeError."""
        field = FieldExpr("role")
        
        with pytest.raises(TypeError) as exc_info:
            field.__ror__("invalid")
        
        assert "Unsupported 'in' operand" in str(exc_info.value)
        assert "role in str" in str(exc_info.value)

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_contains_method_for_array_fields(self, mock_operator):
        """Test contains method uses ANY_IN for array fields."""
        field = FieldExpr("tags", array_field_types=["tags"])
        
        result = field.contains("python")
        
        # Should use ANY_IN for array fields
        mock_operator.assert_called_once()
        call_args = mock_operator.call_args[0]
        assert call_args[0] == "tags"
        assert call_args[2] == "python"
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_contains_method_for_string_fields(self, mock_operator):
        """Test contains method uses CONTAINS for string fields."""
        field = FieldExpr("description")
        
        result = field.contains("keyword")
        
        # Should use CONTAINS for string fields
        mock_operator.assert_called_once()
        call_args = mock_operator.call_args[0]
        assert call_args[0] == "description"
        assert call_args[2] == "keyword"
        assert result == mock_operator.return_value

    @patch('neoalchemy.core.expressions.functions.FunctionExpr')
    def test_lower_method_creates_function_expr(self, mock_function):
        """Test lower method creates FunctionExpr with toLower."""
        field = FieldExpr("name")
        
        result = field.lower()
        
        mock_function.assert_called_once_with("toLower", ["name"])
        assert result == mock_function.return_value

    @patch('neoalchemy.core.expressions.functions.FunctionExpr')
    def test_upper_method_creates_function_expr(self, mock_function):
        """Test upper method creates FunctionExpr with toUpper."""
        field = FieldExpr("name")
        
        result = field.upper()
        
        mock_function.assert_called_once_with("toUpper", ["name"])
        assert result == mock_function.return_value

    def test_eq_with_none_calls_is_null(self):
        """Test __eq__ with None value calls is_null method."""
        field = FieldExpr("optional_field")
        
        with patch.object(field, 'is_null') as mock_is_null:
            result = field.__eq__(None)
            
            mock_is_null.assert_called_once()
            assert result == mock_is_null.return_value

    def test_ne_with_none_calls_is_not_null(self):
        """Test __ne__ with None value calls is_not_null method."""
        field = FieldExpr("required_field")
        
        with patch.object(field, 'is_not_null') as mock_is_not_null:
            result = field.__ne__(None)
            
            mock_is_not_null.assert_called_once()
            assert result == mock_is_not_null.return_value

    @patch('neoalchemy.core.expressions.fields.expression_state')
    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_lt_with_chained_expression(self, mock_operator, mock_state):
        """Test __lt__ handles chained expressions correctly."""
        field = FieldExpr("age")
        
        # Mock chain_expr with __and__ method
        mock_chain_expr = Mock()
        mock_and_result = Mock()
        # Need to properly configure the mock's __and__ method
        mock_chain_expr.__and__ = Mock(return_value=mock_and_result)
        mock_state.chain_expr = mock_chain_expr
        mock_state.is_capturing = True
        
        mock_expr = Mock()
        mock_operator.return_value = mock_expr
        
        result = field.__lt__(30)
        
        # Should create OperatorExpr and handle chaining
        mock_operator.assert_called_once_with("age", "<", 30)
        mock_chain_expr.__and__.assert_called_once_with(mock_expr)
        assert result == mock_and_result

    @patch('neoalchemy.core.expressions.fields.expression_state')
    @patch('neoalchemy.core.expressions.operators.OperatorExpr')
    def test_lt_stores_for_chaining_when_capturing(self, mock_operator, mock_state):
        """Test __lt__ stores expression for chaining when capturing."""
        field = FieldExpr("score")
        mock_state.chain_expr = None
        mock_state.is_capturing = True
        
        mock_expr = Mock()
        mock_operator.return_value = mock_expr
        
        result = field.__lt__(100)
        
        # Should store expression for potential chaining
        assert mock_state.chain_expr == mock_expr
        assert result == mock_expr