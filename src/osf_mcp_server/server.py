"""
OSF MCP Server
==============

This module implements an MCP server for interacting with the Open Science Framework (OSF).
"""

import logging
from typing import Any
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server

from .config import Settings
from .tools import (
    # Search tools
    search_projects_tool, handle_search_projects,
    search_registrations_tool, handle_search_registrations,
    search_preprints_tool, handle_search_preprints,
    # Project tools
    get_project_tool, handle_get_project,
    create_project_tool, handle_create_project,
    update_project_tool, handle_update_project,
    # File tools
    list_files_tool, handle_list_files,
    download_file_tool, handle_download_file,
    read_file_tool, handle_read_file,
    # Wiki tools
    get_wiki_tool, handle_get_wiki,
    # DOI tools
    resolve_doi_tool, handle_resolve_doi,
)

settings = Settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("osf-mcp-server")
logger.setLevel(logging.INFO)

# Create MCP server
server = Server(settings.APP_NAME)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available OSF research tools."""
    tools = [
        # Search tools
        search_projects_tool,
        search_registrations_tool,
        search_preprints_tool,
        # Project tools
        get_project_tool,
        list_files_tool,
        download_file_tool,
        read_file_tool,
        # Wiki tools
        get_wiki_tool,
        # DOI tools
        resolve_doi_tool,
    ]

    # Add write tools only if authenticated
    if settings.is_authenticated:
        tools.extend([
            create_project_tool,
            update_project_tool,
        ])

    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls for OSF research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")

    try:
        # Search tools
        if name == "search_projects":
            return await handle_search_projects(arguments)
        elif name == "search_registrations":
            return await handle_search_registrations(arguments)
        elif name == "search_preprints":
            return await handle_search_preprints(arguments)

        # Project tools
        elif name == "get_project":
            return await handle_get_project(arguments)
        elif name == "create_project":
            return await handle_create_project(arguments)
        elif name == "update_project":
            return await handle_update_project(arguments)

        # File tools
        elif name == "list_files":
            return await handle_list_files(arguments)
        elif name == "download_file":
            return await handle_download_file(arguments)
        elif name == "read_file":
            return await handle_read_file(arguments)

        # Wiki tools
        elif name == "get_wiki":
            return await handle_get_wiki(arguments)

        # DOI tools
        elif name == "resolve_doi":
            return await handle_resolve_doi(arguments)

        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

    except Exception as e:
        logger.error(f"Tool error ({name}): {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the OSF MCP server."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Storage path: {settings.STORAGE_PATH}")
    logger.info(f"Authenticated: {settings.is_authenticated}")

    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.APP_NAME,
                server_version=settings.APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
