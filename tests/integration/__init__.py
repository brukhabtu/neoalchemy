"""
Integration tests for NeoAlchemy.

Integration tests verify that components work correctly when interacting with
a real Neo4j database, but don't test complete end-to-end user workflows.

These tests are designed to be:
- Faster than e2e tests (5-10 seconds total)
- More realistic than unit tests (real database)
- Focused on component boundaries and database interactions

Directory structure:
- orm/: NeoAlchemy ORM integration tests (repository, models, queries, etc.)
"""