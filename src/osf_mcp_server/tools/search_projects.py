"""Search OSF projects tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

search_projects_tool = types.Tool(
    name="search_projects",
    description="""Search for projects on the Open Science Framework (OSF).

OSF is a free, open platform for research collaboration. Projects can contain files,
wiki pages, registrations, and integrations with other research tools.

SEARCH TIPS:
- Use specific keywords related to your research topic
- Filter by tags for more precise results
- Use category filter to narrow down to specific project types

CATEGORIES:
- project: Top-level research projects
- component: Sub-projects or components
- data: Data-focused projects
- analysis: Analysis projects
- software: Software/code projects

EXAMPLES:
- Search for machine learning projects: query="machine learning"
- Search for psychology studies: query="psychology", tags=["experiment"]
- Find open data projects: query="dataset", category="data"

NOTE: Without authentication, only public projects are returned.
With OSF_TOKEN set, you can also search your private projects.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for project title and description. Use specific research terms.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by project tags (e.g., ['psychology', 'open-data'])",
            },
            "category": {
                "type": "string",
                "enum": ["project", "component", "data", "analysis", "software"],
                "description": "Filter by project category type.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 10, max: 50)",
                "default": 10,
            },
        },
    },
)


async def handle_search_projects(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle project search requests."""
    try:
        query = arguments.get("query")
        tags = arguments.get("tags")
        category = arguments.get("category")
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)

        logger.info(f"Searching projects: query='{query}', tags={tags}, category={category}")

        async with OSFClient(settings) as client:
            projects = await client.search_projects(
                query=query,
                tags=tags,
                category=category,
                max_results=max_results,
            )

        results = []
        for project in projects:
            results.append({
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "category": project.category,
                "tags": project.tags,
                "public": project.public,
                "date_created": project.date_created,
                "date_modified": project.date_modified,
                "url": project.url,
                "resource_uri": f"osf://project/{project.id}",
            })

        response_data = {
            "total_results": len(results),
            "authenticated": settings.is_authenticated,
            "projects": results,
        }

        logger.info(f"Found {len(results)} projects")
        return [types.TextContent(type="text", text=json.dumps(response_data, indent=2))]

    except Exception as e:
        logger.error(f"Search projects error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
