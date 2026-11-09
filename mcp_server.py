#!/usr/bin/env python3
"""Launcher para el servidor MCP de GoLuminamics."""
import sys
import os

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from _00_entry.mcp_server import main

if __name__ == "__main__":
    main()
