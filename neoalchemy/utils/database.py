"""
Database utilities for NeoAlchemy development and testing.

Provides common database operations used by CLI tools, testing fixtures,
and development scripts.
"""

from typing import Any, Dict, Optional, Tuple, Union

from neo4j import Driver, GraphDatabase


def clear_database(
    uri_or_driver: Union[str, Driver], 
    auth: Optional[Tuple[str, str]] = None
) -> int:
    """
    Clear all nodes and relationships from a Neo4j database.
    
    Args:
        uri_or_driver: Either a Neo4j URI string or an existing Driver instance
        auth: Username/password tuple, only used if uri_or_driver is a string
        
    Returns:
        Number of nodes that were deleted
        
    Raises:
        Exception: If database connection or operation fails
    """
    if isinstance(uri_or_driver, str):
        if auth is None:
            raise ValueError("auth parameter required when using URI string")
        driver = GraphDatabase.driver(uri_or_driver, auth=auth)
        should_close = True
    else:
        driver = uri_or_driver
        should_close = False
    
    try:
        with driver.session() as session:
            # Get count before deletion for reporting
            node_count_result = session.run("MATCH (n) RETURN count(n) as count")
            record = node_count_result.single()
            if record is None:
                raise RuntimeError("Failed to get node count")
            node_count = record["count"]
            
            # Clear all data
            session.run("MATCH (n) DETACH DELETE n")
            
            # Verify the database is empty
            final_count_result = session.run("MATCH (n) RETURN count(n) as count")
            final_record = final_count_result.single()
            if final_record is None:
                raise RuntimeError("Failed to verify database clear")
            final_count = final_record["count"]
            
            if final_count != 0:
                raise RuntimeError(f"Database clear failed: {final_count} nodes remain")
                
            return int(node_count)
            
    finally:
        if should_close:
            driver.close()


def get_database_info(
    uri_or_driver: Union[str, Driver], 
    auth: Optional[Tuple[str, str]] = None
) -> Dict[str, Any]:
    """
    Get basic information about a Neo4j database.
    
    Args:
        uri_or_driver: Either a Neo4j URI string or an existing Driver instance
        auth: Username/password tuple, only used if uri_or_driver is a string
        
    Returns:
        Dictionary containing database information:
        - version: Neo4j version string
        - node_count: Number of nodes in database
        - relationship_count: Number of relationships in database
        - constraint_count: Number of constraints
        - index_count: Number of indexes
        
    Raises:
        Exception: If database connection fails
    """
    if isinstance(uri_or_driver, str):
        if auth is None:
            raise ValueError("auth parameter required when using URI string")
        driver = GraphDatabase.driver(uri_or_driver, auth=auth)
        should_close = True
    else:
        driver = uri_or_driver
        should_close = False
    
    try:
        # Verify connectivity first
        driver.verify_connectivity()
        
        with driver.session() as session:
            # Get version information
            version_query = "CALL dbms.components() YIELD versions RETURN versions[0] as version"
            version_result = session.run(version_query)
            version_record = version_result.single()
            if version_record is None:
                raise RuntimeError("Failed to get Neo4j version")
            version = version_record["version"]
            
            # Get node count
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_record = node_result.single()
            if node_record is None:
                raise RuntimeError("Failed to get node count")
            node_count = node_record["count"]
            
            # Get relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_record = rel_result.single()
            if rel_record is None:
                raise RuntimeError("Failed to get relationship count")
            relationship_count = rel_record["count"]
            
            # Get constraint count (Neo4j 4.0+ syntax)
            try:
                constraint_result = session.run("SHOW CONSTRAINTS")
                constraint_count = len(constraint_result.data())
            except Exception:
                # Fallback for older Neo4j versions
                constraint_count = 0
            
            # Get index count (Neo4j 4.0+ syntax)
            try:
                index_result = session.run("SHOW INDEXES")
                # Filter out system indexes
                indexes = [idx for idx in index_result.data() 
                          if not idx.get("type", "").startswith("LOOKUP")]
                index_count = len(indexes)
            except Exception:
                # Fallback for older Neo4j versions
                index_count = 0
            
            return {
                "version": version,
                "node_count": node_count,
                "relationship_count": relationship_count,
                "constraint_count": constraint_count,
                "index_count": index_count,
            }
            
    finally:
        if should_close:
            driver.close()


def setup_test_database(
    uri_or_driver: Union[str, Driver], 
    auth: Optional[Tuple[str, str]] = None,
    clear_first: bool = True
) -> None:
    """
    Set up a clean database for testing with constraints.
    
    Args:
        uri_or_driver: Either a Neo4j URI string or an existing Driver instance
        auth: Username/password tuple, only used if uri_or_driver is a string
        clear_first: Whether to clear the database before setup
        
    Raises:
        Exception: If database setup fails
    """
    if isinstance(uri_or_driver, str):
        if auth is None:
            raise ValueError("auth parameter required when using URI string")
        driver = GraphDatabase.driver(uri_or_driver, auth=auth)
        should_close = True
    else:
        driver = uri_or_driver
        should_close = False
    
    try:
        if clear_first:
            clear_database(driver)
        
        # Import and set up constraints
        from neoalchemy.constraints import setup_constraints
        setup_constraints(driver)
        
    finally:
        if should_close:
            driver.close()