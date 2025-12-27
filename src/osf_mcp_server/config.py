"""Configuration settings for the OSF MCP server."""

import sys
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Server configuration settings for OSF MCP Server."""

    APP_NAME: str = "osf-mcp-server"
    APP_VERSION: str = "0.1.0"

    # OSF API Configuration
    OSF_API_URL: str = "https://api.osf.io/v2"
    OSF_TOKEN: str | None = None  # Optional - for authenticated access

    # Request settings
    MAX_RESULTS: int = 50
    BATCH_SIZE: int = 20
    REQUEST_TIMEOUT: int = 60

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    model_config = SettingsConfigDict(
        # Note: No env_prefix since field names already include OSF_ prefix
        # e.g., OSF_TOKEN field maps directly to OSF_TOKEN env var
        extra="allow"
    )

    @property
    def is_authenticated(self) -> bool:
        """Check if OSF token is configured for authenticated access."""
        return bool(self.OSF_TOKEN)

    @property
    def STORAGE_PATH(self) -> Path:
        """Get the resolved storage path and ensure it exists.

        Returns:
            Path: The absolute storage path.
        """
        path = (
            self._get_storage_path_from_args()
            or self._get_storage_path_from_env()
            or Path.home() / ".osf-mcp-server" / "files"
        )
        path = path.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_storage_path_from_env(self) -> Path | None:
        """Get storage path from environment variable."""
        env_path = os.environ.get("OSF_STORAGE_PATH")
        if env_path:
            try:
                return Path(env_path).resolve()
            except (TypeError, ValueError, OSError) as e:
                logger.warning(f"Invalid OSF_STORAGE_PATH: {e}")
        return None

    def _get_storage_path_from_args(self) -> Path | None:
        """Extract storage path from command line arguments.

        Returns:
            Path | None: The storage path if specified in arguments, None otherwise.
        """
        args = sys.argv[1:]

        if len(args) < 2:
            return None

        try:
            storage_path_index = args.index("--storage-path")
        except ValueError:
            return None

        if storage_path_index + 1 >= len(args):
            return None

        try:
            path = Path(args[storage_path_index + 1])
            return path.resolve()
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid storage path format: {e}")
        except OSError as e:
            logger.warning(f"Invalid storage path: {e}")

        return None

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for OSF API requests.

        Returns:
            dict: Headers including auth token if configured.
        """
        headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }
        if self.OSF_TOKEN:
            headers["Authorization"] = f"Bearer {self.OSF_TOKEN}"
        return headers
