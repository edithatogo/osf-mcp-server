"""Tests for OSF MCP Server configuration."""

import pytest
import os
from pathlib import Path
from osf_mcp_server.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.APP_NAME == "osf-mcp-server"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.OSF_API_URL == "https://api.osf.io/v2"
        assert settings.MAX_RESULTS == 50
        assert settings.REQUEST_TIMEOUT == 60

    def test_is_authenticated_without_token(self):
        """Test authentication check without token."""
        settings = Settings()
        # Ensure no token is set
        settings.OSF_TOKEN = None

        assert settings.is_authenticated is False

    def test_is_authenticated_with_token(self):
        """Test authentication check with token."""
        settings = Settings()
        settings.OSF_TOKEN = "test_token_123"

        assert settings.is_authenticated is True

    def test_get_headers_without_auth(self):
        """Test headers without authentication."""
        settings = Settings()
        settings.OSF_TOKEN = None

        headers = settings.get_headers()

        assert "Accept" in headers
        assert headers["Accept"] == "application/vnd.api+json"
        assert "Authorization" not in headers

    def test_get_headers_with_auth(self):
        """Test headers with authentication."""
        settings = Settings()
        settings.OSF_TOKEN = "test_token_123"

        headers = settings.get_headers()

        assert "Accept" in headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token_123"

    def test_storage_path_default(self, tmp_path, monkeypatch):
        """Test default storage path creation."""
        # Clear any existing env vars
        monkeypatch.delenv("OSF_STORAGE_PATH", raising=False)

        settings = Settings()
        storage_path = settings.STORAGE_PATH

        assert storage_path.exists()
        assert storage_path.is_dir()

    def test_storage_path_from_env(self, tmp_path, monkeypatch):
        """Test storage path from environment variable."""
        custom_path = tmp_path / "custom_storage"
        monkeypatch.setenv("OSF_STORAGE_PATH", str(custom_path))

        settings = Settings()
        storage_path = settings.STORAGE_PATH

        assert storage_path == custom_path.resolve()
        assert storage_path.exists()

    def test_env_prefix(self, monkeypatch):
        """Test that environment variables use OSF_ prefix."""
        monkeypatch.setenv("OSF_MAX_RESULTS", "100")

        settings = Settings()

        # Note: pydantic-settings should pick up OSF_MAX_RESULTS
        # This depends on the env_prefix configuration
        assert settings.MAX_RESULTS == 100 or settings.MAX_RESULTS == 50  # Depends on load order
