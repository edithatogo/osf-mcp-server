# OSF MCP Server

An MCP (Model Context Protocol) server for interacting with the [Open Science Framework (OSF)](https://osf.io). Search projects, registrations, preprints, manage files, and more.

## Features

- **Search OSF Content**
  - Projects (public and private with authentication)
  - Registrations (pre-registered studies)
  - Preprints (from OSF Preprints and partner services)

- **File Management**
  - List project files
  - Download files with PDF-to-Markdown conversion
  - Read cached file content

- **Project Management** (requires authentication)
  - Create new projects
  - Update project metadata
  - Access wiki content

- **DOI Resolution**
  - Resolve OSF DOIs to resources

## Installation

```bash
# Clone the repository
cd tools/osf-mcp-server

# Create virtual environment
uv venv
source .venv/bin/activate

# Install with dependencies
uv pip install -e ".[test]"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OSF_TOKEN` | Personal Access Token for authenticated access | None (public only) |
| `OSF_STORAGE_PATH` | Path for downloaded files | `~/.osf-mcp-server/files` |
| `OSF_MAX_RESULTS` | Maximum search results | 50 |
| `OSF_REQUEST_TIMEOUT` | API timeout in seconds | 60 |

### Getting an OSF Token

1. Log in to [osf.io](https://osf.io)
2. Go to Settings → Personal Access Tokens
3. Create a new token with required scopes
4. Set `OSF_TOKEN` environment variable

```bash
export OSF_TOKEN="your_token_here"
```

## Usage

### Running the Server

```bash
# Run directly
python -m osf_mcp_server

# Or via entry point
osf-mcp-server

# With custom storage path
osf-mcp-server --storage-path /path/to/storage
```

### Claude Desktop Integration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "osf": {
      "command": "python",
      "args": ["-m", "osf_mcp_server"],
      "env": {
        "OSF_TOKEN": "your_token_here"
      }
    }
  }
}
```

Or with uv:

```json
{
  "mcpServers": {
    "osf": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/osf-mcp-server",
        "run", "osf-mcp-server"
      ],
      "env": {
        "OSF_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Available Tools

### Search Tools

| Tool | Description |
|------|-------------|
| `search_projects` | Search for OSF projects by title, tags, category |
| `search_registrations` | Search for pre-registered studies |
| `search_preprints` | Search for preprints from OSF and partner services |

### Project Tools

| Tool | Description |
|------|-------------|
| `get_project` | Get detailed project information |
| `create_project` | Create a new project (auth required) |
| `update_project` | Update project metadata (auth required) |

### File Tools

| Tool | Description |
|------|-------------|
| `list_files` | List files and folders in a project |
| `download_file` | Download and cache a file locally |
| `read_file` | Read content of a downloaded file |

### Other Tools

| Tool | Description |
|------|-------------|
| `get_wiki` | List or get wiki page content |
| `resolve_doi` | Resolve an OSF DOI to a resource |

## Examples

### Search for Psychology Projects

```
Search for projects related to "cognitive bias":
- query: "cognitive bias"
- tags: ["psychology"]
- max_results: 20
```

### Download a Research Paper

```
1. Search for preprints: query="machine learning"
2. List project files: project_id="abc12"
3. Download PDF: file_id="xyz789"
4. Read content: file_id="xyz789"
```

### Create a New Project

```
Create project:
- title: "My Research Project"
- description: "A study on..."
- public: false
- tags: ["experiment", "2024"]
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=osf_mcp_server

# Run specific test file
python -m pytest tests/test_search.py -v
```

### Code Formatting

```bash
# Format with black
black src/

# Lint with ruff
ruff check src/
```

## Architecture

```
osf-mcp-server/
├── src/osf_mcp_server/
│   ├── __init__.py          # Entry point
│   ├── server.py             # MCP server implementation
│   ├── config.py             # Configuration settings
│   ├── osf_client.py         # OSF API client
│   ├── tools/                # MCP tools
│   │   ├── search_*.py       # Search tools
│   │   ├── *_file.py         # File tools
│   │   └── ...
│   ├── resources/            # Resource management
│   │   └── osf_manager.py
│   └── prompts/              # Research prompts
│       └── research_prompts.py
└── tests/
```

## OSF API Reference

This server uses the [OSF API v2](https://developer.osf.io/). Key endpoints:

- `/nodes/` - Projects and components
- `/registrations/` - Pre-registered studies
- `/preprints/` - Preprints
- `/files/` - File operations
- `/wikis/` - Wiki pages

## License

MIT License

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request