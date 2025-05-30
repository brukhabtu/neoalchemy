#!/usr/bin/env python
"""
Script to clear all nodes from the Neo4j database.
This gives us a clean slate to work with.
"""

import os
from neo4j import GraphDatabase

# Initialize connection with environment variable support
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


def clear_database():
    """Delete all nodes and relationships from the database."""
    with driver.session() as session:
        # Clear all the data
        result = session.run("MATCH (n) DETACH DELETE n")
        print("Database cleared successfully!")

        # Verify the database is empty
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        print(f"Node count after clearing: {node_count}")


if __name__ == "__main__":
    try:
        clear_database()
    finally:
        driver.close()
