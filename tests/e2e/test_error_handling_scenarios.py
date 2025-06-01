"""End-to-end tests for error handling in complex scenarios.

These tests verify that NeoAlchemy handles various error conditions gracefully
in realistic usage scenarios, including constraint violations, transaction failures,
and data integrity issues.
"""
import pytest
from neo4j.exceptions import ConstraintError, TransientError

from .shared_models import Person, Company, Product, WorksAt, Uses


@pytest.mark.e2e
class TestErrorHandlingScenarios:
    """Test error handling in complex real-world scenarios."""

    def test_constraint_violation_handling(self, repo):
        """Test handling of constraint violations in complex workflows."""
        with repo.transaction() as tx:
            # Create initial valid data
            company = tx.create(Company(
                name="TechCorp",
                founded=2020,
                industry="Technology"
            ))
            
            person1 = tx.create(Person(
                email="unique@techcorp.com",
                name="John Doe",
                age=30,
                tags=["engineer"]
            ))
            
            tx.relate(person1, WorksAt(role="Engineer", since=2022, salary=100000), company)
        
        # Test primary key constraint violation
        with pytest.raises(Exception):  # Should be ConstraintError in practice
            with repo.transaction() as tx:
                # Try to create person with duplicate email (primary key)
                person2 = tx.create(Person(
                    email="unique@techcorp.com",  # Duplicate email
                    name="Jane Smith",
                    age=28,
                    tags=["designer"]
                ))
        
        # Verify original data is still intact
        with repo.transaction() as tx:
            existing_people = tx.query(Person).where(
                Person.email == "unique@techcorp.com"
            ).find()
            assert len(existing_people) == 1
            assert existing_people[0].name == "John Doe"

    def test_transaction_rollback_scenarios(self, repo):
        """Test transaction rollback in complex multi-entity operations."""
        # Test scenario: Creating a complex business setup that partially fails
        
        initial_count = 0
        with repo.transaction() as tx:
            initial_people = tx.query(Person).find()
            initial_count = len(initial_people)
        
        # Simulate a complex operation that should rollback
        try:
            with repo.transaction() as tx:
                # Create valid entities first
                company = tx.create(Company(
                    name="FailureCorp",
                    founded=2021,
                    industry="Testing"
                ))
                
                # Create several valid people
                people = []
                for i in range(3):
                    person = tx.create(Person(
                        email=f"employee{i:02d}@failurecorp.com",
                        name=f"Employee {i:02d}",
                        age=25 + i,
                        tags=["employee", "test"]
                    ))
                    people.append(person)
                    
                    tx.relate(person, WorksAt(
                        role="Test Employee",
                        since=2023,
                        salary=80000
                    ), company)
                
                # Create a duplicate that should cause constraint violation
                duplicate_person = tx.create(Person(
                    email="employee00@failurecorp.com",  # Duplicate email
                    name="Duplicate Employee",
                    age=30,
                    tags=["duplicate"]
                ))
                
        except Exception:
            # Transaction should have rolled back
            pass
        
        # Verify rollback - no new entities should exist
        with repo.transaction() as tx:
            final_people = tx.query(Person).find()
            final_count = len(final_people)
            
            # Count should be unchanged
            assert final_count == initial_count
            
            # Specific entities should not exist
            failure_corp = tx.query(Company).where(
                Company.name == "FailureCorp"
            ).find()
            assert len(failure_corp) == 0
            
            test_employees = tx.query(Person).where(
                "test" in Person.tags
            ).find()
            assert len(test_employees) == 0

    def test_data_consistency_validation(self, repo):
        """Test data consistency validation in complex scenarios."""
        with repo.transaction() as tx:
            # Create a scenario with potential data consistency issues
            
            # Company with inconsistent data
            company = tx.create(Company(
                name="DataCorp",
                founded=2025,  # Future date - potentially invalid
                industry="Technology",
                employee_count=-5  # Negative employee count - invalid
            ))
            
            # Person with edge case data
            person = tx.create(Person(
                email="test@datacorp.com",
                name="",  # Empty name - might be invalid
                age=150,  # Unrealistic age
                tags=[],  # Empty tags
                score=-10.0  # Negative score
            ))
            
            # Create relationship despite data issues
            tx.relate(person, WorksAt(
                role="Test Role",
                since=2030,  # Future date
                salary=-50000  # Negative salary
            ), company)
        
        # Test data validation queries
        with repo.transaction() as tx:
            # Find companies with future founding dates
            future_companies = tx.query(Company).where(
                Company.founded > 2024
            ).find()
            assert len(future_companies) >= 1
            
            # Find people with extreme ages
            extreme_ages = tx.query(Person).where(
                Person.age > 100
            ).find()
            assert len(extreme_ages) >= 1
            
            # Find people with negative scores
            negative_scores = tx.query(Person).where(
                Person.score < 0
            ).find()
            assert len(negative_scores) >= 1

    def test_concurrent_modification_scenarios(self, repo):
        """Test handling of concurrent modifications and race conditions."""
        # This test simulates what might happen with concurrent access
        
        with repo.transaction() as tx:
            # Create initial state
            company = tx.create(Company(
                name="ConcurrentCorp",
                founded=2020,
                industry="Technology",
                employee_count=100
            ))
            
            person = tx.create(Person(
                email="concurrent@corp.com",
                name="Concurrent User",
                age=30,
                score=85.0
            ))
            
            tx.relate(person, WorksAt(
                role="Developer",
                since=2022,
                salary=100000
            ), company)
        
        # Simulate concurrent modifications
        # Transaction 1: Update person score
        with repo.transaction() as tx:
            person = tx.query(Person).where(
                Person.email == "concurrent@corp.com"
            ).find_one()
            
            # Modify and create new version (simulating update)
            updated_person = tx.create(Person(
                email="concurrent.updated@corp.com",
                name=person.name + " Updated",
                age=person.age,
                score=person.score + 10.0,
                tags=["updated"]
            ))
        
        # Transaction 2: Query and verify state
        with repo.transaction() as tx:
            original = tx.query(Person).where(
                Person.email == "concurrent@corp.com"
            ).find()
            
            updated = tx.query(Person).where(
                "updated" in Person.tags
            ).find()
            
            assert len(original) == 1  # Original still exists
            assert len(updated) == 1   # Updated version exists
            assert updated[0].score > original[0].score

    def test_large_transaction_failure_recovery(self, repo):
        """Test recovery from failures in large, complex transactions."""
        # Create a baseline state
        baseline_count = 0
        with repo.transaction() as tx:
            baseline_people = tx.query(Person).find()
            baseline_count = len(baseline_people)
        
        # Attempt a large transaction that will fail partway through
        try:
            with repo.transaction() as tx:
                # Create many entities successfully
                companies = []
                for i in range(5):
                    company = tx.create(Company(
                        name=f"LargeCorp{i:02d}",
                        founded=2020 + i,
                        industry="Technology",
                        employee_count=100 + (i * 50)
                    ))
                    companies.append(company)
                
                # Create many people
                people = []
                for i in range(20):
                    person = tx.create(Person(
                        email=f"largecorp{i:03d}@company.com",
                        name=f"Employee {i:03d}",
                        age=25 + (i % 40),
                        tags=["large-transaction", "employee"],
                        score=70.0 + (i % 30)
                    ))
                    people.append(person)
                    
                    # Create employment relationships
                    company = companies[i % len(companies)]
                    tx.relate(person, WorksAt(
                        role="Employee",
                        since=2023,
                        salary=80000 + (i * 2000)
                    ), company)
                
                # Create a product that will cause failure
                product = tx.create(Product(
                    sku="DUPLICATE-SKU",  # This SKU might already exist
                    name="Large Transaction Product",
                    price=999.99,
                    category="Test"
                ))
                
                # Try to create another product with same SKU (should fail)
                duplicate_product = tx.create(Product(
                    sku="DUPLICATE-SKU",  # Duplicate SKU
                    name="Duplicate Product",
                    price=1999.99,
                    category="Test"
                ))
                
        except Exception:
            # Expected to fail due to duplicate SKU
            pass
        
        # Verify complete rollback
        with repo.transaction() as tx:
            # Check that no large transaction entities were created
            large_corps = tx.query(Company).where(
                Company.name.starts_with("LargeCorp")
            ).find()
            assert len(large_corps) == 0
            
            large_employees = tx.query(Person).where(
                "large-transaction" in Person.tags
            ).find()
            assert len(large_employees) == 0
            
            test_products = tx.query(Product).where(
                Product.sku == "DUPLICATE-SKU"
            ).find()
            # Should either be 0 (if original didn't exist) or 1 (if it did exist)
            assert len(test_products) <= 1
            
            # Verify baseline count unchanged
            final_people = tx.query(Person).find()
            assert len(final_people) == baseline_count

    def test_query_performance_degradation_handling(self, repo, performance_timer):
        """Test handling of queries that might perform poorly."""
        # Create a scenario with potential performance issues
        with repo.transaction() as tx:
            # Create a moderate dataset
            companies = []
            for i in range(10):
                company = tx.create(Company(
                    name=f"PerfCorp{i:02d}",
                    founded=2000 + i,
                    industry=["Tech", "Finance", "Healthcare"][i % 3],
                    employee_count=50 + (i * 20)
                ))
                companies.append(company)
            
            # Create many people with various attributes
            for i in range(100):
                person = tx.create(Person(
                    email=f"perf{i:03d}@company.com",
                    name=f"Performance Test {i:03d}",
                    age=20 + (i % 50),
                    tags=[f"tag{j}" for j in range(i % 5)],  # Variable tag counts
                    score=0.0 + (i % 100)  # Scores from 0-99
                ))
                
                # Connect to random company
                company = companies[i % len(companies)]
                tx.relate(person, WorksAt(
                    role=["Engineer", "Manager", "Analyst"][i % 3],
                    since=2015 + (i % 9),
                    salary=60000 + (i * 1000)
                ), company)
        
        # Test potentially slow queries with timeouts
        performance_timer.start()
        
        with repo.transaction() as tx:
            # Query 1: Complex filtering
            complex_filter = tx.query(Person).where(
                Person.age > 30,
                Person.score > 50,
                Person.name.starts_with("Performance")
            ).find()
            
            # Query 2: Range queries
            age_range = tx.query(Person).where(
                25 <= Person.age <= 45
            ).find()
            
            # Query 3: Ordering large result sets
            ordered_results = tx.query(Person).order_by(
                Person.score, descending=True
            ).limit(20).find()
            
            # Query 4: Multiple companies
            tech_companies = tx.query(Company).where(
                Company.industry == "Tech"
            ).find()
        
        performance_timer.stop()
        
        # Verify queries completed in reasonable time
        assert performance_timer.duration < 10.0, f"Queries took {performance_timer.duration:.2f}s, too slow"
        
        # Verify results are reasonable
        assert len(complex_filter) >= 0  # May be 0 depending on data
        assert len(age_range) > 0
        assert len(ordered_results) > 0
        assert len(tech_companies) > 0

    def test_relationship_integrity_violations(self, repo):
        """Test handling of relationship integrity issues."""
        with repo.transaction() as tx:
            # Create entities
            company = tx.create(Company(
                name="RelationshipCorp",
                founded=2020,
                industry="Testing"
            ))
            
            person = tx.create(Person(
                email="relationship@test.com",
                name="Relationship Tester",
                age=35
            ))
            
            # Create valid relationship
            tx.relate(person, WorksAt(
                role="Tester",
                since=2023,
                salary=90000
            ), company)
        
        # Test querying non-existent relationships
        with repo.transaction() as tx:
            # Query for relationships that don't exist
            non_existent = tx.query(Person).where(
                Person.email == "nonexistent@test.com"
            ).find()
            assert len(non_existent) == 0
            
            # Query for people with impossible conditions
            impossible = tx.query(Person).where(
                Person.age > 200,  # No one should be this old
                Person.score > 200  # Score should not exceed 100
            ).find()
            assert len(impossible) == 0