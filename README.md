# mcp-htmx

Chrome DevTools MCP server for debugging htmx applications.

## Features

- Check if htmx is loaded on any page
- Find all htmx-enabled elements
- Capture and inspect htmx events (beforeRequest, afterSwap, etc.)
- View htmx errors
- Navigate pages with automatic interceptor injection

## Installation

### Via uv (recommended)
```bash
uv tool install /projects/cheatsheet/mcp-htmx-python
```

### Via pip
```bash
pip install mcp-htmx
```

### Development
```bash
cd mcp-htmx-python
uv sync
```

## Usage

### As MCP server with OpenCode
Configure in opencode.json:
```json
{
  "mcp": {
    "htmx": {
      "type": "local",
      "command": ["mcp-htmx"],
      "enabled": true
    }
  }
}
```

### Command line
```bash
mcp-htmx
```

## Tools

| Tool | Description |
|------|-------------|
| `htmx_check` | Check if htmx is loaded + version |
| `htmx_elements` | Find all htmx-enabled elements |
| `htmx_events` | List captured events |
| `htmx_errors` | Get errors |
| `htmx_state` | Get htmx internal state |
| `htmx_navigate` | Navigate + inject |

## Requirements

- Chrome with remote debugging on port 9222
- Python 3.10+

## Chrome Connection

Uses pychrome to connect to Chrome on port 9222. Start Chrome with:
```bash
google-chrome --remote-debugging-port=9222 --headless
```

Or let mcp-htmx spawn Chrome automatically (if found in PATH).