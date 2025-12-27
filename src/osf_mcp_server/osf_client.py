"""OSF API Client - Async wrapper for Open Science Framework API v2."""

import httpx
import logging
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from .config import Settings

logger = logging.getLogger("osf-mcp-server")


@dataclass
class OSFProject:
    """Represents an OSF project/node."""
    id: str
    title: str
    description: str | None
    date_created: str
    date_modified: str
    public: bool
    category: str
    tags: list[str]
    contributors: list[str]
    url: str
    api_url: str
    files_url: str | None
    wiki_url: str | None


@dataclass
class OSFRegistration:
    """Represents an OSF registration."""
    id: str
    title: str
    description: str | None
    date_registered: str
    registration_schema: str
    public: bool
    doi: str | None
    url: str
    api_url: str


@dataclass
class OSFPreprint:
    """Represents an OSF preprint."""
    id: str
    title: str
    description: str | None
    date_published: str
    doi: str | None
    subjects: list[str]
    license: str | None
    download_url: str | None
    url: str
    api_url: str


@dataclass
class OSFFile:
    """Represents an OSF file."""
    id: str
    name: str
    kind: str  # 'file' or 'folder'
    path: str
    size: int | None
    date_modified: str | None
    content_type: str | None
    download_url: str | None
    provider: str


@dataclass
class OSFWikiPage:
    """Represents an OSF wiki page."""
    id: str
    name: str
    content: str
    date_modified: str
    url: str


class OSFClient:
    """Async client for OSF API v2."""

    def __init__(self, settings: Settings | None = None):
        """Initialize OSF client.

        Args:
            settings: Optional settings object. Creates new one if not provided.
        """
        self.settings = settings or Settings()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.settings.OSF_API_URL,
            headers=self.settings.get_headers(),
            timeout=self.settings.REQUEST_TIMEOUT,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating one if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.OSF_API_URL,
                headers=self.settings.get_headers(),
                timeout=self.settings.REQUEST_TIMEOUT,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make GET request to OSF API.

        Args:
            endpoint: API endpoint (e.g., '/nodes/')
            params: Query parameters

        Returns:
            JSON response data
        """
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def _post(self, endpoint: str, data: dict) -> dict[str, Any]:
        """Make POST request to OSF API.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            JSON response data
        """
        response = await self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    async def _patch(self, endpoint: str, data: dict) -> dict[str, Any]:
        """Make PATCH request to OSF API.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            JSON response data
        """
        response = await self.client.patch(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    async def _delete(self, endpoint: str) -> bool:
        """Make DELETE request to OSF API.

        Args:
            endpoint: API endpoint

        Returns:
            True if successful
        """
        response = await self.client.delete(endpoint)
        response.raise_for_status()
        return True

    # =====================
    # PROJECT / NODE METHODS
    # =====================

    async def search_projects(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        max_results: int = 10,
    ) -> list[OSFProject]:
        """Search for OSF projects.

        Args:
            query: Search query for title/description
            tags: Filter by tags
            category: Filter by category (project, component, etc.)
            max_results: Maximum results to return

        Returns:
            List of matching projects
        """
        params: dict[str, Any] = {
            "page[size]": min(max_results, self.settings.MAX_RESULTS),
        }

        if query:
            params["filter[title][icontains]"] = query

        if tags:
            for tag in tags:
                params["filter[tags]"] = tag

        if category:
            params["filter[category]"] = category

        # Only show public projects for unauthenticated requests
        if not self.settings.is_authenticated:
            params["filter[public]"] = "true"

        response = await self._get("/nodes/", params=params)
        return self._parse_projects(response.get("data", []))

    async def get_project(self, project_id: str) -> OSFProject:
        """Get a specific project by ID.

        Args:
            project_id: OSF project ID

        Returns:
            Project details
        """
        response = await self._get(f"/nodes/{project_id}/")
        projects = self._parse_projects([response.get("data", {})])
        if not projects:
            raise ValueError(f"Project {project_id} not found")
        return projects[0]

    async def get_user_projects(self, max_results: int = 20) -> list[OSFProject]:
        """Get current user's projects (requires authentication).

        Args:
            max_results: Maximum results to return

        Returns:
            List of user's projects
        """
        if not self.settings.is_authenticated:
            raise ValueError("Authentication required to get user projects")

        params = {"page[size]": min(max_results, self.settings.MAX_RESULTS)}
        response = await self._get("/users/me/nodes/", params=params)
        return self._parse_projects(response.get("data", []))

    async def create_project(
        self,
        title: str,
        description: str | None = None,
        public: bool = False,
        category: str = "project",
        tags: list[str] | None = None,
    ) -> OSFProject:
        """Create a new OSF project.

        Args:
            title: Project title
            description: Project description
            public: Whether project is public
            category: Project category
            tags: Project tags

        Returns:
            Created project
        """
        if not self.settings.is_authenticated:
            raise ValueError("Authentication required to create projects")

        data = {
            "data": {
                "type": "nodes",
                "attributes": {
                    "title": title,
                    "category": category,
                    "public": public,
                },
            }
        }

        if description:
            data["data"]["attributes"]["description"] = description

        if tags:
            data["data"]["attributes"]["tags"] = tags

        response = await self._post("/nodes/", data)
        projects = self._parse_projects([response.get("data", {})])
        return projects[0]

    async def update_project(
        self,
        project_id: str,
        title: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        tags: list[str] | None = None,
    ) -> OSFProject:
        """Update an existing OSF project.

        Args:
            project_id: Project ID to update
            title: New title
            description: New description
            public: New public status
            tags: New tags

        Returns:
            Updated project
        """
        if not self.settings.is_authenticated:
            raise ValueError("Authentication required to update projects")

        attributes = {}
        if title is not None:
            attributes["title"] = title
        if description is not None:
            attributes["description"] = description
        if public is not None:
            attributes["public"] = public
        if tags is not None:
            attributes["tags"] = tags

        data = {
            "data": {
                "type": "nodes",
                "id": project_id,
                "attributes": attributes,
            }
        }

        response = await self._patch(f"/nodes/{project_id}/", data)
        projects = self._parse_projects([response.get("data", {})])
        return projects[0]

    def _parse_projects(self, data: list[dict]) -> list[OSFProject]:
        """Parse project data from API response."""
        projects = []
        for item in data:
            attrs = item.get("attributes", {})
            links = item.get("links", {})
            rels = item.get("relationships", {})

            # Extract contributor names if available
            contributors = []
            if "contributors" in rels:
                contrib_data = rels["contributors"].get("data", [])
                contributors = [c.get("id", "") for c in contrib_data]

            # Get file and wiki URLs from relationships
            files_url = None
            wiki_url = None
            if "files" in rels:
                files_url = rels["files"].get("links", {}).get("related", {}).get("href")
            if "wikis" in rels:
                wiki_url = rels["wikis"].get("links", {}).get("related", {}).get("href")

            projects.append(OSFProject(
                id=item.get("id", ""),
                title=attrs.get("title", ""),
                description=attrs.get("description"),
                date_created=attrs.get("date_created", ""),
                date_modified=attrs.get("date_modified", ""),
                public=attrs.get("public", False),
                category=attrs.get("category", ""),
                tags=attrs.get("tags", []),
                contributors=contributors,
                url=links.get("html", ""),
                api_url=links.get("self", ""),
                files_url=files_url,
                wiki_url=wiki_url,
            ))
        return projects

    # =====================
    # REGISTRATION METHODS
    # =====================

    async def search_registrations(
        self,
        query: str | None = None,
        max_results: int = 10,
    ) -> list[OSFRegistration]:
        """Search for OSF registrations.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of registrations
        """
        params: dict[str, Any] = {
            "page[size]": min(max_results, self.settings.MAX_RESULTS),
            "filter[public]": "true",
        }

        if query:
            params["filter[title][icontains]"] = query

        response = await self._get("/registrations/", params=params)
        return self._parse_registrations(response.get("data", []))

    async def get_registration(self, registration_id: str) -> OSFRegistration:
        """Get a specific registration by ID."""
        response = await self._get(f"/registrations/{registration_id}/")
        regs = self._parse_registrations([response.get("data", {})])
        if not regs:
            raise ValueError(f"Registration {registration_id} not found")
        return regs[0]

    def _parse_registrations(self, data: list[dict]) -> list[OSFRegistration]:
        """Parse registration data from API response."""
        registrations = []
        for item in data:
            attrs = item.get("attributes", {})
            links = item.get("links", {})

            # Extract DOI from identifiers if available
            doi = None
            identifiers = attrs.get("identifiers", {})
            if isinstance(identifiers, dict):
                doi = identifiers.get("doi")

            registrations.append(OSFRegistration(
                id=item.get("id", ""),
                title=attrs.get("title", ""),
                description=attrs.get("description"),
                date_registered=attrs.get("date_registered", ""),
                registration_schema=attrs.get("registration_schema", ""),
                public=attrs.get("public", False),
                doi=doi,
                url=links.get("html", ""),
                api_url=links.get("self", ""),
            ))
        return registrations

    # =====================
    # PREPRINT METHODS
    # =====================

    async def search_preprints(
        self,
        query: str | None = None,
        subjects: list[str] | None = None,
        provider: str | None = None,
        max_results: int = 10,
    ) -> list[OSFPreprint]:
        """Search for OSF preprints.

        Args:
            query: Search query
            subjects: Filter by subjects
            provider: Filter by preprint provider (e.g., 'osf', 'psyarxiv')
            max_results: Maximum results

        Returns:
            List of preprints
        """
        params: dict[str, Any] = {
            "page[size]": min(max_results, self.settings.MAX_RESULTS),
        }

        if query:
            params["filter[title][icontains]"] = query

        if provider:
            params["filter[provider]"] = provider

        response = await self._get("/preprints/", params=params)
        return self._parse_preprints(response.get("data", []))

    async def get_preprint(self, preprint_id: str) -> OSFPreprint:
        """Get a specific preprint by ID."""
        response = await self._get(f"/preprints/{preprint_id}/")
        preprints = self._parse_preprints([response.get("data", {})])
        if not preprints:
            raise ValueError(f"Preprint {preprint_id} not found")
        return preprints[0]

    def _parse_preprints(self, data: list[dict]) -> list[OSFPreprint]:
        """Parse preprint data from API response."""
        preprints = []
        for item in data:
            attrs = item.get("attributes", {})
            links = item.get("links", {})

            # Extract subjects
            subjects = []
            for subject in attrs.get("subjects", []):
                if isinstance(subject, list):
                    subjects.extend([s.get("text", "") for s in subject if isinstance(s, dict)])
                elif isinstance(subject, dict):
                    subjects.append(subject.get("text", ""))

            preprints.append(OSFPreprint(
                id=item.get("id", ""),
                title=attrs.get("title", ""),
                description=attrs.get("description"),
                date_published=attrs.get("date_published", ""),
                doi=attrs.get("doi"),
                subjects=subjects,
                license=attrs.get("license", {}).get("name") if isinstance(attrs.get("license"), dict) else None,
                download_url=links.get("preprint_doi"),
                url=links.get("html", ""),
                api_url=links.get("self", ""),
            ))
        return preprints

    # =====================
    # FILE METHODS
    # =====================

    async def list_project_files(
        self,
        project_id: str,
        path: str = "/",
        provider: str = "osfstorage",
    ) -> list[OSFFile]:
        """List files in a project.

        Args:
            project_id: Project ID
            path: Path within the project
            provider: Storage provider (default: osfstorage)

        Returns:
            List of files and folders
        """
        endpoint = f"/nodes/{project_id}/files/{provider}/"
        if path and path != "/":
            endpoint = f"{endpoint}{path.lstrip('/')}"

        response = await self._get(endpoint)
        return self._parse_files(response.get("data", []))

    async def get_file(self, file_id: str) -> OSFFile:
        """Get file metadata by ID."""
        response = await self._get(f"/files/{file_id}/")
        files = self._parse_files([response.get("data", {})])
        if not files:
            raise ValueError(f"File {file_id} not found")
        return files[0]

    async def download_file(self, file_id: str) -> bytes:
        """Download file content.

        Args:
            file_id: File ID

        Returns:
            File content as bytes
        """
        # First get file metadata to get download URL
        file_info = await self.get_file(file_id)
        if not file_info.download_url:
            raise ValueError(f"No download URL for file {file_id}")

        # Download the file
        response = await self.client.get(
            file_info.download_url,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.content

    async def download_file_by_url(self, download_url: str) -> bytes:
        """Download file directly by URL.

        Args:
            download_url: Direct download URL

        Returns:
            File content as bytes
        """
        response = await self.client.get(download_url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def _parse_files(self, data: list[dict]) -> list[OSFFile]:
        """Parse file data from API response."""
        files = []
        for item in data:
            attrs = item.get("attributes", {})
            links = item.get("links", {})

            files.append(OSFFile(
                id=item.get("id", ""),
                name=attrs.get("name", ""),
                kind=attrs.get("kind", "file"),
                path=attrs.get("materialized_path", attrs.get("path", "")),
                size=attrs.get("size"),
                date_modified=attrs.get("date_modified"),
                content_type=attrs.get("content_type"),
                download_url=links.get("download"),
                provider=attrs.get("provider", "osfstorage"),
            ))
        return files

    # =====================
    # WIKI METHODS
    # =====================

    async def list_wiki_pages(self, project_id: str) -> list[OSFWikiPage]:
        """List wiki pages for a project.

        Args:
            project_id: Project ID

        Returns:
            List of wiki pages
        """
        response = await self._get(f"/nodes/{project_id}/wikis/")
        return self._parse_wiki_pages(response.get("data", []))

    async def get_wiki_page(self, wiki_id: str) -> OSFWikiPage:
        """Get a specific wiki page."""
        response = await self._get(f"/wikis/{wiki_id}/")
        pages = self._parse_wiki_pages([response.get("data", {})])
        if not pages:
            raise ValueError(f"Wiki page {wiki_id} not found")
        return pages[0]

    async def get_wiki_content(self, wiki_id: str) -> str:
        """Get wiki page content.

        Args:
            wiki_id: Wiki page ID

        Returns:
            Wiki content as string
        """
        response = await self._get(f"/wikis/{wiki_id}/content/")
        return response.get("data", {}).get("attributes", {}).get("content", "")

    def _parse_wiki_pages(self, data: list[dict]) -> list[OSFWikiPage]:
        """Parse wiki page data from API response."""
        pages = []
        for item in data:
            attrs = item.get("attributes", {})
            links = item.get("links", {})

            pages.append(OSFWikiPage(
                id=item.get("id", ""),
                name=attrs.get("name", ""),
                content=attrs.get("content", ""),
                date_modified=attrs.get("date_modified", ""),
                url=links.get("html", ""),
            ))
        return pages

    # =====================
    # DOI METHODS
    # =====================

    async def resolve_doi(self, doi: str) -> dict[str, Any]:
        """Resolve a DOI to get OSF resource information.

        Args:
            doi: DOI string (e.g., '10.17605/OSF.IO/ABC12')

        Returns:
            Resource information
        """
        # Clean up DOI format
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

        # Try to extract OSF ID from DOI
        if "OSF.IO/" in doi.upper():
            osf_id = doi.upper().split("OSF.IO/")[-1]
            # Try as project first
            try:
                project = await self.get_project(osf_id.lower())
                return {
                    "type": "project",
                    "id": project.id,
                    "title": project.title,
                    "url": project.url,
                }
            except Exception:
                pass

            # Try as registration
            try:
                reg = await self.get_registration(osf_id.lower())
                return {
                    "type": "registration",
                    "id": reg.id,
                    "title": reg.title,
                    "url": reg.url,
                }
            except Exception:
                pass

            # Try as preprint
            try:
                preprint = await self.get_preprint(osf_id.lower())
                return {
                    "type": "preprint",
                    "id": preprint.id,
                    "title": preprint.title,
                    "url": preprint.url,
                }
            except Exception:
                pass

        raise ValueError(f"Could not resolve DOI: {doi}")

    # =====================
    # CONTRIBUTOR METHODS
    # =====================

    async def get_project_contributors(self, project_id: str) -> list[dict[str, Any]]:
        """Get contributors for a project.

        Args:
            project_id: Project ID

        Returns:
            List of contributor information
        """
        response = await self._get(f"/nodes/{project_id}/contributors/")
        contributors = []
        for item in response.get("data", []):
            attrs = item.get("attributes", {})
            embeds = item.get("embeds", {})
            user_data = embeds.get("users", {}).get("data", {}).get("attributes", {})

            contributors.append({
                "id": item.get("id", ""),
                "bibliographic": attrs.get("bibliographic", True),
                "permission": attrs.get("permission", "read"),
                "full_name": user_data.get("full_name", ""),
                "given_name": user_data.get("given_name", ""),
                "family_name": user_data.get("family_name", ""),
            })
        return contributors
