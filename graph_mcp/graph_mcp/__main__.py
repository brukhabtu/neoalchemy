#!/usr/bin/env python
"""
Entry point for running graph_mcp as a module.
Usage: python -m graph_mcp
"""

from .mcp_server import main


def main_entry():
    """Entry point for console script."""
    main()


if __name__ == "__main__":
    main()
