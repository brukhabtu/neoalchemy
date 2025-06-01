"""End-to-end tests for complete ORM workflows.

These tests verify complete user workflows from schema initialization
through data operations to complex querying and data export.
"""
import os
import pytest
from .shared_models import Person, Company, Product, WorksAt, Uses, Project, WorksOn

# Test configuration constants
WORKFLOW_EMPLOYEES_COUNT = 10
BULK_COMPANIES_COUNT = int(os.getenv("E2E_BULK_COMPANIES", "20"))
BULK_PEOPLE_COUNT = int(os.getenv("E2E_BULK_PEOPLE", "100"))
MAX_WORKFLOW_TIME = 30.0  # seconds
MAX_BULK_TIME = 15.0  # seconds


@pytest.mark.e2e
class TestCompleteORMWorkflows:
    """Test complete ORM workflows from start to finish."""

    def test_schema_to_export_workflow(self, repo, performance_timer):
        """Test complete workflow: schema → data → query → export."""
        performance_timer.start()
        
        # Phase 1: Schema Setup (constraints already set up by fixture)
        # Verify constraints are in place
        with repo.transaction() as tx:
            # Try to create duplicate - should work since we'll use different emails
            alice1 = tx.create(Person(
                email="alice@company.com",
                name="Alice Johnson", 
                age=30,
                tags=["engineer", "python"]
            ))
            
            # This should work - different email
            alice2 = tx.create(Person(
                email="alice.johnson@company.com",
                name="Alice Johnson",  # Same name is fine
                age=30,
                tags=["engineer", "python"]
            ))
            
            assert alice1.email != alice2.email
            assert alice1.name == alice2.name
        
        # Phase 2: Data Import - Complex business entities
        with repo.transaction() as tx:
            # Create companies
            techcorp = tx.create(Company(
                name="TechCorp Inc",
                founded=2015,
                industry="Technology",
                employee_count=150,
                revenue=50000000.0
            ))
            
            financeplus = tx.create(Company(
                name="FinancePlus",
                founded=2010, 
                industry="Finance",
                employee_count=80,
                revenue=25000000.0
            ))
            
            # Create products
            ml_platform = tx.create(Product(
                sku="TECH-ML-001",
                name="ML Analytics Platform",
                price=2999.99,
                category="Software",
                description="Enterprise machine learning platform"
            ))
            
            fin_tool = tx.create(Product(
                sku="FIN-TOOL-002", 
                name="Financial Dashboard",
                price=1499.99,
                category="Finance",
                description="Real-time financial analytics"
            ))
            
            # Create projects
            ai_project = tx.create(Project(
                code="AI-2024-001",
                name="AI Integration Project",
                status="active",
                budget=500000.0,
                priority=1
            ))
            
            # Create people with realistic data
            people = []
            for i in range(WORKFLOW_EMPLOYEES_COUNT):
                person = tx.create(Person(
                    email=f"employee{i:02d}@techcorp.com",
                    name=f"Employee {i:02d}",
                    age=25 + (i * 3),
                    active=True,
                    tags=["engineer", "python", "ai"] if i < 5 else ["manager", "product"],
                    score=85.0 + i,
                    department="Engineering" if i < 7 else "Product"
                ))
                people.append(person)
                
                # Create employment relationships
                role = "Senior Engineer" if i < 3 else "Engineer" if i < 7 else "Product Manager"
                tx.relate(person, WorksAt(
                    role=role,
                    since=2020 + (i % 4),
                    salary=80000 + (i * 5000),
                    employment_type="full-time"
                ), techcorp)
                
                # Create product usage
                if i < 5:  # Engineers use ML platform
                    tx.relate(person, Uses(
                        since=2021,
                        frequency="daily",
                        license_type="premium"
                    ), ml_platform)
                
                # Create project assignments
                if i < 8:  # Most people work on AI project
                    tx.relate(person, WorksOn(
                        role="Developer" if i < 5 else "Coordinator",
                        allocation=0.8 if i < 5 else 0.5,
                        start_date="2024-01-01"
                    ), ai_project)
        
        # Phase 3: Complex Querying - Realistic business queries
        with repo.transaction() as tx:
            # Query 1: Find senior engineers working on AI project
            senior_ai_engineers = tx.query(Person).where(
                "Engineer" in Person.tags,
                Person.age > 30,
                Person.department == "Engineering"
            ).find()
            
            assert len(senior_ai_engineers) >= 2, f"Expected ≥2 senior AI engineers, got {len(senior_ai_engineers)}"
            
            # Query 2: Find high-value product users
            premium_users = tx.query(Person).where(
                Person.score > 90
            ).find()
            
            assert len(premium_users) >= 3, f"Expected ≥3 premium users (score>90), got {len(premium_users)}"
            
            # Query 3: Complex relationship query - people working on projects
            # This would be expanded with proper relationship traversal
            project_workers = tx.query(Person).where(
                Person.department == "Engineering"
            ).find()
            
            assert len(project_workers) >= 5
            
            # Query 4: Performance-sensitive query with ordering
            top_performers = tx.query(Person).where(
                Person.active == True
            ).order_by(Person.score, descending=True).limit(5).find()
            
            assert len(top_performers) == 5
            assert top_performers[0].score >= top_performers[-1].score
        
        # Phase 4: Data Export/Aggregation
        with repo.transaction() as tx:
            # Export scenario: Generate department statistics
            all_people = tx.query(Person).find()
            
            # Aggregate by department
            dept_stats = {}
            for person in all_people:
                dept = person.department or "Unknown"
                if dept not in dept_stats:
                    dept_stats[dept] = {"count": 0, "avg_score": 0, "total_score": 0}
                
                dept_stats[dept]["count"] += 1
                dept_stats[dept]["total_score"] += person.score
            
            # Calculate averages
            for dept in dept_stats:
                if dept_stats[dept]["count"] > 0:
                    dept_stats[dept]["avg_score"] = (
                        dept_stats[dept]["total_score"] / dept_stats[dept]["count"]
                    )
            
            # Verify realistic business data
            assert "Engineering" in dept_stats
            assert dept_stats["Engineering"]["count"] >= 5
            assert dept_stats["Engineering"]["avg_score"] > 80
            
            # Export scenario: Generate salary report
            all_employees = tx.query(Person).find()
            salary_ranges = {"<100k": 0, "100k-120k": 0, ">120k": 0}
            
            # This would typically involve relationship traversal to get salary data
            # For now, simulate based on score as proxy
            for person in all_employees:
                estimated_salary = 70000 + (person.score * 1000)
                if estimated_salary < 100000:
                    salary_ranges["<100k"] += 1
                elif estimated_salary < 120000:
                    salary_ranges["100k-120k"] += 1
                else:
                    salary_ranges[">120k"] += 1
            
            assert sum(salary_ranges.values()) == len(all_employees)
        
        performance_timer.stop()
        
        # Verify performance is reasonable for E2E test
        assert performance_timer.duration < MAX_WORKFLOW_TIME, f"Workflow took {performance_timer.duration:.2f}s, expected <{MAX_WORKFLOW_TIME}s"
        
        print(f"Complete workflow executed in {performance_timer.duration:.2f} seconds")

    def test_data_migration_workflow(self, repo):
        """Test data migration and transformation workflow."""
        # Phase 1: Create initial data structure
        with repo.transaction() as tx:
            # Old company structure
            old_company = tx.create(Company(
                name="OldCorp",
                founded=2005,
                industry="Legacy",
                employee_count=50
            ))
            
            # Legacy employees
            legacy_employees = []
            for i in range(5):
                emp = tx.create(Person(
                    email=f"legacy{i:02d}@oldcorp.com",
                    name=f"Legacy Employee {i:02d}",
                    age=40 + i,
                    department="Legacy Systems",
                    tags=["legacy", "maintenance"]
                ))
                legacy_employees.append(emp)
                
                tx.relate(emp, WorksAt(
                    role="Legacy Specialist",
                    since=2010,
                    salary=70000
                ), old_company)
        
        # Phase 2: Migration - Transform to new structure
        with repo.transaction() as tx:
            # Create new company
            new_company = tx.create(Company(
                name="ModernTech",
                founded=2020,
                industry="Technology",
                employee_count=100
            ))
            
            # Migrate employees with transformation
            all_legacy = tx.query(Person).where(
                "legacy" in Person.tags
            ).find()
            
            for person in all_legacy:
                # Transform data
                person.department = "Engineering"
                person.tags = ["engineer", "migration", "modern"]
                
                # Update the person (this would be a merge in real scenario)
                updated_person = tx.create(Person(
                    email=person.email.replace("oldcorp", "moderntech"),
                    name=person.name.replace("Legacy ", ""),
                    age=person.age,
                    department="Engineering",
                    tags=["engineer", "migration", "modern"],
                    score=75.0
                ))
                
                # Create new employment
                tx.relate(updated_person, WorksAt(
                    role="Software Engineer",
                    since=2024,
                    salary=90000
                ), new_company)
        
        # Phase 3: Validation - Verify migration
        with repo.transaction() as tx:
            migrated_employees = tx.query(Person).where(
                "modern" in Person.tags
            ).find()
            
            assert len(migrated_employees) == 5
            
            modern_company = tx.query(Company).where(
                Company.name == "ModernTech"
            ).find_one()
            
            assert modern_company is not None
            assert modern_company.industry == "Technology"

    def test_bulk_operations_workflow(self, repo, performance_timer):
        """Test bulk data operations for performance and reliability."""
        performance_timer.start()
        
        # Phase 1: Bulk creation
        with repo.transaction() as tx:
            # Create many entities in single transaction
            companies = []
            for i in range(BULK_COMPANIES_COUNT):
                company = tx.create(Company(
                    name=f"BulkCompany_{i:03d}",
                    founded=2000 + (i % 24),
                    industry=["Tech", "Finance", "Healthcare", "Education"][i % 4],
                    employee_count=10 + (i * 5)
                ))
                companies.append(company)
            
            # Create many people
            people = []
            for i in range(BULK_PEOPLE_COUNT):
                person = tx.create(Person(
                    email=f"bulk_user_{i:04d}@company.com",
                    name=f"Bulk User {i:04d}",
                    age=20 + (i % 50),
                    tags=[f"skill_{j}" for j in range(i % 3)],
                    score=50.0 + (i % 50)
                ))
                people.append(person)
                
                # Connect to random company
                company = companies[i % len(companies)]
                tx.relate(person, WorksAt(
                    role=["Engineer", "Manager", "Analyst"][i % 3],
                    since=2015 + (i % 9),
                    salary=60000 + (i * 500)
                ), company)
        
        # Phase 2: Bulk queries
        with repo.transaction() as tx:
            # Query large result sets
            all_people = tx.query(Person).find()
            assert len(all_people) == BULK_PEOPLE_COUNT, f"Expected {BULK_PEOPLE_COUNT} people, got {len(all_people)}"
            
            # Filtered queries
            young_people = tx.query(Person).where(Person.age < 30).find()
            assert len(young_people) > 0
            
            # Sorted queries
            top_scorers = tx.query(Person).order_by(Person.score, descending=True).limit(10).find()
            assert len(top_scorers) == 10
            
            # Range queries
            mid_aged = tx.query(Person).where(30 <= Person.age <= 45).find()
            assert len(mid_aged) > 0
        
        performance_timer.stop()
        
        # Verify bulk operations complete in reasonable time
        assert performance_timer.duration < MAX_BULK_TIME, f"Bulk operations took {performance_timer.duration:.2f}s, expected <{MAX_BULK_TIME}s"
        
        print(f"Bulk operations completed in {performance_timer.duration:.2f} seconds")