"""
Safe code execution environment for NeoAlchemy.
"""
import sys
import io
import textwrap
from typing import Any, Dict, Optional
import ast
import traceback
import contextlib
import threading
import time
from neo4j import GraphDatabase
from importlib import import_module

# Import sourced models and NeoAlchemy
from sourced_models import Person, Project, Team
from sourced_models import WORKS_ON, BELONGS_TO, MANAGES
from sources import Source, SourceType, SOURCED_FROM, initialize_sources
from neoalchemy import initialize
from neoalchemy.orm.repository import Neo4jRepository
from neo4j.time import DateTime, Date

# Initialize field expressions
initialize()

def run_neoalchemy_code(
    code: str, 
    driver: GraphDatabase.driver,
    timeout_seconds: int = 10
) -> Dict[str, Any]:
    """Run NeoAlchemy code in a safe environment with timeout.
    
    Args:
        code: Python code to execute
        driver: Neo4j driver instance
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Dictionary with execution results containing:
        - stdout: Captured standard output
        - result: Return value (if any)
        - error: Error message (if execution failed)
    """
    # Captured output and result
    stdout_capture = io.StringIO()
    result_value = None
    error_message = None
    
    # Create a repository
    repo = Neo4jRepository(driver)
    
    # Always wrap the code in a transaction
    code = f"""
# Auto-wrapped in transaction
result = None
with repo.transaction() as tx:
    {code.replace(chr(10), chr(10)+'    ')}
    
    # Store the last result for return
    result = locals().get('result', None)
result  # Return the result
"""
    
    # Initialize source mechanism
    initialize_sources()
    
    # Execution globals
    execution_globals = {
        # Sourced Models
        "Person": Person,
        "Project": Project,
        "Team": Team,
        "WORKS_ON": WORKS_ON,
        "BELONGS_TO": BELONGS_TO, 
        "MANAGES": MANAGES,
        
        # Source models and types
        "Source": Source,
        "SourceType": SourceType,
        "SOURCED_FROM": SOURCED_FROM,
        
        # Neo4j types
        "Date": Date,
        "DateTime": DateTime,
        
        # NeoAlchemy components
        "repo": repo,
        
        # Python standard library
        "print": print,
        "datetime": import_module("datetime"),
    }
    
    # Parse the code to check if it's an expression or statements
    try:
        parsed = ast.parse(code.strip(), mode="eval")
        is_expression = True
    except SyntaxError:
        try:
            parsed = ast.parse(code.strip(), mode="exec")
            is_expression = False
        except SyntaxError as e:
            return {
                "stdout": "",
                "result": None,
                "error": f"Syntax error: {str(e)}"
            }
    
    # Create thread for execution
    result_container = {"value": None}
    
    def execute_code():
        nonlocal result_value, error_message
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                if is_expression:
                    # Evaluate expression and capture result
                    compiled_code = compile(parsed, "<string>", "eval")
                    result_container["value"] = eval(compiled_code, execution_globals)
                else:
                    # Execute statements
                    compiled_code = compile(parsed, "<string>", "exec")
                    local_vars = {}
                    exec(compiled_code, execution_globals, local_vars)
                    
                    # Check for return value in last expression
                    last_var = None
                    for var_name in local_vars:
                        last_var = local_vars[var_name]
                    result_container["value"] = last_var
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc(file=stdout_capture)
    
    # Create and start execution thread with timeout
    execution_thread = threading.Thread(target=execute_code)
    execution_thread.daemon = True
    execution_thread.start()
    execution_thread.join(timeout_seconds)
    
    # Check if thread is still alive (timeout occurred)
    if execution_thread.is_alive():
        return {
            "stdout": f"Execution timed out after {timeout_seconds} seconds",
            "result": None,
            "error": f"Execution timed out after {timeout_seconds} seconds"
        }
    
    # Format the result to make it JSON-serializable
    formatted_result = format_result(result_container["value"])
    
    return {
        "stdout": stdout_capture.getvalue(),
        "result": formatted_result,
        "error": error_message
    }

def format_result(result: Any) -> Any:
    """Format results to be JSON-serializable.
    
    Args:
        result: The value to format
        
    Returns:
        JSON-serializable version of the value
    """
    # Handle None
    if result is None:
        return None
        
    # Handle lists and tuples
    if isinstance(result, (list, tuple)):
        return [format_result(item) for item in result]
        
    # Handle dictionaries
    if isinstance(result, dict):
        return {str(k): format_result(v) for k, v in result.items()}
        
    # Handle Neo4jModel instances
    if hasattr(result, "model_dump"):
        # This is likely a Pydantic model - use its serialization
        try:
            return result.model_dump()
        except Exception:
            # Fallback to basic dict conversion
            try:
                return {k: format_result(v) for k, v in result.__dict__.items() 
                       if not k.startswith("_")}
            except Exception:
                return str(result)
    
    # Handle Neo4j's datetime types
    if hasattr(result, "__class__") and "neo4j.time" in str(result.__class__):
        return str(result)
            
    # Handle basic types that are JSON-serializable
    if isinstance(result, (str, int, float, bool)):
        return result
        
    # Default: convert to string
    return str(result)