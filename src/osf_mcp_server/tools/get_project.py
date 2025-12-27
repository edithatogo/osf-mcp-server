"""Get OSF project details tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

get_project_tool = types.Tool(
    name="get_project",
    description="""Get detailed information about a specific OSF project.

Returns comprehensive project metadata including:
- Title and description
- Contributors (authors)
- Tags and category
- Creation and modification dates
- Links to files, wiki, and registrations

Use this after searching to get full details about a project of interest.

EXAMPLES:
- Get project by ID: project_id="abc12"
- Include contributors: project_id="abc12", include_contributors=true""",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The OSF project ID (e.g., 'abc12' from osf.io/abc12)",
            },
            "include_contributors": {
                "type": "boolean",
                "description": "Include full contributor details (default: true)",
                "default": True,
            },
        },
        "required": ["project_id"],
    },
)


async def handle_get_project(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle get project requests."""
    try:
        project_id = arguments["project_id"]
        include_contributors = arguments.get("include_contributors", True)

        logger.info(f"Getting project: {project_id}")

        async with OSFClient(settings) as client:
            project = await client.get_project(project_id)

            # Get contributors if requested
            contributors = []
            if include_contributors:
                try:
                    contributors = await client.get_project_contributors(project_id)
                except Exception as e:
                    logger.warning(f"Could not fetch contributors: {e}")

        result = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "category": project.category,
            "tags": project.tags,
            "public": project.public,
            "date_created": project.date_created,
            "date_modified": project.date_modified,
            "url": project.url,
            "files_url": project.files_url,
            "wiki_url": project.wiki_url,
            "contributors": contributors,
            "resource_uri": f"osf://project/{project.id}",
        }

        logger.info(f"Retrieved project: {project.title}")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Get project error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
