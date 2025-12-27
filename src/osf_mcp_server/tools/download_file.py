"""Download OSF file tool."""

import json
import asyncio
import logging
from pathlib import Path
from typing import Any
from datetime import datetime
from dataclasses import dataclass
import mcp.types as types
import pymupdf4llm
from ..config import Settings
from ..osf_client import OSFClient

logger = logging.getLogger("osf-mcp-server")
settings = Settings()

# Track conversion status
conversion_statuses: dict[str, Any] = {}


@dataclass
class ConversionStatus:
    """Track the status of a file download/conversion."""
    file_id: str
    status: str  # 'downloading', 'converting', 'success', 'error'
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    file_path: str | None = None


download_file_tool = types.Tool(
    name="download_file",
    description="""Download a file from an OSF project and store it locally.

Downloads the file and converts PDFs to Markdown for easy reading.
Files are cached indefinitely for fast subsequent access.

Supported conversions:
- PDF → Markdown (using PyMuPDF)
- Text files → stored as-is
- Other formats → stored as binary

Use check_status=true to check on an in-progress download.

EXAMPLES:
- Download by file ID: file_id="abc123def"
- Check download status: file_id="abc123def", check_status=true""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_id": {
                "type": "string",
                "description": "The OSF file ID to download",
            },
            "check_status": {
                "type": "boolean",
                "description": "If true, only check download/conversion status",
                "default": False,
            },
        },
        "required": ["file_id"],
    },
)


def get_file_path(file_id: str, suffix: str = "") -> Path:
    """Get the absolute file path for a downloaded file."""
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path / f"{file_id}{suffix}"


def convert_pdf_to_markdown(file_id: str, pdf_path: Path) -> None:
    """Convert PDF to Markdown in a separate thread."""
    try:
        logger.info(f"Starting PDF conversion for {file_id}")
        markdown = pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)
        md_path = get_file_path(file_id, ".md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        status = conversion_statuses.get(file_id)
        if status:
            status.status = "success"
            status.completed_at = datetime.now()
            status.file_path = str(md_path)

        # Optionally clean up PDF after conversion
        # pdf_path.unlink()
        logger.info(f"PDF conversion completed for {file_id}")

    except Exception as e:
        logger.error(f"PDF conversion failed for {file_id}: {str(e)}")
        status = conversion_statuses.get(file_id)
        if status:
            status.status = "error"
            status.completed_at = datetime.now()
            status.error = str(e)


async def handle_download_file(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle file download requests."""
    try:
        file_id = arguments["file_id"]
        check_status = arguments.get("check_status", False)

        # Check status only
        if check_status:
            status = conversion_statuses.get(file_id)
            if not status:
                # Check if file already exists
                md_path = get_file_path(file_id, ".md")
                if md_path.exists():
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "success",
                            "message": "File is ready",
                            "file_path": str(md_path),
                            "resource_uri": f"file://{md_path}",
                        }),
                    )]
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "unknown",
                        "message": "No download in progress for this file",
                    }),
                )]

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": status.status,
                    "started_at": status.started_at.isoformat(),
                    "completed_at": status.completed_at.isoformat() if status.completed_at else None,
                    "error": status.error,
                    "file_path": status.file_path,
                    "message": f"File download/conversion {status.status}",
                }),
            )]

        # Check if already downloaded
        md_path = get_file_path(file_id, ".md")
        if md_path.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "message": "File already available",
                    "file_path": str(md_path),
                    "resource_uri": f"file://{md_path}",
                }),
            )]

        # Check if already in progress
        if file_id in conversion_statuses:
            status = conversion_statuses[file_id]
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": status.status,
                    "message": f"File download/conversion {status.status}",
                    "started_at": status.started_at.isoformat(),
                }),
            )]

        # Start new download
        logger.info(f"Starting download for file: {file_id}")

        async with OSFClient(settings) as client:
            # Get file metadata
            file_info = await client.get_file(file_id)

            # Initialize status
            conversion_statuses[file_id] = ConversionStatus(
                file_id=file_id,
                status="downloading",
                started_at=datetime.now(),
            )

            # Download file content
            content = await client.download_file(file_id)

            # Determine file extension and storage
            original_name = file_info.name
            content_type = file_info.content_type or ""

            if original_name.lower().endswith(".pdf") or "pdf" in content_type.lower():
                # Save as PDF and convert to Markdown
                pdf_path = get_file_path(file_id, ".pdf")
                with open(pdf_path, "wb") as f:
                    f.write(content)

                # Update status
                status = conversion_statuses[file_id]
                status.status = "converting"

                # Start conversion in background
                asyncio.create_task(
                    asyncio.to_thread(convert_pdf_to_markdown, file_id, pdf_path)
                )

                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "converting",
                        "message": "File downloaded, PDF conversion started",
                        "original_name": original_name,
                        "started_at": status.started_at.isoformat(),
                    }),
                )]

            else:
                # Store as-is (text or binary)
                ext = Path(original_name).suffix or ".bin"
                file_path = get_file_path(file_id, ext)

                mode = "wb" if isinstance(content, bytes) else "w"
                with open(file_path, mode) as f:
                    f.write(content)

                # Update status
                status = conversion_statuses[file_id]
                status.status = "success"
                status.completed_at = datetime.now()
                status.file_path = str(file_path)

                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "message": "File downloaded successfully",
                        "original_name": original_name,
                        "file_path": str(file_path),
                        "resource_uri": f"file://{file_path}",
                    }),
                )]

    except Exception as e:
        logger.error(f"Download file error: {e}")
        # Update status on error
        if "file_id" in arguments and arguments["file_id"] in conversion_statuses:
            status = conversion_statuses[arguments["file_id"]]
            status.status = "error"
            status.completed_at = datetime.now()
            status.error = str(e)

        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Error: {str(e)}",
            }),
        )]
