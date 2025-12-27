"""List OSF project files tool."""

import json
import logging
from typing import Any
import mcp.types as types
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

list_files_tool = types.Tool(
    name="list_files",
    description="""List files and folders in an OSF project.

OSF projects can have files stored in multiple storage providers:
- osfstorage: Default OSF storage
- github: Connected GitHub repositories
- googledrive: Connected Google Drive
- dropbox: Connected Dropbox
- figshare: Connected Figshare
- and others...

Returns file metadata including:
- File/folder name and path
- File size and type
- Last modified date
- Download URL

EXAMPLES:
- List root files: project_id="abc12"
- List from specific path: project_id="abc12", path="/data/"
- List from GitHub: project_id="abc12", provider="github" """,
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The OSF project ID",
            },
            "path": {
                "type": "string",
                "description": "Path within the project (default: root '/')",
                "default": "/",
            },
            "provider": {
                "type": "string",
                "description": "Storage provider (default: 'osfstorage')",
                "default": "osfstorage",
            },
        },
        "required": ["project_id"],
    },
)


async def handle_list_files(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle list files requests."""
    try:
        project_id = arguments["project_id"]
        path = arguments.get("path", "/")
        provider = arguments.get("provider", "osfstorage")

        logger.info(f"Listing files: project={project_id}, path={path}, provider={provider}")

        async with OSFClient(settings) as client:
            files = await client.list_project_files(
                project_id=project_id,
                path=path,
                provider=provider,
            )

        results = []
        for file in files:
            results.append({
                "id": file.id,
                "name": file.name,
                "kind": file.kind,
                "path": file.path,
                "size": file.size,
                "size_human": _format_size(file.size) if file.size else None,
                "content_type": file.content_type,
                "date_modified": file.date_modified,
                "download_url": file.download_url,
                "provider": file.provider,
                "resource_uri": f"osf://file/{file.id}",
            })

        response_data = {
            "project_id": project_id,
            "path": path,
            "provider": provider,
            "total_items": len(results),
            "files": results,
        }

        logger.info(f"Found {len(results)} files/folders")
        return [types.TextContent(type="text", text=json.dumps(response_data, indent=2))]

    except Exception as e:
        logger.error(f"List files error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def _format_size(size_bytes: int | None) -> str:
    """Format file size in human-readable format."""
    if size_bytes is None:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
