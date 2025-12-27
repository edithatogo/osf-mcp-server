"""OSF MCP Server Tools."""

from .search_projects import search_projects_tool, handle_search_projects
from .search_registrations import search_registrations_tool, handle_search_registrations
from .search_preprints import search_preprints_tool, handle_search_preprints
from .get_project import get_project_tool, handle_get_project
from .list_files import list_files_tool, handle_list_files
from .download_file import download_file_tool, handle_download_file
from .read_file import read_file_tool, handle_read_file
from .create_project import create_project_tool, handle_create_project
from .update_project import update_project_tool, handle_update_project
from .wiki import get_wiki_tool, handle_get_wiki
from .resolve_doi import resolve_doi_tool, handle_resolve_doi

__all__ = [
    # Search tools
    "search_projects_tool",
    "handle_search_projects",
    "search_registrations_tool",
    "handle_search_registrations",
    "search_preprints_tool",
    "handle_search_preprints",
    # Project tools
    "get_project_tool",
    "handle_get_project",
    "create_project_tool",
    "handle_create_project",
    "update_project_tool",
    "handle_update_project",
    # File tools
    "list_files_tool",
    "handle_list_files",
    "download_file_tool",
    "handle_download_file",
    "read_file_tool",
    "handle_read_file",
    # Wiki tools
    "get_wiki_tool",
    "handle_get_wiki",
    # DOI tools
    "resolve_doi_tool",
    "handle_resolve_doi",
]
