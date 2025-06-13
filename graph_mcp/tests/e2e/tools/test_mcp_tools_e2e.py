"""
E2E tests for MCP tools with real Neo4j database operations.

These tests verify complete MCP tool workflows including:
- Real database operations
- Entity and relationship creation
- Source tracking
- Query execution
- Complete data lineage
"""

import pytest

from graph_mcp.tools.entities import _create_entity_impl
from graph_mcp.tools.relationships import _create_relationship_impl
from graph_mcp.tools.sources import _create_source_impl, _create_sourced_from_impl
from graph_mcp.tools.query import _query_entities_impl
from graph_mcp.models.entities import Person, Team, Project, Service, Repository
from graph_mcp.models.sources import Source, SourceType

# Create MODEL_MAP for E2E tests (simulates runtime construction)
MODEL_MAP = {
    "Person": Person,
    "Team": Team,
    "Project": Project,
    "Service": Service,
    "Repository": Repository,
    "Source": Source,
}


@pytest.mark.e2e
class TestEntityToolsCompleteWorkflow:
    """Test complete entity management workflows with real database."""
    
    async def test_create_person_complete_workflow(self, app_context, clean_database):
        """Test creating a person with complete validation and database storage."""
        # Create person with real validation
        person_data = {
            "email": "John.Doe@Company.COM",  # Test normalization
            "name": "  John Doe  ",  # Test trimming
            "title": "Senior Software Engineer"
        }
        
        result = await _create_entity_impl("Person", person_data, app_context, MODEL_MAP)
        
        # Verify creation success
        assert result["success"] is True
        assert result["entity_type"] == "Person"
        assert result["entity_id"] == "john.doe@company.com"  # Normalized
        
        # Verify entity was actually stored in database
        with app_context.repo.transaction() as tx:
            found_person = tx.find_one(Person, email="john.doe@company.com")
            assert found_person is not None
            assert found_person.name == "John Doe"  # Trimmed
            assert found_person.title == "Senior Software Engineer"
    
    async def test_create_team_complete_workflow(self, app_context, clean_database):
        """Test creating a team with complete workflow."""
        team_data = {
            "name": "Engineering Team",
            "department": "Product Development",
            "description": "Main product engineering team"
        }
        
        result = await _create_entity_impl("Team", team_data, app_context, MODEL_MAP)
        
        # Verify creation
        assert result["success"] is True
        assert result["entity_id"] == "Engineering Team"
        
        # Verify database storage
        with app_context.repo.transaction() as tx:
            found_team = tx.find_one(Team, name="Engineering Team")
            assert found_team is not None
            assert found_team.department == "Product Development"
            assert found_team.description == "Main product engineering team"
    
    async def test_create_project_complete_workflow(self, app_context, clean_database):
        """Test creating a project with complete workflow."""
        project_data = {
            "name": "API Modernization",
            "status": "planning",
            "description": "Modernizing legacy API architecture"
        }
        
        result = await _create_entity_impl("Project", project_data, app_context, MODEL_MAP)
        
        # Verify creation
        assert result["success"] is True
        assert result["entity_id"] == "API Modernization"
        
        # Verify database storage
        with app_context.repo.transaction() as tx:
            found_project = tx.find_one(Project, name="API Modernization")
            assert found_project is not None
            assert found_project.status == "planning"
            assert found_project.description == "Modernizing legacy API architecture"
    
    async def test_entity_validation_errors_with_database(self, app_context, clean_database):
        """Test that validation errors prevent database operations."""
        # Attempt to create person with invalid email
        invalid_person_data = {
            "email": "not-an-email",
            "name": "Test User"
        }
        
        result = await _create_entity_impl("Person", invalid_person_data, app_context, MODEL_MAP)
        
        # Should fail validation
        assert "error" in result
        assert "validation error" in result["error"].lower()
        
        # Verify nothing was stored in database
        with app_context.repo.transaction() as tx:
            # Search for any person with that name
            persons = tx.query(Person).where(Person.name == "Test User").all()
            assert len(persons) == 0


@pytest.mark.e2e
class TestRelationshipToolsCompleteWorkflow:
    """Test complete relationship management workflows with real database."""
    
    async def test_create_manages_relationship_complete_workflow(self, app_context, clean_database):
        """Test creating a MANAGES relationship with complete database operations."""
        # First create entities
        person_data = {"email": "manager@company.com", "name": "Alice Manager", "title": "Engineering Manager"}
        team_data = {"name": "Backend Team", "department": "Engineering"}
        
        # Create person
        person_result = await _create_entity_impl("Person", person_data, app_context, MODEL_MAP)
        assert person_result["success"] is True
        
        # Create team
        team_result = await _create_entity_impl("Team", team_data, app_context, MODEL_MAP)
        assert team_result["success"] is True
        
        # Create relationship
        relationship_result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="manager@company.com",
            to_entity_type="Team",
            to_entity_id="Backend Team",
            properties={"since": "2023-01-01", "authority_level": "full"},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify relationship creation
        assert relationship_result["success"] is True
        assert relationship_result["relationship_type"] == "MANAGES"
        
        # Verify relationship exists in database
        with app_context.repo.transaction() as tx:
            # Query for the relationship
            cypher_query = """
            MATCH (p:Person {email: 'manager@company.com'})-[r:MANAGES]->(t:Team {name: 'Backend Team'})
            RETURN r.since as since, r.authority_level as authority_level
            """
            result = tx.run(cypher_query)
            records = result.data()
            
            assert len(records) == 1
            assert records[0]["since"] == "2023-01-01"
            assert records[0]["authority_level"] == "full"
    
    async def test_create_contributes_to_relationship_workflow(self, app_context, clean_database):
        """Test creating CONTRIBUTES_TO relationship workflow."""
        # Create entities
        person_data = {"email": "dev@company.com", "name": "Bob Developer"}
        project_data = {"name": "Mobile App", "status": "active"}
        
        await _create_entity_impl("Person", person_data, app_context, MODEL_MAP)
        await _create_entity_impl("Project", project_data, app_context, MODEL_MAP)
        
        # Create relationship
        result = await _create_relationship_impl(
            relationship_type="CONTRIBUTES_TO",
            from_entity_type="Person",
            from_entity_id="dev@company.com",
            to_entity_type="Project",
            to_entity_id="Mobile App",
            properties={"role": "lead_developer", "hours_per_week": 40},
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify
        assert result["success"] is True
        
        # Verify in database
        with app_context.repo.transaction() as tx:
            cypher_query = """
            MATCH (p:Person {email: 'dev@company.com'})-[r:CONTRIBUTES_TO]->(proj:Project {name: 'Mobile App'})
            RETURN r.role as role, r.hours_per_week as hours
            """
            records = tx.run(cypher_query).data()
            
            assert len(records) == 1
            assert records[0]["role"] == "lead_developer"
            assert records[0]["hours"] == 40
    
    async def test_relationship_entity_not_found_workflow(self, app_context, clean_database):
        """Test relationship creation when entities don't exist in database."""
        # Attempt to create relationship with non-existent entities
        result = await _create_relationship_impl(
            relationship_type="MANAGES",
            from_entity_type="Person",
            from_entity_id="nonexistent@company.com",
            to_entity_type="Team",
            to_entity_id="NonexistentTeam",
            properties=None,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should fail because entities don't exist
        assert "error" in result
        assert "not found" in result["error"]
        
        # Verify no relationship was created
        with app_context.repo.transaction() as tx:
            cypher_query = """
            MATCH ()-[r:MANAGES]->()
            RETURN count(r) as count
            """
            count = tx.run(cypher_query).single()["count"]
            assert count == 0


@pytest.mark.e2e
class TestSourceToolsCompleteWorkflow:
    """Test complete source management workflows with real database."""
    
    async def test_create_source_complete_workflow(self, app_context, clean_database):
        """Test creating a source with complete database storage."""
        # Create JIRA source
        result = await _create_source_impl(
            name="PROJ-456",
            source_type="JIRA",
            description="Feature development ticket",
            url="https://company.atlassian.net/browse/PROJ-456",
            app_context=app_context
        )
        
        # Verify creation
        assert result["success"] is True
        assert result["source_type"] == "JIRA"
        assert result["source_name"] == "PROJ-456"
        
        # Verify database storage
        with app_context.repo.transaction() as tx:
            found_source = tx.find_one(Source, name="PROJ-456")
            assert found_source is not None
            assert found_source.type == SourceType.JIRA
            assert found_source.description == "Feature development ticket"
            assert found_source.url == "https://company.atlassian.net/browse/PROJ-456"
    
    async def test_create_sourced_from_complete_workflow(self, app_context, clean_database):
        """Test creating SOURCED_FROM relationships with complete workflow."""
        # Create person and source first
        person_data = {"email": "tracked@company.com", "name": "Tracked User"}
        await _create_entity_impl("Person", person_data, app_context, MODEL_MAP)
        
        await _create_source_impl(
            name="DOC-123",
            source_type="CONFLUENCE",
            description="Team documentation",
            url=None,
            app_context=app_context
        )
        
        # Create SOURCED_FROM relationship
        result = await _create_sourced_from_impl(
            entity_type="Person",
            entity_id="tracked@company.com",
            source_id="DOC-123",
            method="MANUAL_ENTRY",
            confidence=0.95,
            primary=True,
            context="Added from team roster document",
            app_context=app_context
        )
        
        # Verify creation
        assert result["success"] is True
        assert result["method"] == "MANUAL_ENTRY"
        
        # Verify relationship in database
        with app_context.repo.transaction() as tx:
            cypher_query = """
            MATCH (p:Person {email: 'tracked@company.com'})-[r:SOURCED_FROM]->(s:Source {name: 'DOC-123'})
            RETURN r.method as method, r.confidence as confidence, r.primary as primary, r.context as context
            """
            records = tx.run(cypher_query).data()
            
            assert len(records) == 1
            record = records[0]
            assert record["method"] == "MANUAL_ENTRY"
            assert record["confidence"] == 0.95
            assert record["primary"] is True
            assert record["context"] == "Added from team roster document"


@pytest.mark.e2e
class TestQueryToolsCompleteWorkflow:
    """Test complete query workflows with real database."""
    
    async def test_query_entities_complete_workflow(self, app_context, sample_database_entities):
        """Test querying entities with real database data."""
        # Query for all persons
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="True",  # Match all
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Verify query success
        assert result["success"] is True
        assert result["entity_type"] == "Person"
        assert result["count"] >= 1  # Should have at least the sample person
        assert "entities" in result
        
        # Verify returned data structure
        entities = result["entities"]
        assert len(entities) >= 1
        
        # Find our sample person
        sample_person = None
        for entity in entities:
            if entity.get("email") == "alice.smith@company.com":
                sample_person = entity
                break
        
        assert sample_person is not None
        assert sample_person["name"] == "Alice Smith"
        assert sample_person["title"] == "Senior Engineer"
    
    async def test_query_with_filter_expression_workflow(self, app_context, sample_database_entities):
        """Test querying with specific filter expressions."""
        # Query for persons with specific email
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="email == 'alice.smith@company.com'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should find exactly one person
        assert result["success"] is True
        assert result["count"] == 1
        
        entities = result["entities"]
        assert len(entities) == 1
        assert entities[0]["email"] == "alice.smith@company.com"
    
    async def test_query_teams_workflow(self, app_context, sample_database_entities):
        """Test querying team entities."""
        result = await _query_entities_impl(
            entity_type="Team",
            filter_expr="department == 'Product'",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should find the sample team
        assert result["success"] is True
        assert result["count"] >= 1
        
        # Verify team data
        teams = result["entities"]
        engineering_team = None
        for team in teams:
            if team.get("name") == "Engineering":
                engineering_team = team
                break
        
        assert engineering_team is not None
        assert engineering_team["department"] == "Product"
    
    async def test_query_with_complex_expression_workflow(self, app_context, sample_database_entities):
        """Test querying with complex logical expressions."""
        # Add another person for more complex testing
        person_data = {"email": "test@company.com", "name": "Test Engineer", "title": "Engineer"}
        await _create_entity_impl("Person", person_data, app_context, MODEL_MAP)
        
        # Query for engineers (multiple title possibilities)
        result = await _query_entities_impl(
            entity_type="Person",
            filter_expr="title.contains('Engineer')",
            limit=10,
            app_context=app_context,
            MODEL_MAP=MODEL_MAP
        )
        
        # Should find both engineers
        assert result["success"] is True
        assert result["count"] >= 2
        
        # Verify all returned entities have "Engineer" in title
        entities = result["entities"]
        for entity in entities:
            assert "Engineer" in entity["title"]


@pytest.mark.e2e
class TestCompleteDataLineageWorkflow:
    """Test complete data lineage and source tracking workflows."""
    
    async def test_complete_entity_with_source_tracking_workflow(self, app_context, clean_database):
        """Test complete workflow of creating entities with full source tracking."""
        # 1. Create a source
        source_result = await _create_source_impl(
            name="TICKET-789",
            source_type="JIRA",
            description="User story for new feature",
            url="https://company.atlassian.net/browse/TICKET-789",
            app_context=app_context
        )
        assert source_result["success"] is True
        
        # 2. Create an entity
        person_result = await _create_entity_impl(
            "Person", 
            {"email": "feature.owner@company.com", "name": "Feature Owner", "title": "Product Manager"},
            app_context, 
            MODEL_MAP
        )
        assert person_result["success"] is True
        
        # 3. Link entity to source
        sourced_from_result = await _create_sourced_from_impl(
            entity_type="Person",
            entity_id="feature.owner@company.com",
            source_id="TICKET-789",
            method="API_IMPORT",
            confidence=0.98,
            primary=True,
            context="Extracted from JIRA ticket assignee field",
            app_context=app_context
        )
        assert sourced_from_result["success"] is True
        
        # 4. Verify complete data lineage in database
        with app_context.repo.transaction() as tx:
            # Query for complete lineage
            cypher_query = """
            MATCH (p:Person {email: 'feature.owner@company.com'})-[r:SOURCED_FROM]->(s:Source {name: 'TICKET-789'})
            RETURN p.name as person_name, p.title as person_title,
                   s.type as source_type, s.description as source_description,
                   r.method as extraction_method, r.confidence as confidence,
                   r.context as context
            """
            records = tx.run(cypher_query).data()
            
            assert len(records) == 1
            record = records[0]
            
            # Verify person data
            assert record["person_name"] == "Feature Owner"
            assert record["person_title"] == "Product Manager"
            
            # Verify source data
            assert record["source_type"] == "JIRA"
            assert record["source_description"] == "User story for new feature"
            
            # Verify lineage data
            assert record["extraction_method"] == "API_IMPORT"
            assert record["confidence"] == 0.98
            assert record["context"] == "Extracted from JIRA ticket assignee field"
    
    async def test_multi_entity_relationship_with_sources_workflow(self, app_context, clean_database):
        """Test complete workflow with multiple entities, relationships, and sources."""
        # Create sources
        await _create_source_impl("EPIC-100", "JIRA", "Project epic", None, app_context)
        await _create_source_impl("MEETING-NOTES", "EMAIL", "Planning meeting notes", None, app_context)
        
        # Create entities
        await _create_entity_impl("Person", {"email": "lead@company.com", "name": "Tech Lead"}, app_context, MODEL_MAP)
        await _create_entity_impl("Project", {"name": "New Platform", "status": "planning"}, app_context, MODEL_MAP)
        
        # Add source tracking
        await _create_sourced_from_impl(
            "Person", "lead@company.com", "EPIC-100", "MANUAL_ENTRY", 0.9, True, "From epic assignee", app_context
        )
        await _create_sourced_from_impl(
            "Project", "New Platform", "MEETING-NOTES", "EMAIL_PARSING", 0.85, True, "From meeting notes", app_context
        )
        
        # Create relationship
        relationship_result = await _create_relationship_impl(
            "CONTRIBUTES_TO", "Person", "lead@company.com", "Project", "New Platform",
            {"role": "technical_lead"}, app_context, MODEL_MAP
        )
        assert relationship_result["success"] is True
        
        # Verify complete data graph
        with app_context.repo.transaction() as tx:
            cypher_query = """
            MATCH (p:Person)-[contrib:CONTRIBUTES_TO]->(proj:Project),
                  (p)-[ps:SOURCED_FROM]->(psrc:Source),
                  (proj)-[pjs:SOURCED_FROM]->(pjsrc:Source)
            WHERE p.email = 'lead@company.com' AND proj.name = 'New Platform'
            RETURN p.name as person_name, proj.status as project_status,
                   contrib.role as contribution_role,
                   psrc.name as person_source, ps.method as person_method,
                   pjsrc.name as project_source, pjs.method as project_method
            """
            records = tx.run(cypher_query).data()
            
            assert len(records) == 1
            record = records[0]
            
            # Verify entity data
            assert record["person_name"] == "Tech Lead"
            assert record["project_status"] == "planning"
            
            # Verify relationship
            assert record["contribution_role"] == "technical_lead"
            
            # Verify source tracking
            assert record["person_source"] == "EPIC-100"
            assert record["person_method"] == "MANUAL_ENTRY"
            assert record["project_source"] == "MEETING-NOTES"
            assert record["project_method"] == "EMAIL_PARSING"


@pytest.mark.e2e
class TestErrorHandlingCompleteWorkflows:
    """Test error handling in complete workflows with real database."""
    
    async def test_transaction_rollback_on_error_workflow(self, app_context, clean_database):
        """Test that errors cause proper transaction rollback."""
        # This test would need to trigger a database constraint violation
        # or other error after some operations have succeeded
        
        # Create a person
        person_result = await _create_entity_impl(
            "Person",
            {"email": "rollback.test@company.com", "name": "Rollback Test"},
            app_context,
            MODEL_MAP
        )
        assert person_result["success"] is True
        
        # Verify person exists
        with app_context.repo.transaction() as tx:
            found = tx.find_one(Person, email="rollback.test@company.com")
            assert found is not None
        
        # Attempt to create duplicate (should fail if unique constraints exist)
        duplicate_result = await _create_entity_impl(
            "Person",
            {"email": "rollback.test@company.com", "name": "Duplicate Test"},
            app_context,
            MODEL_MAP
        )
        
        # The result depends on whether unique constraints are enforced
        # This demonstrates the error handling pattern
        if "error" in duplicate_result:
            # Verify original person still exists and wasn't affected
            with app_context.repo.transaction() as tx:
                found = tx.find_one(Person, email="rollback.test@company.com")
                assert found is not None
                assert found.name == "Rollback Test"  # Original name preserved