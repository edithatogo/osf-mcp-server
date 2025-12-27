# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install with test dependencies
uv pip install -e ".[test]"
```

### Testing
```bash
# Run all tests with coverage
python -m pytest

# Run specific test file
python -m pytest tests/test_search.py

# Run tests with verbose output
python -m pytest -v
```

### Running the Server
```bash
# Run as module
python -m osf_mcp_server

# Or via entry point
osf-mcp-server

# With custom storage path
osf-mcp-server --storage-path /path/to/storage

# With authentication
OSF_TOKEN=your_token osf-mcp-server
```

## Architecture Overview

This is an **MCP (Model Context Protocol) server** that provides AI models access to Open Science Framework (OSF) research resources. The codebase follows a modular architecture with four main layers:

### Core Components

1. **Server Layer** (`server.py`): Main MCP server implementation that handles tool registration and request routing
2. **OSF Client** (`osf_client.py`): Async HTTP client for OSF API v2 with data classes for projects, registrations, preprints, and files
3. **Tools Layer** (`tools/`): Individual MCP tools for OSF operations:
   - `search_projects.py`: Search OSF projects
   - `search_registrations.py`: Search pre-registered studies
   - `search_preprints.py`: Search preprints from OSF and partners
   - `get_project.py`: Get project details and contributors
   - `list_files.py`: List project files
   - `download_file.py`: Download files with PDF-to-markdown conversion
   - `read_file.py`: Read stored file content
   - `create_project.py`: Create new projects (auth required)
   - `update_project.py`: Update project metadata (auth required)
   - `wiki.py`: Access wiki content
   - `resolve_doi.py`: Resolve OSF DOIs
4. **Resource Management** (`resources/osf_manager.py`): `OSFResourceManager` class handles file storage and retrieval
5. **Configuration** (`config.py`): Pydantic-based settings with environment variable support
6. **Prompts** (`prompts/`): Research-focused prompt templates

### Key Design Patterns

- **MCP Protocol Compliance**: All tools follow MCP specification with proper type definitions
- **Async-First**: Built on httpx with asyncio for non-blocking I/O operations
- **Dual Auth Mode**: Supports both authenticated (private access) and unauthenticated (public only) modes
- **PDF Conversion**: Downloads PDFs and converts to Markdown using pymupdf4llm for easy reading
- **Error Handling**: Comprehensive error handling with user-friendly JSON responses
- **JSON:API Format**: Proper handling of OSF's JSON:API response format

### Configuration

Environment variables (all optional with sensible defaults):
- `OSF_TOKEN`: Personal access token for authenticated access (optional)
- `OSF_STORAGE_PATH`: File storage location (default: `~/.osf-mcp-server/files`)
- `OSF_MAX_RESULTS`: Search results limit (default: 50)
- `OSF_REQUEST_TIMEOUT`: API timeout in seconds (default: 60)
- `OSF_API_URL`: Base API URL (default: `https://api.osf.io/v2`)

### Testing Strategy

Tests use pytest with async support and comprehensive mocking:
- `conftest.py` provides shared fixtures for mock OSF resources
- Tests cover both unit-level tool functionality and integration scenarios
- Mock-based approach avoids external API calls during testing

### OSF API Notes

- OSF uses JSON:API format with `data`, `attributes`, `relationships` structure
- Pagination uses `page[size]` and `page[number]` parameters
- Filtering syntax: `filter[field][operator]=value`
- Files can have multiple providers (osfstorage, github, dropbox, etc.)
