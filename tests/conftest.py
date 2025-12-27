"""Pytest configuration and fixtures for OSF MCP Server tests."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from osf_mcp_server.config import Settings
from osf_mcp_server.osf_client import (
    OSFClient,
    OSFProject,
    OSFRegistration,
    OSFPreprint,
    OSFFile,
)


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Create mock settings with temporary storage path."""
    settings = Settings()
    # Override storage path to use temp directory
    settings._storage_path_override = tmp_path / "osf_files"
    return settings


@pytest.fixture
def mock_project() -> OSFProject:
    """Create a mock OSF project."""
    return OSFProject(
        id="abc12",
        title="Test Research Project",
        description="A test project for unit testing",
        date_created="2024-01-15T10:00:00Z",
        date_modified="2024-06-20T15:30:00Z",
        public=True,
        category="project",
        tags=["test", "research", "psychology"],
        contributors=["user123", "user456"],
        url="https://osf.io/abc12/",
        api_url="https://api.osf.io/v2/nodes/abc12/",
        files_url="https://api.osf.io/v2/nodes/abc12/files/",
        wiki_url="https://api.osf.io/v2/nodes/abc12/wikis/",
    )


@pytest.fixture
def mock_registration() -> OSFRegistration:
    """Create a mock OSF registration."""
    return OSFRegistration(
        id="reg123",
        title="Pre-registered Study on Cognitive Bias",
        description="A pre-registered replication study",
        date_registered="2024-02-01T12:00:00Z",
        registration_schema="OSF Preregistration",
        public=True,
        doi="10.17605/OSF.IO/REG123",
        url="https://osf.io/reg123/",
        api_url="https://api.osf.io/v2/registrations/reg123/",
    )


@pytest.fixture
def mock_preprint() -> OSFPreprint:
    """Create a mock OSF preprint."""
    return OSFPreprint(
        id="pre456",
        title="Machine Learning in Psychology Research",
        description="A review of ML applications",
        date_published="2024-03-15T09:00:00Z",
        doi="10.31234/osf.io/pre456",
        subjects=["Psychology", "Methodology"],
        license="CC-BY 4.0",
        download_url="https://osf.io/pre456/download/",
        url="https://osf.io/pre456/",
        api_url="https://api.osf.io/v2/preprints/pre456/",
    )


@pytest.fixture
def mock_file() -> OSFFile:
    """Create a mock OSF file."""
    return OSFFile(
        id="file789",
        name="analysis_script.py",
        kind="file",
        path="/analysis_script.py",
        size=15420,
        date_modified="2024-05-10T14:20:00Z",
        content_type="text/x-python",
        download_url="https://files.osf.io/v1/resources/abc12/providers/osfstorage/file789",
        provider="osfstorage",
    )


@pytest.fixture
def mock_pdf_file() -> OSFFile:
    """Create a mock PDF file."""
    return OSFFile(
        id="pdf001",
        name="paper.pdf",
        kind="file",
        path="/paper.pdf",
        size=1024000,
        date_modified="2024-04-01T10:00:00Z",
        content_type="application/pdf",
        download_url="https://files.osf.io/v1/resources/abc12/providers/osfstorage/pdf001",
        provider="osfstorage",
    )


@pytest.fixture
def mock_osf_client(mock_project, mock_registration, mock_preprint, mock_file):
    """Create a mock OSF client."""
    client = MagicMock(spec=OSFClient)

    # Configure async methods
    client.search_projects = AsyncMock(return_value=[mock_project])
    client.get_project = AsyncMock(return_value=mock_project)
    client.search_registrations = AsyncMock(return_value=[mock_registration])
    client.get_registration = AsyncMock(return_value=mock_registration)
    client.search_preprints = AsyncMock(return_value=[mock_preprint])
    client.get_preprint = AsyncMock(return_value=mock_preprint)
    client.list_project_files = AsyncMock(return_value=[mock_file])
    client.get_file = AsyncMock(return_value=mock_file)
    client.download_file = AsyncMock(return_value=b"file content here")
    client.get_project_contributors = AsyncMock(
        return_value=[
            {
                "id": "user123",
                "bibliographic": True,
                "permission": "admin",
                "full_name": "Test User",
            }
        ]
    )

    return client


@pytest.fixture
def mock_api_response_project():
    """Create mock API response for a project."""
    return {
        "data": {
            "id": "abc12",
            "type": "nodes",
            "attributes": {
                "title": "Test Research Project",
                "description": "A test project",
                "category": "project",
                "public": True,
                "tags": ["test"],
                "date_created": "2024-01-15T10:00:00Z",
                "date_modified": "2024-06-20T15:30:00Z",
            },
            "links": {
                "self": "https://api.osf.io/v2/nodes/abc12/",
                "html": "https://osf.io/abc12/",
            },
            "relationships": {
                "files": {
                    "links": {
                        "related": {
                            "href": "https://api.osf.io/v2/nodes/abc12/files/"
                        }
                    }
                },
                "contributors": {
                    "data": [{"id": "user123", "type": "contributors"}]
                },
            },
        }
    }


@pytest.fixture
def mock_api_response_files():
    """Create mock API response for file listing."""
    return {
        "data": [
            {
                "id": "file789",
                "type": "files",
                "attributes": {
                    "name": "analysis_script.py",
                    "kind": "file",
                    "path": "/analysis_script.py",
                    "materialized_path": "/analysis_script.py",
                    "size": 15420,
                    "content_type": "text/x-python",
                    "date_modified": "2024-05-10T14:20:00Z",
                    "provider": "osfstorage",
                },
                "links": {
                    "download": "https://files.osf.io/v1/resources/abc12/providers/osfstorage/file789",
                },
            }
        ]
    }
