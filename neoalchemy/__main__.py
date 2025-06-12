#!/usr/bin/env python
"""
NeoAlchemy CLI - Command line interface for NeoAlchemy operations.

Usage:
    neoalch db clear [--uri URI] [--user USER] [--password PASSWORD]
    neoalch db status [--uri URI] [--user USER] [--password PASSWORD]
    neoalch --help
    neoalch --version

Commands:
    db clear     Clear all nodes and relationships from the database
    db status    Show database connection status and basic info

Options:
    --uri URI           Neo4j connection URI [default: bolt://localhost:7687]
    --user USER         Neo4j username [default: neo4j]
    --password PASSWORD Neo4j password [default: password]
    --help              Show this help message
    --version           Show version information
"""

import os
import sys
from typing import Any, Dict

from docopt import docopt  # type: ignore[import-untyped]
from neo4j.exceptions import AuthError, ServiceUnavailable

from neoalchemy import __version__
from neoalchemy.utils.database import clear_database, get_database_info


def _get_connection_params(arguments: Dict[str, Any]) -> tuple[str, str, str]:
    """Extract connection parameters from CLI arguments and environment."""
    uri = arguments.get("--uri") or os.getenv("NEO4J_URI") or "bolt://localhost:7687"
    user = arguments.get("--user") or os.getenv("NEO4J_USER") or "neo4j"
    password = arguments.get("--password") or os.getenv("NEO4J_PASSWORD") or "password"
    return uri, user, password


def _cmd_db_clear(arguments: Dict[str, Any]) -> None:
    """Handle 'db clear' command."""
    uri, user, password = _get_connection_params(arguments)
    
    print(f"🧹 Clearing database at {uri}...")
    try:
        node_count = clear_database(uri, (user, password))
        print(f"✅ Database cleared successfully! Removed {node_count} nodes.")
    except ServiceUnavailable:
        print(f"❌ Cannot connect to Neo4j at {uri}. Is the service running?")
        sys.exit(1)
    except AuthError:
        print("❌ Authentication failed. Check username/password.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to clear database: {e}")
        sys.exit(1)


def _cmd_db_status(arguments: Dict[str, Any]) -> None:
    """Handle 'db status' command."""
    uri, user, password = _get_connection_params(arguments)
    
    print(f"📊 Checking database status at {uri}...")
    try:
        info = get_database_info(uri, (user, password))
        print(f"✅ Connected to Neo4j {info['version']}")
        print("📈 Database contains:")
        print(f"   - {info['node_count']} nodes")
        print(f"   - {info['relationship_count']} relationships")
        print(f"   - {info['constraint_count']} constraints")
        print(f"   - {info['index_count']} indexes")
    except ServiceUnavailable:
        print(f"❌ Cannot connect to Neo4j at {uri}. Is the service running?")
        sys.exit(1)
    except AuthError:
        print("❌ Authentication failed. Check username/password.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    arguments = docopt(__doc__, version=f"NeoAlchemy {__version__}")
    
    # Handle commands
    if arguments["db"]:
        if arguments["clear"]:
            _cmd_db_clear(arguments)
        elif arguments["status"]:
            _cmd_db_status(arguments)
    else:
        # Should not reach here due to docopt validation
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()