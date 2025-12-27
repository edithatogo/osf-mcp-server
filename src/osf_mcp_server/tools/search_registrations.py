"""Search OSF registrations tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

search_registrations_tool = types.Tool(
    name="search_registrations",
    description="""Search for registrations on the Open Science Framework (OSF).

Registrations are frozen, timestamped versions of OSF projects that create a permanent
record of research at a specific point in time. They are crucial for:

- Pre-registration of studies (before data collection)
- Registered Reports (peer-reviewed study designs)
- Archiving completed research with DOIs
- Ensuring research transparency and reproducibility

SEARCH TIPS:
- Search by study title or topic
- Registrations often have DOIs for citation
- Use this to find pre-registered studies in your field

EXAMPLES:
- Find psychology pre-registrations: query="pre-registration psychology"
- Search for specific methodology: query="fMRI"
- Find registered reports: query="registered report"

All registrations are public by design.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for registration title and description.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 10, max: 50)",
                "default": 10,
            },
        },
    },
)


async def handle_search_registrations(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle registration search requests."""
    try:
        query = arguments.get("query")
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)

        logger.info(f"Searching registrations: query='{query}'")

        async with OSFClient(settings) as client:
            registrations = await client.search_registrations(
                query=query,
                max_results=max_results,
            )

        results = []
        for reg in registrations:
            results.append({
                "id": reg.id,
                "title": reg.title,
                "description": reg.description,
                "date_registered": reg.date_registered,
                "registration_schema": reg.registration_schema,
                "doi": reg.doi,
                "url": reg.url,
                "resource_uri": f"osf://registration/{reg.id}",
            })

        response_data = {
            "total_results": len(results),
            "registrations": results,
        }

        logger.info(f"Found {len(results)} registrations")
        return [types.TextContent(type="text", text=json.dumps(response_data, indent=2))]

    except Exception as e:
        logger.error(f"Search registrations error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
