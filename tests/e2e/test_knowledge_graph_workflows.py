"""End-to-end tests for knowledge graph construction workflows.

These tests verify realistic knowledge graph building scenarios including
entity linking, hierarchical relationships, and complex graph traversals.
"""
import pytest
from .shared_models import (
    Person, Company, Product, Project, Department,
    WorksAt, Uses, PartOf, ManufacturedBy, Collaborates, 
    Reports, Manages, WorksOn
)


@pytest.mark.e2e
class TestKnowledgeGraphWorkflows:
    """Test knowledge graph construction and traversal workflows."""

    def test_organizational_hierarchy_construction(self, repo):
        """Test building and querying organizational hierarchy."""
        with repo.transaction() as tx:
            # Create organizational structure
            
            # Top-level company
            company = tx.create(Company(
                name="GlobalTech Corp",
                founded=2010,
                industry="Technology",
                employee_count=500,
                revenue=100000000.0
            ))
            
            # Department hierarchy
            engineering = tx.create(Department(
                name="Engineering",
                budget=5000000.0,
                head_count=150,
                location="San Francisco"
            ))
            
            frontend_team = tx.create(Department(
                name="Frontend Engineering", 
                budget=1500000.0,
                head_count=45,
                location="San Francisco"
            ))
            
            backend_team = tx.create(Department(
                name="Backend Engineering",
                budget=2000000.0,
                head_count=60,
                location="San Francisco"
            ))
            
            ai_team = tx.create(Department(
                name="AI/ML Engineering",
                budget=1500000.0,
                head_count=45,
                location="San Francisco"
            ))
            
            # Create hierarchical relationships
            tx.relate(frontend_team, PartOf(since=2015, responsibility="Web Applications"), engineering)
            tx.relate(backend_team, PartOf(since=2012, responsibility="Infrastructure"), engineering)
            tx.relate(ai_team, PartOf(since=2018, responsibility="Machine Learning"), engineering)
            
            # Create people in hierarchy
            cto = tx.create(Person(
                email="cto@globaltech.com",
                name="Sarah Chen",
                age=45,
                department="Engineering",
                tags=["leadership", "technology", "strategy"],
                score=98.0
            ))
            
            frontend_lead = tx.create(Person(
                email="frontend.lead@globaltech.com", 
                name="Mike Johnson",
                age=35,
                department="Frontend Engineering",
                tags=["react", "typescript", "architecture"],
                score=92.0
            ))
            
            backend_lead = tx.create(Person(
                email="backend.lead@globaltech.com",
                name="Anna Rodriguez",
                age=38,
                department="Backend Engineering", 
                tags=["python", "microservices", "databases"],
                score=94.0
            ))
            
            ai_lead = tx.create(Person(
                email="ai.lead@globaltech.com",
                name="David Kim",
                age=40,
                department="AI/ML Engineering",
                tags=["machine-learning", "python", "research"],
                score=96.0
            ))
            
            # Create management relationships
            tx.relate(cto, Manages(since=2015, budget_authority=5000000.0, team_size=150), engineering)
            tx.relate(frontend_lead, Manages(since=2018, budget_authority=1500000.0, team_size=45), frontend_team)
            tx.relate(backend_lead, Manages(since=2016, budget_authority=2000000.0, team_size=60), backend_team)
            tx.relate(ai_lead, Manages(since=2019, budget_authority=1500000.0, team_size=45), ai_team)
            
            # Create reporting relationships
            tx.relate(frontend_lead, Reports(since=2018, review_cycle="quarterly"), cto)
            tx.relate(backend_lead, Reports(since=2016, review_cycle="quarterly"), cto)
            tx.relate(ai_lead, Reports(since=2019, review_cycle="quarterly"), cto)
            
            # Add team members
            team_members = []
            for i in range(12):
                if i < 4:  # Frontend team
                    dept = "Frontend Engineering"
                    tags = ["react", "javascript", "css"]
                    lead = frontend_lead
                elif i < 8:  # Backend team
                    dept = "Backend Engineering"
                    tags = ["python", "apis", "databases"]
                    lead = backend_lead
                else:  # AI team
                    dept = "AI/ML Engineering" 
                    tags = ["python", "tensorflow", "data-science"]
                    lead = ai_lead
                
                member = tx.create(Person(
                    email=f"engineer{i:02d}@globaltech.com",
                    name=f"Engineer {i:02d}",
                    age=25 + (i % 15),
                    department=dept,
                    tags=tags + ["engineer"],
                    score=80.0 + (i % 15)
                ))
                team_members.append(member)
                
                # Create employment and reporting
                tx.relate(member, WorksAt(
                    role="Software Engineer",
                    since=2020 + (i % 4),
                    salary=90000 + (i * 5000)
                ), company)
                
                tx.relate(member, Reports(since=2020 + (i % 4), review_cycle="quarterly"), lead)
        
        # Test hierarchical queries
        with repo.transaction() as tx:
            # Find all department heads
            managers = tx.query(Person).where(
                "leadership" in Person.tags
            ).find()
            assert len(managers) >= 1
            
            # Find all engineers
            engineers = tx.query(Person).where(
                "engineer" in Person.tags
            ).find()
            assert len(engineers) >= 10
            
            # Find AI specialists
            ai_specialists = tx.query(Person).where(
                Person.department == "AI/ML Engineering"
            ).find()
            assert len(ai_specialists) >= 4

    def test_product_ecosystem_knowledge_graph(self, repo):
        """Test building product ecosystem with complex relationships."""
        with repo.transaction() as tx:
            # Create companies in ecosystem
            tech_corp = tx.create(Company(
                name="TechCorp",
                founded=2015,
                industry="Technology",
                employee_count=200
            ))
            
            hardware_inc = tx.create(Company(
                name="Hardware Inc",
                founded=2008,
                industry="Manufacturing",
                employee_count=500
            ))
            
            software_solutions = tx.create(Company(
                name="Software Solutions",
                founded=2012,
                industry="Software",
                employee_count=150
            ))
            
            # Create products with complex relationships
            smartphone = tx.create(Product(
                sku="SMART-001",
                name="TechPhone Pro",
                price=999.99,
                category="Consumer Electronics",
                description="Premium smartphone",
                manufacturer="Hardware Inc"
            ))
            
            os_platform = tx.create(Product(
                sku="OS-PLAT-002",
                name="TechOS Mobile",
                price=0.0,  # Free OS
                category="Operating System",
                description="Mobile operating system",
                manufacturer="TechCorp"
            ))
            
            dev_toolkit = tx.create(Product(
                sku="DEV-KIT-003",
                name="TechOS SDK",
                price=299.99,
                category="Development Tools", 
                description="Development kit for TechOS",
                manufacturer="Software Solutions"
            ))
            
            analytics_app = tx.create(Product(
                sku="ANALYTICS-004",
                name="Business Analytics Suite",
                price=199.99,
                category="Business Software",
                description="Enterprise analytics platform"
            ))
            
            # Create manufacturing relationships
            tx.relate(smartphone, ManufacturedBy(
                since=2020,
                contract_type="exclusive",
                quality_rating=4.8
            ), hardware_inc)
            
            tx.relate(os_platform, ManufacturedBy(
                since=2015,
                contract_type="internal",
                quality_rating=4.9
            ), tech_corp)
            
            tx.relate(dev_toolkit, ManufacturedBy(
                since=2018,
                contract_type="partnership",
                quality_rating=4.7
            ), software_solutions)
            
            # Create collaboration relationships
            tx.relate(tech_corp, Collaborates(
                since=2020,
                contract_value=50000000.0,
                project_count=3
            ), hardware_inc)
            
            tx.relate(tech_corp, Collaborates(
                since=2018,
                contract_value=25000000.0,
                project_count=2
            ), software_solutions)
            
            # Create user ecosystem
            developers = []
            for i in range(8):
                dev = tx.create(Person(
                    email=f"dev{i:02d}@company.com",
                    name=f"Developer {i:02d}",
                    age=25 + (i % 20),
                    tags=["developer", "mobile", "techOS"],
                    score=85.0 + (i % 10)
                ))
                developers.append(dev)
                
                # Developers use SDK
                tx.relate(dev, Uses(
                    since=2021,
                    frequency="daily",
                    license_type="professional"
                ), dev_toolkit)
                
                # Some developers also use analytics
                if i % 3 == 0:
                    tx.relate(dev, Uses(
                        since=2022,
                        frequency="weekly",
                        license_type="enterprise"
                    ), analytics_app)
            
            # Create enterprise customers
            enterprise_users = []
            for i in range(5):
                user = tx.create(Person(
                    email=f"enterprise{i:02d}@bigcorp.com",
                    name=f"Enterprise User {i:02d}",
                    age=35 + (i % 15),
                    tags=["business", "analytics", "enterprise"],
                    score=90.0 + i
                ))
                enterprise_users.append(user)
                
                # Enterprise users primarily use analytics
                tx.relate(user, Uses(
                    since=2021,
                    frequency="daily",
                    license_type="enterprise"
                ), analytics_app)
        
        # Test ecosystem queries
        with repo.transaction() as tx:
            # Find products by category
            dev_tools = tx.query(Product).where(
                Product.category == "Development Tools"
            ).find()
            assert len(dev_tools) >= 1
            
            # Find enterprise software users
            enterprise_users = tx.query(Person).where(
                "enterprise" in Person.tags
            ).find()
            assert len(enterprise_users) >= 3
            
            # Find companies in ecosystem
            tech_companies = tx.query(Company).where(
                Company.industry == "Technology"
            ).find()
            assert len(tech_companies) >= 1

    def test_research_collaboration_network(self, repo):
        """Test academic/research collaboration knowledge graph."""
        with repo.transaction() as tx:
            # Create research institutions
            university = tx.create(Company(
                name="Tech University",
                founded=1995,
                industry="Education",
                employee_count=1000
            ))
            
            research_lab = tx.create(Company(
                name="AI Research Labs",
                founded=2018,
                industry="Research",
                employee_count=50
            ))
            
            # Create research projects
            ai_project = tx.create(Project(
                code="AI-NLP-2024",
                name="Natural Language Processing Research",
                status="active",
                budget=2000000.0,
                priority=1
            ))
            
            robotics_project = tx.create(Project(
                code="ROBOT-VIS-2024", 
                name="Computer Vision for Robotics",
                status="active",
                budget=1500000.0,
                priority=2
            ))
            
            quantum_project = tx.create(Project(
                code="QUANTUM-2024",
                name="Quantum Computing Applications",
                status="planning",
                budget=3000000.0,
                priority=1
            ))
            
            # Create researchers
            principal_investigator = tx.create(Person(
                email="pi@techuniversity.edu",
                name="Dr. Elena Vasquez",
                age=50,
                tags=["researcher", "ai", "nlp", "leadership"],
                score=98.0
            ))
            
            senior_researcher = tx.create(Person(
                email="senior@airesearch.org",
                name="Dr. James Liu",
                age=42,
                tags=["researcher", "computer-vision", "robotics"],
                score=95.0
            ))
            
            # Create research team
            researchers = []
            for i in range(6):
                specialties = [
                    ["nlp", "transformers", "python"],
                    ["computer-vision", "pytorch", "opencv"],
                    ["quantum", "qiskit", "mathematics"],
                    ["robotics", "ros", "control-systems"],
                    ["machine-learning", "tensorflow", "statistics"],
                    ["data-science", "pandas", "visualization"]
                ]
                
                researcher = tx.create(Person(
                    email=f"researcher{i:02d}@techuniversity.edu",
                    name=f"Dr. Researcher {i:02d}",
                    age=28 + (i * 3),
                    tags=["researcher"] + specialties[i],
                    score=85.0 + (i * 2)
                ))
                researchers.append(researcher)
                
                # Assign to institutions
                institution = university if i < 4 else research_lab
                tx.relate(researcher, WorksAt(
                    role="Research Scientist",
                    since=2019 + (i % 5),
                    salary=95000 + (i * 10000)
                ), institution)
                
                # Assign to projects based on specialty
                if "nlp" in specialties[i] or "transformers" in specialties[i]:
                    tx.relate(researcher, WorksOn(
                        role="Lead Researcher" if i == 0 else "Researcher",
                        allocation=0.8,
                        start_date="2024-01-01"
                    ), ai_project)
                
                if "computer-vision" in specialties[i] or "robotics" in specialties[i]:
                    tx.relate(researcher, WorksOn(
                        role="Researcher",
                        allocation=0.6,
                        start_date="2024-02-01"
                    ), robotics_project)
                
                if "quantum" in specialties[i]:
                    tx.relate(researcher, WorksOn(
                        role="Researcher",
                        allocation=0.9,
                        start_date="2024-06-01"
                    ), quantum_project)
            
            # Create institutional collaborations
            tx.relate(university, Collaborates(
                since=2022,
                contract_value=5000000.0,
                project_count=3
            ), research_lab)
        
        # Test research network queries
        with repo.transaction() as tx:
            # Find AI researchers
            ai_researchers = tx.query(Person).where(
                "ai" in Person.tags
            ).find()
            assert len(ai_researchers) >= 1
            
            # Find active projects
            active_projects = tx.query(Project).where(
                Project.status == "active"
            ).find()
            assert len(active_projects) >= 2
            
            # Find high-budget projects
            major_projects = tx.query(Project).where(
                Project.budget > 1000000.0
            ).find()
            assert len(major_projects) >= 2
            
            # Find cross-institutional researchers
            all_researchers = tx.query(Person).where(
                "researcher" in Person.tags
            ).find()
            assert len(all_researchers) >= 6

    def test_supply_chain_knowledge_graph(self, repo):
        """Test complex supply chain relationship modeling."""
        with repo.transaction() as tx:
            # Create supply chain entities
            manufacturer = tx.create(Company(
                name="Global Manufacturing",
                founded=2000,
                industry="Manufacturing",
                employee_count=2000
            ))
            
            supplier_a = tx.create(Company(
                name="Component Supplier A",
                founded=1995,
                industry="Components",
                employee_count=500
            ))
            
            supplier_b = tx.create(Company(
                name="Raw Materials Co",
                founded=1985,
                industry="Raw Materials",
                employee_count=800
            ))
            
            distributor = tx.create(Company(
                name="Global Distribution",
                founded=2005,
                industry="Logistics",
                employee_count=1200
            ))
            
            # Create products at different supply chain levels
            raw_material = tx.create(Product(
                sku="RAW-STEEL-001",
                name="High Grade Steel",
                price=2.50,  # per kg
                category="Raw Materials"
            ))
            
            component = tx.create(Product(
                sku="COMP-ENGINE-002",
                name="Engine Component",
                price=450.00,
                category="Components"
            ))
            
            final_product = tx.create(Product(
                sku="FINAL-CAR-003",
                name="Electric Vehicle",
                price=35000.00,
                category="Vehicles"
            ))
            
            # Create supply chain relationships
            tx.relate(raw_material, ManufacturedBy(
                since=2018,
                contract_type="long-term",
                quality_rating=4.9
            ), supplier_b)
            
            tx.relate(component, ManufacturedBy(
                since=2019,
                contract_type="exclusive",
                quality_rating=4.7
            ), supplier_a)
            
            tx.relate(final_product, ManufacturedBy(
                since=2020,
                contract_type="internal",
                quality_rating=4.8
            ), manufacturer)
            
            # Create collaboration relationships for supply chain
            tx.relate(manufacturer, Collaborates(
                since=2018,
                contract_value=100000000.0,
                project_count=5
            ), supplier_a)
            
            tx.relate(manufacturer, Collaborates(
                since=2017,
                contract_value=75000000.0,
                project_count=3
            ), supplier_b)
            
            tx.relate(manufacturer, Collaborates(
                since=2020,
                contract_value=200000000.0,
                project_count=8
            ), distributor)
        
        # Test supply chain queries
        with repo.transaction() as tx:
            # Find raw materials
            raw_materials = tx.query(Product).where(
                Product.category == "Raw Materials"
            ).find()
            assert len(raw_materials) >= 1
            
            # Find high-value collaborations
            major_partnerships = tx.query(Company).where(
                Company.industry == "Manufacturing"
            ).find()
            assert len(major_partnerships) >= 1
            
            # Find suppliers
            suppliers = tx.query(Company).where(
                Company.name.starts_with("Component") | Company.name.starts_with("Raw")
            ).find()
            assert len(suppliers) >= 2