"""End-to-end tests for complex relationship traversal and graph queries.

These tests verify advanced graph traversal patterns, multi-hop relationships,
and complex query scenarios that demonstrate real-world graph database usage.
"""
import pytest
from .shared_models import (
    Person, Company, Product, Project, Department,
    WorksAt, Uses, PartOf, ManufacturedBy, Collaborates, 
    Reports, Manages, WorksOn
)


@pytest.mark.e2e
class TestComplexRelationshipTraversal:
    """Test complex graph traversal and relationship queries."""

    def test_multi_hop_relationship_queries(self, repo):
        """Test queries that traverse multiple relationship hops."""
        with repo.transaction() as tx:
            # Create a complex network for traversal testing
            
            # Companies
            parent_corp = tx.create(Company(
                name="Parent Corporation",
                founded=1990,
                industry="Conglomerate",
                employee_count=10000
            ))
            
            tech_subsidiary = tx.create(Company(
                name="Tech Subsidiary",
                founded=2000,
                industry="Technology", 
                employee_count=1000
            ))
            
            consulting_subsidiary = tx.create(Company(
                name="Consulting Subsidiary",
                founded=2005,
                industry="Consulting",
                employee_count=500
            ))
            
            client_company = tx.create(Company(
                name="Client Company",
                founded=2010,
                industry="Finance",
                employee_count=2000
            ))
            
            # Departments
            tech_engineering = tx.create(Department(
                name="Engineering",
                budget=5000000.0,
                head_count=200
            ))
            
            consulting_strategy = tx.create(Department(
                name="Strategy",
                budget=2000000.0,
                head_count=50
            ))
            
            # Projects
            digital_transformation = tx.create(Project(
                code="DT-2024-001",
                name="Digital Transformation Initiative",
                status="active",
                budget=10000000.0,
                priority=1
            ))
            
            ai_platform = tx.create(Project(
                code="AI-PLAT-2024",
                name="AI Platform Development",
                status="active",
                budget=5000000.0,
                priority=1
            ))
            
            # Products
            platform_software = tx.create(Product(
                sku="PLAT-SOFT-001",
                name="Enterprise Platform",
                price=50000.0,
                category="Enterprise Software"
            ))
            
            consulting_service = tx.create(Product(
                sku="CONSULT-001",
                name="Strategic Consulting",
                price=25000.0,
                category="Professional Services"
            ))
            
            # People with various roles
            ceo = tx.create(Person(
                email="ceo@parentcorp.com",
                name="CEO John Smith",
                age=55,
                tags=["executive", "leadership", "strategy"],
                score=99.0
            ))
            
            tech_cto = tx.create(Person(
                email="cto@techsub.com",
                name="CTO Sarah Johnson",
                age=45,
                tags=["technology", "leadership", "innovation"],
                score=95.0
            ))
            
            lead_engineer = tx.create(Person(
                email="lead.eng@techsub.com",
                name="Lead Engineer Mike Chen",
                age=35,
                tags=["engineering", "ai", "platform", "lead"],
                score=92.0
            ))
            
            consultant = tx.create(Person(
                email="consultant@consultingsub.com",
                name="Senior Consultant Lisa Brown",
                age=40,
                tags=["consulting", "strategy", "transformation", "lead"],
                score=90.0
            ))
            
            client_manager = tx.create(Person(
                email="pm@clientcompany.com",
                name="Project Manager Tom Wilson",
                age=38,
                tags=["project-management", "client", "coordination"],
                score=88.0
            ))
            
            # Create complex relationship network
            
            # Corporate structure
            tx.relate(tech_subsidiary, PartOf(since=2000, responsibility="Technology Solutions"), parent_corp)
            tx.relate(consulting_subsidiary, PartOf(since=2005, responsibility="Professional Services"), parent_corp)
            
            # Department relationships
            tx.relate(tech_engineering, PartOf(since=2000, responsibility="Product Development"), tech_subsidiary)
            tx.relate(consulting_strategy, PartOf(since=2005, responsibility="Client Strategy"), consulting_subsidiary)
            
            # Employment relationships
            tx.relate(ceo, WorksAt(role="Chief Executive Officer", since=1995, salary=500000), parent_corp)
            tx.relate(tech_cto, WorksAt(role="Chief Technology Officer", since=2010, salary=300000), tech_subsidiary)
            tx.relate(lead_engineer, WorksAt(role="Lead Engineer", since=2015, salary=150000), tech_subsidiary)
            tx.relate(consultant, WorksAt(role="Senior Consultant", since=2018, salary=120000), consulting_subsidiary)
            tx.relate(client_manager, WorksAt(role="Project Manager", since=2020, salary=100000), client_company)
            
            # Management relationships
            tx.relate(tech_cto, Manages(since=2010, budget_authority=5000000.0, team_size=200), tech_engineering)
            tx.relate(lead_engineer, Reports(since=2015, review_cycle="quarterly"), tech_cto)
            tx.relate(consultant, Reports(since=2018, review_cycle="monthly"), ceo)  # Direct report to CEO
            
            # Project assignments
            tx.relate(lead_engineer, WorksOn(role="Technical Lead", allocation=1.0, start_date="2024-01-01"), ai_platform)
            tx.relate(consultant, WorksOn(role="Strategy Lead", allocation=0.8, start_date="2024-01-01"), digital_transformation)
            tx.relate(client_manager, WorksOn(role="Client Lead", allocation=0.6, start_date="2024-02-01"), digital_transformation)
            
            # Product relationships
            tx.relate(platform_software, ManufacturedBy(since=2020, contract_type="internal", quality_rating=4.8), tech_subsidiary)
            tx.relate(consulting_service, ManufacturedBy(since=2005, contract_type="internal", quality_rating=4.9), consulting_subsidiary)
            
            # Business relationships
            tx.relate(consulting_subsidiary, Collaborates(since=2022, contract_value=15000000.0, project_count=3), client_company)
            tx.relate(tech_subsidiary, Collaborates(since=2023, contract_value=8000000.0, project_count=2), client_company)
            
            # Product usage
            tx.relate(client_manager, Uses(since=2023, frequency="daily", license_type="enterprise"), platform_software)
            tx.relate(client_company, Uses(since=2022, frequency="ongoing", license_type="enterprise"), consulting_service)
        
        # Test complex traversal queries
        with repo.transaction() as tx:
            # Query 1: Find all people working on projects for specific clients
            # This would involve: Person -> WorksOn -> Project -> (inferred client relationship)
            project_workers = tx.query(Person).where(
                "lead" in Person.tags  # Find leads
            ).find()
            
            transformation_workers = []
            for person in project_workers:
                if "strategy" in person.tags or "engineering" in person.tags:
                    transformation_workers.append(person)
            
            assert len(transformation_workers) >= 2
            
            # Query 2: Find products developed by subsidiaries of a parent company
            # This involves: Product -> ManufacturedBy -> Company -> PartOf -> Parent Company
            tech_products = tx.query(Product).where(
                Product.category == "Enterprise Software"
            ).find()
            assert len(tech_products) >= 1
            
            # Query 3: Find all executives in the corporate hierarchy
            executives = tx.query(Person).where(
                ("executive" in Person.tags) | ("leadership" in Person.tags)
            ).find()
            assert len(executives) >= 2
            
            # Query 4: Find high-value collaborations
            major_collaborators = tx.query(Company).where(
                Company.name.starts_with("Client") | Company.name.starts_with("Tech")
            ).find()
            assert len(major_collaborators) >= 2

    def test_social_network_analysis_patterns(self, repo):
        """Test social network analysis patterns and influence tracking."""
        with repo.transaction() as tx:
            # Create a social/professional network
            
            # Create people representing different roles and influence levels
            influencers = []
            connectors = []
            specialists = []
            
            # Influencers (high influence, many connections)
            for i in range(3):
                influencer = tx.create(Person(
                    email=f"influencer{i:02d}@network.com",
                    name=f"Influencer {i:02d}",
                    age=40 + i,
                    tags=["influencer", "thought-leader", "speaker"],
                    score=95.0 + i
                ))
                influencers.append(influencer)
            
            # Connectors (medium influence, bridge different groups)
            for i in range(5):
                connector = tx.create(Person(
                    email=f"connector{i:02d}@network.com",
                    name=f"Connector {i:02d}",
                    age=35 + i,
                    tags=["connector", "networker", "facilitator"],
                    score=85.0 + i
                ))
                connectors.append(connector)
            
            # Specialists (domain expertise, moderate connections)
            specialties = ["ai", "blockchain", "cloud", "security", "data", "mobile", "web", "iot"]
            for i, specialty in enumerate(specialties):
                specialist = tx.create(Person(
                    email=f"specialist{i:02d}@network.com",
                    name=f"{specialty.title()} Specialist",
                    age=30 + i,
                    tags=["specialist", specialty, "expert"],
                    score=80.0 + i
                ))
                specialists.append(specialist)
            
            # Create companies representing different tech sectors
            companies = []
            sectors = ["AI/ML", "Blockchain", "Cloud Computing", "Cybersecurity"]
            for i, sector in enumerate(sectors):
                company = tx.create(Company(
                    name=f"{sector} Corp",
                    founded=2015 + i,
                    industry="Technology",
                    employee_count=100 + (i * 50)
                ))
                companies.append(company)
            
            # Create projects representing collaborations
            projects = []
            project_types = ["Research Collaboration", "Industry Standard", "Open Source Initiative", "Conference Organization"]
            for i, proj_type in enumerate(project_types):
                project = tx.create(Project(
                    code=f"COLLAB-{i:02d}",
                    name=f"{proj_type} Project",
                    status="active",
                    budget=500000.0 + (i * 250000),
                    priority=1 + (i % 2)
                ))
                projects.append(project)
            
            # Create employment relationships
            # Influencers work at different companies
            for i, influencer in enumerate(influencers):
                company = companies[i % len(companies)]
                tx.relate(influencer, WorksAt(
                    role="VP of Innovation" if i == 0 else "Technical Director",
                    since=2018 + i,
                    salary=200000 + (i * 50000)
                ), company)
            
            # Connectors work across different companies
            for i, connector in enumerate(connectors):
                company = companies[(i + 1) % len(companies)]
                tx.relate(connector, WorksAt(
                    role="Partnership Manager" if i % 2 == 0 else "Business Development",
                    since=2019 + (i % 3),
                    salary=120000 + (i * 10000)
                ), company)
            
            # Specialists distributed across companies
            for i, specialist in enumerate(specialists):
                company = companies[i % len(companies)]
                tx.relate(specialist, WorksAt(
                    role="Senior Engineer",
                    since=2020 + (i % 4),
                    salary=140000 + (i * 5000)
                ), company)
            
            # Create collaboration patterns
            # Influencers lead major projects
            for i, project in enumerate(projects):
                lead = influencers[i % len(influencers)]
                tx.relate(lead, WorksOn(
                    role="Project Lead",
                    allocation=0.3,  # Part-time leadership
                    start_date="2024-01-01"
                ), project)
                
                # Connectors facilitate projects
                facilitator = connectors[i % len(connectors)]
                tx.relate(facilitator, WorksOn(
                    role="Project Coordinator", 
                    allocation=0.5,
                    start_date="2024-01-01"
                ), project)
                
                # Specialists contribute technical expertise
                for j in range(2):  # 2 specialists per project
                    specialist = specialists[(i * 2 + j) % len(specialists)]
                    tx.relate(specialist, WorksOn(
                        role="Technical Contributor",
                        allocation=0.4,
                        start_date="2024-01-01"
                    ), project)
            
            # Create reporting relationships for influence mapping
            # Connectors often report to influencers
            for i, connector in enumerate(connectors[:3]):
                influencer = influencers[i % len(influencers)]
                tx.relate(connector, Reports(
                    since=2022,
                    review_cycle="quarterly"
                ), influencer)
            
            # Some specialists report to connectors
            for i, specialist in enumerate(specialists[:4]):
                connector = connectors[i % len(connectors)]
                tx.relate(specialist, Reports(
                    since=2023,
                    review_cycle="monthly"
                ), connector)
        
        # Test social network analysis queries
        with repo.transaction() as tx:
            # Find network influencers
            network_influencers = tx.query(Person).where(
                "influencer" in Person.tags,
                Person.score > 95.0
            ).find()
            assert len(network_influencers) >= 2
            
            # Find connectors (people who bridge groups)
            network_connectors = tx.query(Person).where(
                "connector" in Person.tags
            ).find()
            assert len(network_connectors) >= 3
            
            # Find domain specialists
            ai_specialists = tx.query(Person).where(
                "ai" in Person.tags,
                "specialist" in Person.tags
            ).find()
            assert len(ai_specialists) >= 1
            
            # Find cross-company collaborations
            collaboration_projects = tx.query(Project).where(
                "Collaboration" in Project.name
            ).find()
            assert len(collaboration_projects) >= 1

    def test_temporal_relationship_patterns(self, repo):
        """Test time-based relationship analysis and evolution patterns."""
        with repo.transaction() as tx:
            # Create a scenario that evolves over time
            
            # Startup evolution scenario
            startup = tx.create(Company(
                name="StartupCorp",
                founded=2020,
                industry="Technology",
                employee_count=5  # Started small
            ))
            
            scale_up = tx.create(Company(
                name="ScaleUpCorp", 
                founded=2022,
                industry="Technology",
                employee_count=50  # After growth
            ))
            
            enterprise = tx.create(Company(
                name="EnterpriseCorp",
                founded=2024,
                industry="Technology", 
                employee_count=200  # Mature stage
            ))
            
            # Founder and early team
            founder = tx.create(Person(
                email="founder@startup.com",
                name="Founder Alice",
                age=32,
                tags=["founder", "ceo", "visionary"],
                score=98.0
            ))
            
            early_engineers = []
            for i in range(3):
                engineer = tx.create(Person(
                    email=f"early.eng{i:02d}@startup.com",
                    name=f"Early Engineer {i:02d}",
                    age=28 + i,
                    tags=["early-employee", "engineer", "startup"],
                    score=90.0 + i
                ))
                early_engineers.append(engineer)
            
            # Growth phase team
            growth_team = []
            for i in range(8):
                role_type = "engineer" if i < 5 else "manager"
                person = tx.create(Person(
                    email=f"growth.{role_type}{i:02d}@scaleup.com",
                    name=f"Growth {role_type.title()} {i:02d}",
                    age=25 + (i * 2),
                    tags=["growth-hire", role_type, "scale-up"],
                    score=85.0 + (i % 5)
                ))
                growth_team.append(person)
            
            # Enterprise phase team
            enterprise_team = []
            for i in range(15):
                if i < 8:
                    role_type = "engineer"
                elif i < 12:
                    role_type = "manager"
                else:
                    role_type = "executive"
                
                person = tx.create(Person(
                    email=f"enterprise.{role_type}{i:02d}@enterprise.com",
                    name=f"Enterprise {role_type.title()} {i:02d}",
                    age=24 + (i * 2),
                    tags=["enterprise-hire", role_type, "mature"],
                    score=82.0 + (i % 8)
                ))
                enterprise_team.append(person)
            
            # Create temporal employment relationships
            
            # Startup phase (2020-2021)
            tx.relate(founder, WorksAt(
                role="Founder & CEO",
                since=2020,
                salary=80000  # Low founder salary
            ), startup)
            
            for i, engineer in enumerate(early_engineers):
                tx.relate(engineer, WorksAt(
                    role="Software Engineer",
                    since=2020 + (i % 2),
                    salary=90000 + (i * 5000)
                ), startup)
            
            # Growth phase (2022-2023) - founder moves to scale-up
            tx.relate(founder, WorksAt(
                role="CEO",
                since=2022,
                salary=180000  # Higher CEO salary
            ), scale_up)
            
            # Some early employees follow to scale-up
            for i, engineer in enumerate(early_engineers[:2]):
                tx.relate(engineer, WorksAt(
                    role="Senior Engineer" if i == 0 else "Engineering Manager",
                    since=2022,
                    salary=130000 + (i * 20000)
                ), scale_up)
            
            # New growth hires
            for i, person in enumerate(growth_team):
                role = "Software Engineer" if "engineer" in person.tags else "Team Manager"
                tx.relate(person, WorksAt(
                    role=role,
                    since=2022 + (i % 2),
                    salary=100000 + (i * 8000)
                ), scale_up)
            
            # Enterprise phase (2024) - transition to enterprise
            tx.relate(founder, WorksAt(
                role="Chief Executive Officer",
                since=2024,
                salary=300000  # Executive salary
            ), enterprise)
            
            # Key people transition
            for i, engineer in enumerate(early_engineers[:1]):  # Only top engineer
                tx.relate(engineer, WorksAt(
                    role="VP of Engineering",
                    since=2024,
                    salary=250000
                ), enterprise)
            
            # Growth team members transition
            for i, person in enumerate(growth_team[:5]):
                role = "Staff Engineer" if "engineer" in person.tags else "Director"
                tx.relate(person, WorksAt(
                    role=role,
                    since=2024,
                    salary=150000 + (i * 15000)
                ), enterprise)
            
            # New enterprise hires
            for i, person in enumerate(enterprise_team):
                if "engineer" in person.tags:
                    role = "Software Engineer"
                    salary = 110000 + (i * 5000)
                elif "manager" in person.tags:
                    role = "Engineering Manager"
                    salary = 140000 + (i * 8000)
                else:
                    role = "Senior Director"
                    salary = 200000 + (i * 10000)
                
                tx.relate(person, WorksAt(
                    role=role,
                    since=2024,
                    salary=salary
                ), enterprise)
            
            # Create projects representing company evolution
            mvp_project = tx.create(Project(
                code="MVP-2020",
                name="Minimum Viable Product",
                status="completed",
                budget=500000.0,
                priority=1
            ))
            
            growth_project = tx.create(Project(
                code="SCALE-2022",
                name="Platform Scaling Initiative",
                status="completed", 
                budget=2000000.0,
                priority=1
            ))
            
            enterprise_project = tx.create(Project(
                code="ENTERPRISE-2024",
                name="Enterprise Platform",
                status="active",
                budget=10000000.0,
                priority=1
            ))
            
            # Project assignments reflecting temporal patterns
            tx.relate(founder, WorksOn(role="Product Owner", allocation=1.0, start_date="2020-01-01"), mvp_project)
            for engineer in early_engineers:
                tx.relate(engineer, WorksOn(role="Developer", allocation=1.0, start_date="2020-01-01"), mvp_project)
            
            tx.relate(founder, WorksOn(role="Executive Sponsor", allocation=0.3, start_date="2022-01-01"), growth_project)
            for person in growth_team[:6]:
                tx.relate(person, WorksOn(role="Developer", allocation=0.8, start_date="2022-01-01"), growth_project)
            
            tx.relate(founder, WorksOn(role="Executive Sponsor", allocation=0.2, start_date="2024-01-01"), enterprise_project)
            for person in enterprise_team[:10]:
                tx.relate(person, WorksOn(role="Team Member", allocation=0.6, start_date="2024-01-01"), enterprise_project)
        
        # Test temporal analysis queries
        with repo.transaction() as tx:
            # Find company founders
            founders = tx.query(Person).where(
                "founder" in Person.tags
            ).find()
            assert len(founders) >= 1
            
            # Find early employees (loyal across phases)
            early_employees = tx.query(Person).where(
                "early-employee" in Person.tags
            ).find()
            assert len(early_employees) >= 3
            
            # Find current enterprise employees
            current_employees = tx.query(Person).where(
                ("enterprise-hire" in Person.tags) | ("mature" in Person.tags)
            ).find()
            assert len(current_employees) >= 10
            
            # Find active projects
            active_projects = tx.query(Project).where(
                Project.status == "active",
                Project.budget > 5000000.0
            ).find()
            assert len(active_projects) >= 1
            
            # Find high-budget evolution projects
            major_projects = tx.query(Project).where(
                Project.budget > 1000000.0
            ).find()
            assert len(major_projects) >= 2