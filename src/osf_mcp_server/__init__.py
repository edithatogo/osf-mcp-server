"""
OSF MCP Server
==============

MCP server for Open Science Framework (OSF) - search projects, registrations,
preprints, and manage files.

Usage:
    osf-mcp-server [--storage-path PATH]

Environment Variables:
    OSF_TOKEN: Personal access token for authenticated access (optional)
    OSF_STORAGE_PATH: Path for downloaded files (default: ~/.osf-mcp-server/files)
    OSF_MAX_RESULTS: Maximum search results (default: 50)
    OSF_REQUEST_TIMEOUT: API timeout in seconds (default: 60)
"""

import asyncio
from .server import main as async_main


def main():
    """Entry point for the OSF MCP server."""
    asyncio.run(async_main())


__all__ = ["main"]
__version__ = "0.1.0"
