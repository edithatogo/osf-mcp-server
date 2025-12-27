"""Update OSF project tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

update_project_tool = types.Tool(
    name="update_project",
    description="""Update an existing OSF project's metadata.

REQUIRES AUTHENTICATION: You must have OSF_TOKEN set and write access to the project.

You can update:
- Title
- Description
- Public/private status
- Tags

Only specify the fields you want to change.

EXAMPLES:
- Update title: project_id="abc12", title="New Title"
- Make public: project_id="abc12", public=true
- Update multiple fields: project_id="abc12", title="Updated", description="New desc"
- Replace tags: project_id="abc12", tags=["v2", "final"]""",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The OSF project ID to update",
            },
            "title": {
                "type": "string",
                "description": "New project title",
            },
            "description": {
                "type": "string",
                "description": "New project description",
            },
            "public": {
                "type": "boolean",
                "description": "New public/private status",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "New project tags (replaces existing)",
            },
        },
        "required": ["project_id"],
    },
)


async def handle_update_project(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle update project requests."""
    try:
        if not settings.is_authenticated:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Authentication required",
                    "message": "Set OSF_TOKEN environment variable to update projects",
                }),
            )]

        project_id = arguments["project_id"]
        title = arguments.get("title")
        description = arguments.get("description")
        public = arguments.get("public")
        tags = arguments.get("tags")

        # Check if any updates provided
        if all(v is None for v in [title, description, public, tags]):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "No updates provided",
                    "message": "Specify at least one field to update (title, description, public, tags)",
                }),
            )]

        logger.info(f"Updating project: {project_id}")

        async with OSFClient(settings) as client:
            project = await client.update_project(
                project_id=project_id,
                title=title,
                description=description,
                public=public,
                tags=tags,
            )

        result = {
            "status": "success",
            "message": "Project updated successfully",
            "project": {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "category": project.category,
                "public": project.public,
                "tags": project.tags,
                "url": project.url,
                "date_modified": project.date_modified,
                "resource_uri": f"osf://project/{project.id}",
            },
        }

        logger.info(f"Updated project: {project.id}")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Update project error: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": str(e),
            }),
        )]
