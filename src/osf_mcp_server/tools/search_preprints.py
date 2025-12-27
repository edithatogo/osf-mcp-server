"""Search OSF preprints tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

search_preprints_tool = types.Tool(
    name="search_preprints",
    description="""Search for preprints on OSF Preprints and partner services.

OSF hosts preprints from multiple disciplines through OSF Preprints and partner
preprint servers including:

PREPRINT PROVIDERS:
- osf: OSF Preprints (general)
- psyarxiv: Psychology
- socarxiv: Social Sciences
- engrxiv: Engineering
- biohackrxiv: Bioinformatics
- eartharxiv: Earth Sciences
- mediarxiv: Media Studies
- agrixiv: Agriculture
- and many more...

SEARCH TIPS:
- Search by title, abstract keywords
- Filter by provider for discipline-specific results
- Preprints often have DOIs

EXAMPLES:
- Find psychology preprints: query="cognitive bias", provider="psyarxiv"
- Search engineering papers: query="renewable energy", provider="engrxiv"
- General search: query="machine learning"

All preprints are publicly accessible.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for preprint title and abstract.",
            },
            "provider": {
                "type": "string",
                "description": "Preprint provider filter (e.g., 'psyarxiv', 'socarxiv', 'osf')",
            },
            "subjects": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by subject areas",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 10, max: 50)",
                "default": 10,
            },
        },
    },
)


async def handle_search_preprints(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle preprint search requests."""
    try:
        query = arguments.get("query")
        provider = arguments.get("provider")
        subjects = arguments.get("subjects")
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)

        logger.info(f"Searching preprints: query='{query}', provider={provider}")

        async with OSFClient(settings) as client:
            preprints = await client.search_preprints(
                query=query,
                provider=provider,
                subjects=subjects,
                max_results=max_results,
            )

        results = []
        for preprint in preprints:
            results.append({
                "id": preprint.id,
                "title": preprint.title,
                "description": preprint.description,
                "date_published": preprint.date_published,
                "doi": preprint.doi,
                "subjects": preprint.subjects,
                "license": preprint.license,
                "download_url": preprint.download_url,
                "url": preprint.url,
                "resource_uri": f"osf://preprint/{preprint.id}",
            })

        response_data = {
            "total_results": len(results),
            "preprints": results,
        }

        logger.info(f"Found {len(results)} preprints")
        return [types.TextContent(type="text", text=json.dumps(response_data, indent=2))]

    except Exception as e:
        logger.error(f"Search preprints error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
