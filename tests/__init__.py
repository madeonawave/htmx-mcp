"""Tests for mcp-htmx package - file-based tests that don't require imports."""

import os
import re


def test_package_structure():
    """Test package has correct structure."""
    src_path = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_htmx")
    assert os.path.exists(src_path)
    init_path = os.path.join(src_path, "__init__.py")
    assert os.path.exists(init_path)


def test_pyproject_has_scripts():
    """Test pyproject.toml has entry point."""
    path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(path) as f:
        content = f.read()

    assert 'mcp-htmx = "mcp_htmx:main"' in content


def test_build_system():
    """Test pyproject.toml has build system."""
    path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(path) as f:
        content = f.read()

    assert "hatchling" in content
    assert "[build-system]" in content


def test_has_8_tools():
    """Test 8 tool definitions in code (with async versions)."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    # Count @mcp.tool() decorators - there are 8 unique tools, but some are async too
    tool_count = content.count("@mcp.tool()")
    assert tool_count >= 8, f"Expected at least 8 tools, found {tool_count}"


def test_has_hx_attributes():
    """Test htmx attributes are detected."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    # Check for hx-* selectors in interceptor
    assert "hx-get" in content
    assert "hx-post" in content
    assert "hx-put" in content
    assert "hx-patch" in content
    assert "hx-delete" in content


def test_has_event_listeners():
    """Test htmx events are captured."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    # Core events
    assert "htmx:beforeRequest" in content
    assert "htmx:afterRequest" in content
    assert "htmx:afterSwap" in content


def test_has_error_handling():
    """Test error events are captured."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "htmx:responseError" in content
    assert "htmx:sendError" in content
    assert "htmx:swapError" in content


def test_has_main_function():
    """Test main() function exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def main():" in content


def test_has_spawn_chrome():
    """Test spawn_chrome function exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def spawn_chrome():" in content


def test_has_get_tab():
    """Test get_tab function exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def get_tab():" in content


def test_has_cleanup():
    """Test cleanup function exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def cleanup():" in content


def test_tool_htmx_trigger():
    """Test htmx_trigger tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_trigger(" in content


def test_tool_htmx_ajax():
    """Test htmx_ajax tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_ajax(" in content


def test_tool_htmx_navigate():
    """Test htmx_navigate tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_navigate(" in content


def test_tool_htmx_check():
    """Test htmx_check tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_check(" in content


def test_tool_htmx_elements():
    """Test htmx_elements tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_elements(" in content


def test_tool_htmx_events():
    """Test htmx_events tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_events(" in content


def test_tool_htmx_errors():
    """Test htmx_errors tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_errors(" in content


def test_tool_htmx_state():
    """Test htmx_state tool exists."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "def htmx_state(" in content


def test_has_signal_handlers():
    """Test signal handlers are set up."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "signal.SIGTERM" in content
    assert "signal.SIGINT" in content


def test_has_pychrome_import():
    """Test pychrome is imported."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "import pychrome" in content


def test_has_mcp_import():
    """Test mcp is imported."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert "from mcp.server.fastmcp import FastMCP" in content


def test_mcp_name():
    """Test MCP is named 'htmx'."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "src", "mcp_htmx", "__init__.py"
    )
    with open(path) as f:
        content = f.read()

    assert 'FastMCP("htmx"' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
