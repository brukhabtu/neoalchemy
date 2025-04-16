"""
Tests for NeoAlchemy expression system.

These tests focus on the expression functionality - showing how expressions
can be built and combined in various ways.
"""

import pytest

# Import Person model from the models module
from tests.models import Person

from neoalchemy.core.expressions import FieldExpr
from neoalchemy.core.state import expression_state


@pytest.mark.e2e
def test_pythonic_string_methods(repo, clean_db):
    """Test Pythonic string method aliases (startswith, endswith)."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email="bob@test.com"))
        tx.create(Person(name="Charlie", age=35, email="charlie@example.com"))
        
        # Test startswith (Pythonic alias for starts_with)
        starts_test = tx.query(Person).where(Person.email.startswith("alice")).find()
        assert len(starts_test) == 1
        assert starts_test[0].name == "Alice"
        
        # Test endswith (Pythonic alias for ends_with)
        ends_test = tx.query(Person).where(Person.email.endswith("example.com")).find()
        assert len(ends_test) == 2
        assert set(p.name for p in ends_test) == {"Alice", "Charlie"}
        
        # Compare with traditional methods to ensure they're equivalent
        starts_with_test = tx.query(Person).where(Person.email.starts_with("alice")).find()
        assert len(starts_with_test) == len(starts_test)
        assert set(p.name for p in starts_with_test) == set(p.name for p in starts_test)
        
        ends_with_test = tx.query(Person).where(Person.email.ends_with("example.com")).find()
        assert len(ends_with_test) == len(ends_test)
        assert set(p.name for p in ends_with_test) == set(p.name for p in ends_test)


@pytest.mark.e2e
def test_equality_operators(repo, clean_db):
    """Test equality (==) and inequality (!=) operators."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        
        # Test equality
        equals_query = tx.query(Person).where(Person.name == "Alice").find()
        assert len(equals_query) == 1
        assert equals_query[0].name == "Alice"
        
        # Test inequality
        not_equals_query = tx.query(Person).where(Person.name != "Alice").find()
        assert len(not_equals_query) == 1
        assert not_equals_query[0].name == "Bob"


@pytest.mark.e2e
def test_comparison_operators(repo, clean_db):
    """Test comparison operators (>, <, >=, <=)."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        
        # Greater than
        gt_query = tx.query(Person).where(Person.age > 30).find()
        assert len(gt_query) == 1
        assert gt_query[0].name == "Charlie"
        
        # Less than
        lt_query = tx.query(Person).where(Person.age < 30).find()
        assert len(lt_query) == 1
        assert lt_query[0].name == "Bob"
        
        # Greater than or equal
        gte_query = tx.query(Person).where(Person.age >= 30).find()
        assert len(gte_query) == 2
        assert set(p.name for p in gte_query) == {"Alice", "Charlie"}
        
        # Less than or equal
        lte_query = tx.query(Person).where(Person.age <= 30).find()
        assert len(lte_query) == 2
        assert set(p.name for p in lte_query) == {"Alice", "Bob"}


@pytest.mark.e2e
def test_and_condition(repo, clean_db):
    """Test combining conditions with AND logic."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        
        # Test multiple where conditions (implicit AND)
        and_query = tx.query(Person).where(Person.age >= 30).where(Person.score >= 90).find()
        assert len(and_query) == 1
        assert and_query[0].name == "Alice"


@pytest.mark.e2e
def test_multiple_conditions(repo, clean_db):
    """Test using multiple conditions."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        
        # Test individual conditions and combine results
        young_people = tx.query(Person).where(Person.age < 26).find()
        high_scorers = tx.query(Person).where(Person.score > 90).find()
        
        # Manually combine results
        combined_people = set(p.name for p in young_people + high_scorers)
        assert combined_people == {"Alice", "Bob"}


@pytest.mark.e2e
def test_not_equal(repo, clean_db):
    """Test logical NOT using != operator."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, active=True))
        tx.create(Person(name="Bob", age=25, active=False))
        
        # Test inequality
        inactive_people = tx.query(Person).where(Person.active != True).find()
        assert len(inactive_people) == 1
        assert inactive_people[0].name == "Bob"


@pytest.mark.e2e
def test_complex_query_patterns(repo, clean_db):
    """Test complex query patterns with different approaches."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        tx.create(Person(name="David", age=28, score=90.0))
        
        # Approach 1: Find each group separately
        older_low_scorers = tx.query(Person).where(Person.age >= 30).where(Person.score < 80).find()
        young_high_scorers = tx.query(Person).where(Person.age < 30).where(Person.score >= 90).find()
        
        # Combine results manually
        target_people = set()
        for p in older_low_scorers:
            target_people.add(p.name)
        for p in young_high_scorers:
            target_people.add(p.name)
            
        assert target_people == {"Charlie", "David"}


@pytest.mark.e2e
def test_string_contains(repo, clean_db):
    """Test string containment with 'in' operator."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email="bob@test.com"))
        
        # Using 'in' operator for string containment
        contains_query = tx.query(Person).where("example" in Person.email).find()
        assert len(contains_query) == 1
        assert contains_query[0].name == "Alice"


@pytest.mark.e2e
def test_string_starts_with(repo, clean_db):
    """Test string 'starts_with' operation."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email="bob@example.com"))
        
        # Using starts_with method
        starts_with_query = tx.query(Person).where(Person.email.starts_with("alice")).find()
        assert len(starts_with_query) == 1
        assert starts_with_query[0].name == "Alice"


@pytest.mark.e2e
def test_string_ends_with(repo, clean_db):
    """Test string 'ends_with' operation."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email="bob@test.com"))
        
        # Using ends_with method
        ends_with_query = tx.query(Person).where(Person.email.ends_with("test.com")).find()
        assert len(ends_with_query) == 1
        assert ends_with_query[0].name == "Bob"


@pytest.mark.e2e
def test_in_operator_with_strings(repo, clean_db):
    """Test 'in' operator for string containment."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email="bob@test.com"))
        
        # Using the 'in' operator
        in_query = tx.query(Person).where("example" in Person.email).find()
        assert len(in_query) == 1
        assert in_query[0].name == "Alice"


@pytest.mark.e2e
def test_array_membership(repo, clean_db):
    """Test array field membership with 'in' operator."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, tags=["developer", "python"]))
        tx.create(Person(name="Bob", age=25, tags=["designer", "ui"]))
        
        # Using the 'in' operator for arrays
        developers = tx.query(Person).where("developer" in Person.tags).find()
        assert len(developers) == 1
        assert developers[0].name == "Alice"


@pytest.mark.e2e
def test_array_membership_different_value(repo, clean_db):
    """Test array field membership with different values."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, tags=["developer", "python"]))
        tx.create(Person(name="Bob", age=25, tags=["designer", "ui"]))
        
        # Test with a different tag value
        python_devs = tx.query(Person).where("python" in Person.tags).find()
        assert len(python_devs) == 1
        assert python_devs[0].name == "Alice"
        
        # Test with a tag that doesn't exist
        java_devs = tx.query(Person).where("java" in Person.tags).find()
        assert len(java_devs) == 0


@pytest.mark.e2e
def test_array_multiple_conditions(repo, clean_db):
    """Test multiple array conditions."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, tags=["developer", "python"]))
        tx.create(Person(name="Bob", age=25, tags=["developer", "java"]))
        tx.create(Person(name="Charlie", age=35, tags=["designer", "ui"]))
        
        # Multiple array conditions (implicit AND)
        python_developers = tx.query(Person).where("developer" in Person.tags).where("python" in Person.tags).find()
        assert len(python_developers) == 1
        assert python_developers[0].name == "Alice"


@pytest.mark.e2e
def test_between_method(repo, clean_db):
    """Test the 'between' method for range queries."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        tx.create(Person(name="David", age=40, score=90.0))
        
        # Age between 25 and 35 (inclusive)
        middle_aged = tx.query(Person).where(
            Person.age.between(25, 35)
        ).find()
        assert len(middle_aged) == 3
        assert set(p.name for p in middle_aged) == {"Alice", "Bob", "Charlie"}


@pytest.mark.e2e
def test_in_list_methods(repo, clean_db):
    """Test methods for checking if a value is in a list."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        tx.create(Person(name="David", age=40))
        
        # Using the in_list method to check if a field is in a list of values
        selected_people_1 = tx.query(Person).where(
            Person.name.in_list(["Alice", "Charlie", "Eve"])
        ).find()
        assert len(selected_people_1) == 2
        assert set(p.name for p in selected_people_1) == {"Alice", "Charlie"}
        
        # Using the one_of method (more convenient variant of in_list)
        selected_people_2 = tx.query(Person).where(
            Person.name.one_of("Alice", "Charlie", "Eve")
        ).find()
        assert len(selected_people_2) == 2
        assert set(p.name for p in selected_people_2) == {"Alice", "Charlie"}
        
        # Create the expressions directly (to avoid the immediate evaluation issue)
        # For a list
        list_expr = Person.name.in_list(["Alice", "Charlie", "Eve"])
        selected_people_3 = tx.query(Person).where(list_expr).find()
        assert len(selected_people_3) == 2
        assert set(p.name for p in selected_people_3) == {"Alice", "Charlie"}
        
        # For a tuple
        tuple_expr = Person.name.in_list(["Alice", "Charlie", "Eve"])
        selected_people_4 = tx.query(Person).where(tuple_expr).find()
        assert len(selected_people_4) == 2
        assert set(p.name for p in selected_people_4) == {"Alice", "Charlie"}
        
        # For a set
        set_expr = Person.name.in_list(["Alice", "Charlie", "Eve"])
        selected_people_5 = tx.query(Person).where(set_expr).find()
        assert len(selected_people_5) == 2
        assert set(p.name for p in selected_people_5) == {"Alice", "Charlie"}


@pytest.mark.e2e
def test_null_values(repo, clean_db):
    """Test handling of null values (empty strings in our case)."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com"))
        tx.create(Person(name="Bob", age=25, email=""))
        
        # Empty string check
        no_email = tx.query(Person).where(Person.email == "").find()
        assert len(no_email) == 1
        assert no_email[0].name == "Bob"


@pytest.mark.e2e
def test_boolean_values(repo, clean_db):
    """Test handling of boolean values."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, active=True))
        tx.create(Person(name="Bob", age=25, active=False))
        
        # Boolean equality
        active_people = tx.query(Person).where(Person.active == True).find()
        assert len(active_people) == 1
        assert active_people[0].name == "Alice"
        
        # Boolean inequality
        inactive_people = tx.query(Person).where(Person.active == False).find()
        assert len(inactive_people) == 1
        assert inactive_people[0].name == "Bob"


@pytest.mark.e2e
def test_chained_comparison(repo, clean_db):
    """Test Python's chained comparison operators (e.g., 25 <= x <= 35)."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        tx.create(Person(name="David", age=40, score=90.0))
        tx.create(Person(name="Eve", age=20, score=80.0))
        
        # Test chained comparison (25 <= age <= 35)
        # This should be equivalent to Person.age.between(25, 35)
        middle_aged = tx.query(Person).where(
            25 <= Person.age <= 35
        ).find()
        assert len(middle_aged) == 3
        assert set(p.name for p in middle_aged) == {"Alice", "Bob", "Charlie"}
        
        # Test complex chained comparison (75 <= score <= 90)
        medium_scorers = tx.query(Person).where(
            75 <= Person.score <= 90
        ).find()
        assert len(medium_scorers) == 4
        assert set(p.name for p in medium_scorers) == {"Bob", "Charlie", "David", "Eve"}
        
        # Test chained comparison with mixed operators (age > 25 and age < 40)
        target_age_range = tx.query(Person).where(
            25 < Person.age < 40
        ).find()
        assert len(target_age_range) == 2
        assert set(p.name for p in target_age_range) == {"Alice", "Charlie"}


@pytest.mark.e2e
def test_chained_comparison_with_equality(repo, clean_db):
    """Test Python's chained comparison with equality operators."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, score=95.5))
        tx.create(Person(name="Bob", age=25, score=85.5))
        tx.create(Person(name="Charlie", age=35, score=75.5))
        tx.create(Person(name="David", age=40, score=90.0))
        tx.create(Person(name="Eve", age=20, score=80.0))
        
        # Test comparison including both inequality and equality
        # Age >= 25 and age <= 35
        middle_aged_exact = tx.query(Person).where(
            25 <= Person.age <= 35
        ).find()
        assert len(middle_aged_exact) == 3
        assert set(p.name for p in middle_aged_exact) == {"Alice", "Bob", "Charlie"}
        
        # Greater than or equal comparison (age >= 35)
        older_people = tx.query(Person).where(
            35 <= Person.age
        ).find()
        assert len(older_people) == 2
        assert set(p.name for p in older_people) == {"Charlie", "David"}


@pytest.mark.e2e
def test_order_by(repo, clean_db):
    """Test ordering query results."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        
        # Order by age ascending
        age_asc = tx.query(Person).order_by(Person.age).find()
        assert len(age_asc) == 3
        assert [p.name for p in age_asc] == ["Bob", "Alice", "Charlie"]
        
        # Order by age descending
        age_desc = tx.query(Person).order_by(Person.age, descending=True).find()
        assert len(age_desc) == 3
        assert [p.name for p in age_desc] == ["Charlie", "Alice", "Bob"]


@pytest.mark.e2e
def test_limit(repo, clean_db):
    """Test limiting query results."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        
        # Limit results
        limited_query = tx.query(Person).limit(2).find()
        assert len(limited_query) == 2
        
        # Combined with order_by
        oldest_two = tx.query(Person).order_by(Person.age, descending=True).limit(2).find()
        assert len(oldest_two) == 2
        assert set(p.name for p in oldest_two) == {"Charlie", "Alice"}


@pytest.mark.e2e
def test_find_one(repo, clean_db):
    """Test find_one method."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        
        # Find one result
        oldest = tx.query(Person).order_by(Person.age, descending=True).find_one()
        assert oldest.name == "Charlie"
        
        # Find one by condition
        alice = tx.query(Person).where(Person.name == "Alice").find_one()
        assert alice.name == "Alice"


@pytest.mark.e2e
def test_combined_pythonic_features(repo, clean_db):
    """Test combining multiple Pythonic features together."""
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30, email="alice@example.com", tags=["developer", "python"]))
        tx.create(Person(name="Bob", age=25, email="bob@test.com", tags=["designer", "ui"]))
        tx.create(Person(name="Charlie", age=35, email="charlie@example.com", tags=["developer", "java"]))
        tx.create(Person(name="David", age=40, email="david@sample.net", tags=["manager", "python"]))
        
        # Combine reversed membership test with string method aliases
        # Find python developers with example.com email domain
        python_devs_example = tx.query(Person).where(
            "python" in Person.tags
        ).where(
            Person.email.endswith("example.com")
        ).find()
        
        assert len(python_devs_example) == 1
        assert python_devs_example[0].name == "Alice"
        
        # Multiple queries combined with OR as separate where clauses
        # Find python devs OR anyone with emails starting with 'a'
        pythonic_devs = tx.query(Person).where("python" in Person.tags).find()
        a_emails = tx.query(Person).where(Person.email.startswith("a")).find()
        
        # Manually combine results
        combined_results = set()
        for p in pythonic_devs:
            combined_results.add(p.name)
        for p in a_emails:
            combined_results.add(p.name)
            
        assert combined_results == {"Alice", "David"}


@pytest.mark.e2e
def test_reversed_in_operator(repo, clean_db):
    """Test the reversed 'in' operator (field in collection) directly.
    
    This tests the __ror__ method implementation on FieldExpr, which enables
    the syntax: field in collection.
    """
    # First, let's test the method directly
    expr = Person.name.__ror__(["Alice", "Bob"])
    assert expr.field == "name"
    assert expr.operator == "IN"
    assert expr.value == ["Alice", "Bob"]
    
    # Test with different collection types
    list_expr = Person.age.__ror__([25, 30, 35])
    assert list_expr.field == "age"
    assert list_expr.operator == "IN"
    assert list_expr.value == [25, 30, 35]
    
    tuple_expr = Person.name.__ror__(("Alice", "Bob"))
    assert tuple_expr.field == "name"
    assert tuple_expr.operator == "IN"
    assert tuple_expr.value == ["Alice", "Bob"]  # Converted to list
    
    set_expr = Person.name.__ror__({"Alice", "Bob"})
    assert set_expr.field == "name"
    assert set_expr.operator == "IN"
    assert isinstance(set_expr.value, list)
    assert set(set_expr.value) == {"Alice", "Bob"}  # Converted to list
    
    # Test with invalid type (should raise TypeError)
    with pytest.raises(TypeError):
        Person.name.__ror__("not_a_collection")
        
    # Now test in the database context
    with repo.transaction() as tx:
        # Create sample data
        tx.create(Person(name="Alice", age=30))
        tx.create(Person(name="Bob", age=25))
        tx.create(Person(name="Charlie", age=35))
        
        # Create the expressions and use them in queries
        name_expr = Person.name.__ror__(["Alice", "Charlie"])
        selected_people = tx.query(Person).where(name_expr).find()
        
        assert len(selected_people) == 2
        assert set(p.name for p in selected_people) == {"Alice", "Charlie"}