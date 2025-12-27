"""Resolve DOI to OSF resource tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

resolve_doi_tool = types.Tool(
    name="resolve_doi",
    description="""Resolve a DOI to find the corresponding OSF resource.

OSF assigns DOIs to:
- Registrations (permanent, citable)
- Preprints (for citation)
- Some projects (if minted)

Given a DOI, this tool will:
1. Extract the OSF resource ID
2. Determine the resource type (project, registration, preprint)
3. Return the resource details

SUPPORTED DOI FORMATS:
- Full URL: https://doi.org/10.17605/OSF.IO/ABC12
- DOI string: 10.17605/OSF.IO/ABC12
- OSF-style: OSF.IO/ABC12

EXAMPLES:
- Resolve DOI: doi="10.17605/OSF.IO/ABC12"
- From URL: doi="https://doi.org/10.17605/OSF.IO/XYZ789" """,
    inputSchema={
        "type": "object",
        "properties": {
            "doi": {
                "type": "string",
                "description": "DOI to resolve (full URL or DOI string)",
            },
        },
        "required": ["doi"],
    },
)


async def handle_resolve_doi(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle DOI resolution requests."""
    try:
        doi = arguments["doi"]
        logger.info(f"Resolving DOI: {doi}")

        async with OSFClient(settings) as client:
            result = await client.resolve_doi(doi)

        response = {
            "doi": doi,
            "resolved": True,
            "resource_type": result["type"],
            "resource_id": result["id"],
            "title": result["title"],
            "url": result["url"],
            "resource_uri": f"osf://{result['type']}/{result['id']}",
        }

        logger.info(f"Resolved DOI to {result['type']}: {result['id']}")
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except ValueError as e:
        logger.warning(f"Could not resolve DOI: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "doi": arguments.get("doi", ""),
                "resolved": False,
                "error": str(e),
                "suggestion": "Make sure this is a valid OSF DOI (format: 10.17605/OSF.IO/XXXXX)",
            }),
        )]
    except Exception as e:
        logger.error(f"Resolve DOI error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
