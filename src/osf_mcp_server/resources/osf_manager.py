"""Resource management and storage for OSF files."""

from pathlib import Path
from typing import Any
import aiofiles
import logging
import mcp.types as types
from pydantic import AnyUrl
from ..config import Settings
from ..osf_client import OSFClient, OSFFile

logger = logging.getLogger("osf-mcp-server")


class OSFResourceManager:
    """Manages the storage, retrieval, and resource handling of OSF files."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the OSF resource management system."""
        self.settings = settings or Settings()
        self.storage_path = Path(self.settings.STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, file_id: str, suffix: str = "") -> Path:
        """Get the absolute file path for a stored file."""
        return self.storage_path / f"{file_id}{suffix}"

    async def has_file(self, file_id: str) -> bool:
        """Check if a file is available in storage."""
        # Check for any file with this ID
        for path in self.storage_path.glob(f"{file_id}.*"):
            return True
        return False

    async def list_files(self) -> list[str]:
        """List all stored file IDs."""
        logger.info(f"Listing files in {self.storage_path}")
        file_ids = set()
        for path in self.storage_path.glob("*"):
            if path.is_file():
                # Get ID without extension
                file_ids.add(path.stem)
        logger.info(f"Found {len(file_ids)} files")
        return list(file_ids)

    async def list_resources(self) -> list[types.Resource]:
        """List all files as MCP resources."""
        file_ids = await self.list_files()
        resources = []

        for file_id in file_ids:
            # Find the actual file path
            file_path = None
            for path in self.storage_path.glob(f"{file_id}.*"):
                file_path = path
                break

            if file_path:
                resources.append(
                    types.Resource(
                        uri=AnyUrl(f"file://{str(file_path)}"),
                        name=file_path.name,
                        description=f"OSF file: {file_id}",
                        mimeType=self._get_mime_type(file_path),
                    )
                )

        logger.info(f"Found {len(resources)} resources")
        return resources

    async def get_file_content(self, file_id: str) -> str:
        """Get the text content of a stored file."""
        # Find file with any extension
        file_path = None
        for path in self.storage_path.glob(f"{file_id}.*"):
            file_path = path
            break

        if not file_path:
            raise ValueError(f"File {file_id} not found in storage")

        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()

    async def store_file(
        self,
        file_id: str,
        content: bytes | str,
        suffix: str = "",
    ) -> Path:
        """Store file content.

        Args:
            file_id: Unique file identifier
            content: File content (bytes or string)
            suffix: File extension

        Returns:
            Path to stored file
        """
        file_path = self._get_file_path(file_id, suffix)

        if isinstance(content, bytes):
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        else:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

        logger.info(f"Stored file: {file_path}")
        return file_path

    async def delete_file(self, file_id: str) -> bool:
        """Delete a stored file."""
        deleted = False
        for path in self.storage_path.glob(f"{file_id}.*"):
            path.unlink()
            deleted = True
            logger.info(f"Deleted file: {path}")
        return deleted

    def get_storage_info(self) -> dict[str, Any]:
        """Get storage statistics."""
        total_size = 0
        file_count = 0

        for path in self.storage_path.glob("*"):
            if path.is_file():
                total_size += path.stat().st_size
                file_count += 1

        return {
            "storage_path": str(self.storage_path),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_human": self._format_size(total_size),
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def _get_mime_type(path: Path) -> str:
        """Get MIME type for a file."""
        suffix = path.suffix.lower()
        mime_types = {
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".json": "application/json",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".xml": "application/xml",
            ".html": "text/html",
        }
        return mime_types.get(suffix, "application/octet-stream")
