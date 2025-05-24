#!/usr/bin/env python
"""
Script to clear all nodes from the Neo4j database.
This gives us a clean slate to work with.
"""

from neo4j import GraphDatabase

# Initialize connection
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_secure_password"))


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
