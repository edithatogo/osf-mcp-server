"""Read downloaded OSF file tool."""

import json
import logging
from pathlib import Path
from typing import Any
import aiofiles
import mcp.types as types
from ..config import Settings

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

read_file_tool = types.Tool(
    name="read_file",
    description="""Read the content of a previously downloaded OSF file.

Returns the file content as text. For PDFs, returns the converted Markdown.
Use download_file first to download and cache the file.

EXAMPLES:
- Read file by ID: file_id="abc123def"
- Read with line limit: file_id="abc123def", max_lines=100""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_id": {
                "type": "string",
                "description": "The OSF file ID (must be previously downloaded)",
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to return (0 = all)",
                "default": 0,
            },
        },
        "required": ["file_id"],
    },
)


async def handle_read_file(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle read file requests."""
    try:
        file_id = arguments["file_id"]
        max_lines = arguments.get("max_lines", 0)

        logger.info(f"Reading file: {file_id}")

        storage_path = Path(settings.STORAGE_PATH)

        # Look for the file with various extensions
        file_path = None
        for ext in [".md", ".txt", ".json", ".csv", ".xml", ".html", ""]:
            candidate = storage_path / f"{file_id}{ext}"
            if candidate.exists():
                file_path = candidate
                break

        if not file_path:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"File {file_id} not found in storage. Use download_file first.",
                    "storage_path": str(storage_path),
                }),
            )]

        # Read file content
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()

        # Limit lines if requested
        if max_lines > 0:
            lines = content.split("\n")
            if len(lines) > max_lines:
                content = "\n".join(lines[:max_lines])
                content += f"\n\n... (truncated, showing {max_lines} of {len(lines)} lines)"

        result = {
            "file_id": file_id,
            "file_path": str(file_path),
            "file_type": file_path.suffix,
            "size_bytes": file_path.stat().st_size,
            "content": content,
        }

        logger.info(f"Read file: {file_path} ({len(content)} chars)")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except UnicodeDecodeError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": f"File {file_id} is binary and cannot be read as text",
                "suggestion": "This file format is not supported for text reading",
            }),
        )]
    except Exception as e:
        logger.error(f"Read file error: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
