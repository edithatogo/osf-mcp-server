"""Create OSF project tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

create_project_tool = types.Tool(
    name="create_project",
    description="""Create a new project on the Open Science Framework.

REQUIRES AUTHENTICATION: You must have OSF_TOKEN set to use this tool.

Creates a new OSF project with the specified attributes. Projects can be:
- Public (visible to everyone)
- Private (only visible to contributors)

CATEGORIES:
- project: Standard research project
- component: Sub-project/component
- data: Data repository
- analysis: Analysis project
- software: Code/software project

EXAMPLES:
- Create public project: title="My Research", public=true
- Create private project with tags: title="Lab Notes", tags=["internal", "2024"]
- Create data project: title="Dataset v1", category="data", public=true""",
    inputSchema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Project title (required)",
            },
            "description": {
                "type": "string",
                "description": "Project description",
            },
            "public": {
                "type": "boolean",
                "description": "Whether the project is public (default: false)",
                "default": False,
            },
            "category": {
                "type": "string",
                "enum": ["project", "component", "data", "analysis", "software"],
                "description": "Project category (default: 'project')",
                "default": "project",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Project tags for discoverability",
            },
        },
        "required": ["title"],
    },
)


async def handle_create_project(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle create project requests."""
    try:
        if not settings.is_authenticated:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Authentication required",
                    "message": "Set OSF_TOKEN environment variable to create projects",
                }),
            )]

        title = arguments["title"]
        description = arguments.get("description")
        public = arguments.get("public", False)
        category = arguments.get("category", "project")
        tags = arguments.get("tags")

        logger.info(f"Creating project: title='{title}', public={public}")

        async with OSFClient(settings) as client:
            project = await client.create_project(
                title=title,
                description=description,
                public=public,
                category=category,
                tags=tags,
            )

        result = {
            "status": "success",
            "message": "Project created successfully",
            "project": {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "category": project.category,
                "public": project.public,
                "tags": project.tags,
                "url": project.url,
                "date_created": project.date_created,
                "resource_uri": f"osf://project/{project.id}",
            },
        }

        logger.info(f"Created project: {project.id}")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Create project error: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": str(e),
            }),
        )]
