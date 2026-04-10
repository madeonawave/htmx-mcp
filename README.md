# htmx-mcp

Chrome DevTools MCP server for debugging htmx applications.

This MCP connects to a Chrome browser (via CDP) and lets you inspect and debug any htmx-powered web page. 
It captures htmx events and exposes an API to query the page.

It can: 
- Trigger HTMX Events
- Validate swaps automatically
- Monitor HTMX State
- Discover all elements with htmx attributes on a page:
  - `hx-get`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete`
  - `hx-trigger`, `hx-target`, `hx-swap`, etc.

- Monitor the htmx event lifecycle:
  - `htmx:beforeRequest` - before any request
  - `htmx:configRequest` - request configuration
  - `htmx:afterRequest` - after response received
  - `htmx:afterSwap` - after DOM swap
  - `htmx:settle` - after settle phase
  - Error events: `htmx:responseError`, `htmx:sendError`, `htmx:swapError`

- Debug Issues
  - View all captured errors
  - Check if htmx is loaded
  - Get htmx version
  - Inspect internal state

- Interact Programmatically
  - Trigger events on elements
  - Make htmx-style ajax requests
  - Navigate pages (auto-injects interceptor)

### What It Cannot Do
- Cannot change how htmx processes requests or responses.
- Only captures event metadata, not the actual request/response content.
- It won't click buttons or fill forms automatically.
- It can not share Chrome with other tools. Each MCP gets its own (background) tab.


## Installation

### From Source
```bash
git clone https://github.com/madeonawave/htmx-mcp.git
cd htmx-mcp
uv tool install -e .
```

### Via uv (once published)
```bash
uv tool install mcp-htmx
```

### Via pip (once published)
```bash
pip install mcp-htmx
```

## Usage

### 1. Start Chrome with Remote Debugging

```bash
google-chrome --remote-debugging-port=9222 --headless-new --no-sandbox
```

Or use the MCP's auto-spawn feature (it will try to find Chrome in your PATH).

### 2. Configure in OpenCode

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

### 3. Use the Tools

In OpenCode, ask:

> "Find all htmx elements on the current page"
> "Show me the htmx events"
> "Navigate to https://example.com and check if htmx is loaded"

## Tools Reference

| Tool | Description | Example |
|------|-------------|---------|
| `htmx_check` | Is htmx loaded? Get version | `{loaded: true, version: "1.9.12"}` |
| `htmx_elements` | All htmx-enabled elements | `[{"tag":"button","attrs":{"hx-get":"/api"}}]` |
| `htmx_events` | Captured events (with filter/limit) | `[{name: "htmx:beforeRequest", time: 1234567890}]` |
| `htmx_errors` | All captured errors | `[{message: "Network error", time: 1234567890}]` |
| `htmx_state` | Internal htmx state | `{version: "1.9.12"}` |
| `htmx_navigate` | Navigate URL + inject interceptor | `{success: true, url: "https://..."}` |
| `htmx_trigger` | Trigger event on element | `{success: true, event: "click"}` |
| `htmx_ajax` | Make htmx-style request | `{success: true, method: "GET"}` |

## Requirements

- Python 3.10+
- Chrome/Chromium with remote debugging enabled
- Chrome must be accessible on `localhost:9222`

## Security Warning

Use a separate Chrome browser / profile. The MCP can execute JavaScript in the browser. Don't use your primary browser session.

## Development

```bash
# Run tests
uv run --with pytest pytest tests/test_package.py -v

# Run manually
uv sync
mcp-htmx
```

## License

MIT
