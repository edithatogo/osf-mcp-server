"""Tests for OSF search tools."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from osf_mcp_server.tools.search_projects import handle_search_projects
from osf_mcp_server.tools.search_registrations import handle_search_registrations
from osf_mcp_server.tools.search_preprints import handle_search_preprints


class TestSearchProjects:
    """Tests for search_projects tool."""

    @pytest.mark.asyncio
    async def test_search_projects_basic(self, mock_project):
        """Test basic project search."""
        with patch("osf_mcp_server.tools.search_projects.OSFClient") as MockClient:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_projects = AsyncMock(return_value=[mock_project])
            MockClient.return_value = mock_instance

            # Call handler
            result = await handle_search_projects({"query": "test"})

            # Verify
            assert len(result) == 1
            response = json.loads(result[0].text)
            assert response["total_results"] == 1
            assert response["projects"][0]["id"] == "abc12"
            assert response["projects"][0]["title"] == "Test Research Project"

    @pytest.mark.asyncio
    async def test_search_projects_with_filters(self, mock_project):
        """Test project search with filters."""
        with patch("osf_mcp_server.tools.search_projects.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_projects = AsyncMock(return_value=[mock_project])
            MockClient.return_value = mock_instance

            result = await handle_search_projects({
                "query": "psychology",
                "tags": ["experiment"],
                "category": "project",
                "max_results": 20,
            })

            response = json.loads(result[0].text)
            assert response["total_results"] == 1

    @pytest.mark.asyncio
    async def test_search_projects_empty_results(self):
        """Test project search with no results."""
        with patch("osf_mcp_server.tools.search_projects.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_projects = AsyncMock(return_value=[])
            MockClient.return_value = mock_instance

            result = await handle_search_projects({"query": "nonexistent"})

            response = json.loads(result[0].text)
            assert response["total_results"] == 0
            assert response["projects"] == []

    @pytest.mark.asyncio
    async def test_search_projects_error_handling(self):
        """Test project search error handling."""
        with patch("osf_mcp_server.tools.search_projects.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_projects = AsyncMock(side_effect=Exception("API Error"))
            MockClient.return_value = mock_instance

            result = await handle_search_projects({"query": "test"})

            assert "Error" in result[0].text


class TestSearchRegistrations:
    """Tests for search_registrations tool."""

    @pytest.mark.asyncio
    async def test_search_registrations_basic(self, mock_registration):
        """Test basic registration search."""
        with patch("osf_mcp_server.tools.search_registrations.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_registrations = AsyncMock(return_value=[mock_registration])
            MockClient.return_value = mock_instance

            result = await handle_search_registrations({"query": "cognitive"})

            response = json.loads(result[0].text)
            assert response["total_results"] == 1
            assert response["registrations"][0]["id"] == "reg123"
            assert "Pre-registered Study" in response["registrations"][0]["title"]


class TestSearchPreprints:
    """Tests for search_preprints tool."""

    @pytest.mark.asyncio
    async def test_search_preprints_basic(self, mock_preprint):
        """Test basic preprint search."""
        with patch("osf_mcp_server.tools.search_preprints.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_preprints = AsyncMock(return_value=[mock_preprint])
            MockClient.return_value = mock_instance

            result = await handle_search_preprints({"query": "machine learning"})

            response = json.loads(result[0].text)
            assert response["total_results"] == 1
            assert response["preprints"][0]["id"] == "pre456"

    @pytest.mark.asyncio
    async def test_search_preprints_with_provider(self, mock_preprint):
        """Test preprint search with provider filter."""
        with patch("osf_mcp_server.tools.search_preprints.OSFClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.search_preprints = AsyncMock(return_value=[mock_preprint])
            MockClient.return_value = mock_instance

            result = await handle_search_preprints({
                "query": "psychology",
                "provider": "psyarxiv",
            })

            response = json.loads(result[0].text)
            assert response["total_results"] == 1
