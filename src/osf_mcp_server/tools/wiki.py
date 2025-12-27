"""Get OSF wiki content tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

get_wiki_tool = types.Tool(
    name="get_wiki",
    description="""Get wiki pages from an OSF project.

OSF projects can have wiki pages with documentation, protocols, and notes.
Wiki content is in Markdown format.

Two modes:
1. List all wiki pages in a project
2. Get content of a specific wiki page

EXAMPLES:
- List wiki pages: project_id="abc12"
- Get specific page: wiki_id="xyz789"
- Get home page: project_id="abc12", page_name="home" """,
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The OSF project ID (to list wiki pages)",
            },
            "wiki_id": {
                "type": "string",
                "description": "Specific wiki page ID (to get content)",
            },
            "page_name": {
                "type": "string",
                "description": "Wiki page name to find (e.g., 'home')",
            },
        },
    },
)


async def handle_get_wiki(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle wiki requests."""
    try:
        project_id = arguments.get("project_id")
        wiki_id = arguments.get("wiki_id")
        page_name = arguments.get("page_name")

        async with OSFClient(settings) as client:
            # If wiki_id provided, get that specific page
            if wiki_id:
                logger.info(f"Getting wiki page: {wiki_id}")
                page = await client.get_wiki_page(wiki_id)
                content = await client.get_wiki_content(wiki_id)

                result = {
                    "id": page.id,
                    "name": page.name,
                    "date_modified": page.date_modified,
                    "url": page.url,
                    "content": content,
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            # If project_id provided, list pages
            if project_id:
                logger.info(f"Listing wiki pages for project: {project_id}")
                pages = await client.list_wiki_pages(project_id)

                # If page_name specified, find and return that page
                if page_name:
                    for page in pages:
                        if page.name.lower() == page_name.lower():
                            content = await client.get_wiki_content(page.id)
                            result = {
                                "id": page.id,
                                "name": page.name,
                                "date_modified": page.date_modified,
                                "url": page.url,
                                "content": content,
                            }
                            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

                    return [types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Wiki page '{page_name}' not found",
                            "available_pages": [p.name for p in pages],
                        }),
                    )]

                # Return list of pages
                results = []
                for page in pages:
                    results.append({
                        "id": page.id,
                        "name": page.name,
                        "date_modified": page.date_modified,
                        "url": page.url,
                    })

                response = {
                    "project_id": project_id,
                    "total_pages": len(results),
                    "pages": results,
                }

                logger.info(f"Found {len(results)} wiki pages")
                return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Either project_id or wiki_id is required",
                }),
            )]

    except Exception as e:
        logger.error(f"Get wiki error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
