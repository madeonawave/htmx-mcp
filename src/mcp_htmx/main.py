#!/usr/bin/env python3
"""
mcp-htmx - Chrome DevTools MCP for debugging htmx applications.

Uses:
- mcp: Model Context Protocol Python SDK
- pychrome: Connect to Chrome on port 9222
"""

import sys
import os
import subprocess
import asyncio
import signal
from typing import Any

from mcp.server.fastmcp import FastMCP
import pychrome


def spawn_chrome():
    """Spawn Chrome with remote debugging if not already running."""
    try:
        # Try to connect first
        test_browser = pychrome.Browser(url="http://127.0.0.1:9222")
        test_browser.close()
        return True  # Already running
    except:
        pass

    # Spawn Chrome
    chrome_paths = [
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "google-chrome",
    ]

    for chrome_path in chrome_paths:
        try:
            subprocess.Popen(
                [
                    chrome_path,
                    "--remote-debugging-port=9222",
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--window-size=1280,720",
                    "about:blank",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for Chrome to start
            import time

            time.sleep(2)
            return True
        except FileNotFoundError:
            continue

    return False


HTMX_INTERCEPTOR = """
(function() {
  if (window.__htmxInterceptorInjected) return;
  window.__htmxInterceptorInjected = true;

  window.__htmxEventLog = [];
  window.__htmxErrorLog = [];
  const MAX = 100;

  function logEvent(name, evt) {
    window.__htmxEventLog.push({
      name: name,
      time: Date.now(),
      target: evt?.target?.id || evt?.target?.tagName || null,
      detail: evt?.detail ? JSON.stringify(evt.detail).substring(0, 200) : null
    });
    if (window.__htmxEventLog.length > MAX) window.__htmxEventLog.shift();
  }

  function logError(err) {
    window.__htmxErrorLog.push({
      time: Date.now(),
      message: err.message || String(err),
      stack: err.stack ? err.stack.substring(0, 500) : null
    });
    if (window.__htmxErrorLog.length > MAX) window.__htmxErrorLog.shift();
  }

  document.body.addEventListener('htmx:beforeRequest', e => logEvent('htmx:beforeRequest', e));
  document.body.addEventListener('htmx:afterRequest', e => logEvent('htmx:afterRequest', e));
  document.body.addEventListener('htmx:afterSwap', e => logEvent('htmx:afterSwap', e));
  document.body.addEventListener('htmx:beforeSwap', e => logEvent('htmx:beforeSwap', e));
  document.body.addEventListener('htmx:configRequest', e => logEvent('htmx:configRequest', e));
  document.body.addEventListener('htmx:responseError', e => { logEvent('htmx:responseError', e); logError(e.detail?.error || 'Response error'); });
  document.body.addEventListener('htmx:sendError', e => { logEvent('htmx:sendError', e); logError(e.detail?.error || 'Send error'); });
  document.body.addEventListener('htmx:swapError', e => { logEvent('htmx:swapError', e); logError(e.detail?.error || 'Swap error'); });

  window._htmxTool = {
    events: () => window.__htmxEventLog,
    errors: () => window.__htmxErrorLog,
    elements: () => {
      const els = document.querySelectorAll('[hx-get], [hx-post], [hx-put], [hx-patch], [hx-delete], [data-hx-get], [data-hx-post]');
      return Array.from(els).map(el => {
        const a = {}; 
        for (const attr of el.attributes) {
          if (attr.name.startsWith('hx-') || attr.name.startsWith('data-hx-')) a[attr.name] = attr.value;
        }
        return { tag: el.tagName.toLowerCase(), id: el.id, attrs: a };
      });
    },
    state: () => window.htmx ? { version: window.htmx.version } : null
  };
})();
"""

mcp = FastMCP("htmx", json_response=True)

browser = None
tab = None


def get_tab():
    """Get or create browser tab by connecting to Chrome on port 9222."""
    global browser, tab

    # Test if existing tab works
    if tab is not None:
        try:
            tab.Runtime.evaluate(expression="1+1")
            return tab
        except:
            tab = None  # Reset dead tab

    try:
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        tab = browser.new_tab()
        tab.start()
        # Inject the interceptor
        tab.Runtime.evaluate(expression=HTMX_INTERCEPTOR)
        return tab
    except Exception as e:
        print(f"No Chrome, trying to spawn: {e}", file=sys.stderr)
        if spawn_chrome():
            return get_tab()  # Retry after spawning
        return None


def eval_js(t, expr: str):
    """Evaluate JS and extract value from CDP result."""
    result = t.Runtime.evaluate(expression=expr)
    if result and "result" in result:
        return result["result"].get("value")
    return result


@mcp.tool()
def htmx_check() -> dict:
    """Check if htmx is loaded on page and get version."""
    t = get_tab()
    if t is None:
        return {
            "error": "Cannot connect to Chrome on port 9222. Is Chrome running with --remote-debugging-port=9222?"
        }

    try:
        return eval_js(
            t,
            """window._htmxTool 
            ? { loaded: true, version: window._htmxTool.state()?.version }
            : { loaded: false }""",
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def htmx_events(limit: int = 20, filter: str = "") -> list:
    """Get captured htmx events (beforeRequest, afterSwap, etc.)."""
    t = get_tab()
    if t is None:
        return [{"error": "Cannot connect to Chrome"}]

    global tab
    tab = t
    try:
        if filter:
            expr = f"""window._htmxTool.events().filter(e=>e.name.includes('{filter}')).slice(-{limit})"""
        else:
            expr = f"window._htmxTool.events().slice(-{limit})"

        return eval_js(t, expr) or []
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def htmx_elements() -> list:
    """Find all htmx-enabled elements on page."""
    t = get_tab()
    if t is None:
        return [{"error": "Cannot connect to Chrome"}]

    global tab
    tab = t
    try:
        return eval_js(t, "window._htmxTool.elements()") or []
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def htmx_errors() -> list:
    """Get captured htmx errors."""
    t = get_tab()
    if t is None:
        return [{"error": "Cannot connect to Chrome"}]

    global tab
    tab = t
    try:
        return eval_js(t, "window._htmxTool.errors()") or []
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def htmx_state() -> dict:
    """Get htmx internal state."""
    t = get_tab()
    if t is None:
        return {"error": "Cannot connect to Chrome"}

    global tab
    tab = t
    try:
        return eval_js(t, "window._htmxTool.state()") or {}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def htmx_navigate(url: str = "about:blank") -> dict:
    """Navigate to a URL and inject htmx interceptor."""
    t = get_tab()
    if t is None:
        return {"error": "Cannot connect to Chrome"}

    try:
        t.Page.navigate(url=url)
        # Wait for page to load
        import time

        time.sleep(2)
        # Reinject interceptor
        t.Runtime.evaluate(expression=HTMX_INTERCEPTOR)
        return {"success": True, "url": url}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def htmx_trigger(selector: str, event: str = "click") -> dict:
    """Trigger an event on an htmx element.

    Args:
        selector: CSS selector for the element
        event: Event name to trigger (e.g., 'click', 'submit', 'change')
    """
    t = get_tab()
    if t is None:
        return {"error": "Cannot connect to Chrome"}

    global tab
    tab = t
    try:
        result = eval_js(
            t,
            f"""(function() {{
            const el = document.querySelector('{selector}');
            if (!el) return {{ error: 'Element not found: {selector}' }};
            htmx.trigger(el, '{event}');
            return {{ success: true, event: '{event}', selector: '{selector}' }};
        }})()""",
        )
        return result or {"error": "No result"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def htmx_ajax(
    method: str = "GET",
    url: str = "",
    source: str = "",
    target: str = "",
    swap: str = "innerHTML",
) -> dict:
    """Issue an htmx-style ajax request directly.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        url: URL to request
        source: CSS selector for source element (values from this element)
        target: CSS selector for target element to receive response
        swap: Swap method (innerHTML, outerHTML, afterbegin, beforeend, etc.)
    """
    t = get_tab()
    if t is None:
        return {"error": "Cannot connect to Chrome"}

    global tab
    tab = t
    try:
        # Build the htmx.ajax config object
        config = f"""{{
            source: document.querySelector('{source}') || undefined,
            target: document.querySelector('{target}') || undefined,
            swap: '{swap}'
        }}"""

        if not url:
            # Use htmx.trigger with the params
            return {"error": "url is required"}

        result = eval_js(
            t,
            f"""(function() {{
            const detail = {config};
            detail.url = '{url}';
            detail.path = '{url}';
            detail.verb = '{method}';
            
            // Find a trigger element if not specified
            const triggerEl = detail.source || document.activeElement;
            
            htmx.ajax('{method}', '{url}', detail);
            return {{ success: true, method: '{method}', url: '{url}', swap: '{swap}' }};
        }})()""",
        )
        return result or {"error": "No result"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def htmx_events(limit: int = 20, filter: str = "") -> list:
    """Get captured htmx events (beforeRequest, afterSwap, etc.)."""
    p = await get_page()
    if p is None:
        return [{"error": "Cannot connect to Chrome"}]

    try:
        if filter:
            expr = f"""() => window._htmxTool.events().filter(e=>e.name.includes('{filter}')).slice(-{limit})"""
        else:
            expr = f"""() => window._htmxTool.events().slice(-{limit})"""

        result = await p.evaluate(f"({expr})()")
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def htmx_elements() -> list:
    """Find all htmx-enabled elements on page."""
    p = await get_page()
    if p is None:
        return [{"error": "Cannot connect to Chrome"}]

    try:
        result = await p.evaluate("() => window._htmxTool.elements()")
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def htmx_errors() -> list:
    """Get captured htmx errors."""
    p = await get_page()
    if p is None:
        return [{"error": "Cannot connect to Chrome"}]

    try:
        result = await p.evaluate("() => window._htmxTool.errors()")
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def htmx_state() -> dict:
    """Get htmx internal state."""
    p = await get_page()
    if p is None:
        return {"error": "Cannot connect to Chrome"}

    try:
        result = await p.evaluate("() => window._htmxTool.state()")
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def htmx_navigate(url: str = "about:blank") -> dict:
    """Navigate to a URL and inject htmx interceptor."""
    global page

    p = await get_page()
    if p is None:
        return {"error": "Cannot connect to Chrome"}

    try:
        await p.goto(url)
        await p.evaluateOnDocument(HTMX_INTERCEPTOR)
        return {"success": True, "url": url}
    except Exception as e:
        return {"error": str(e)}


def cleanup():
    """Close browser on exit."""
    global browser, tab
    print("mcp-htmx closing...", file=sys.stderr)
    if tab:
        try:
            tab.stop()
        except Exception as e:
            print(f"Tab stop error: {e}", file=sys.stderr)
    if browser:
        try:
            pass  # pychrome Browser has no close method
        except Exception as e:
            print(f"Browser cleanup error: {e}", file=sys.stderr)


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    cleanup()
    sys.exit(0)


def main():
    """Main entry point for the MCP server."""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("mcp-htmx starting on stdio...", file=sys.stderr)
    try:
        mcp.run(transport="stdio")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
