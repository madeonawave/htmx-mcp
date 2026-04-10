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

  document.addEventListener('htmx:beforeRequest', e => logEvent('htmx:beforeRequest', e));
  document.addEventListener('htmx:afterRequest', e => logEvent('htmx:afterRequest', e));
  document.addEventListener('htmx:afterSwap', e => logEvent('htmx:afterSwap', e));
  document.addEventListener('htmx:beforeSwap', e => logEvent('htmx:beforeSwap', e));
  document.addEventListener('htmx:configRequest', e => logEvent('htmx:configRequest', e));
  document.addEventListener('htmx:responseError', e => { logEvent('htmx:responseError', e); logError(e.detail?.error || 'Response error'); });
  document.addEventListener('htmx:sendError', e => { logEvent('htmx:sendError', e); logError(e.detail?.error || 'Send error'); });
  document.addEventListener('htmx:swapError', e => { logEvent('htmx:swapError', e); logError(e.detail?.error || 'Swap error'); });

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
            pass  # Tab dead, will create new one

    try:
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        tab = browser.new_tab()
        tab.start()
        tab.Runtime.evaluate(expression=HTMX_INTERCEPTOR)
        return tab
    except Exception as e:
        print(f"No Chrome, trying to spawn: {e}", file=sys.stderr)
        if spawn_chrome():
            browser = None
            tab = None
            return get_tab()  # Retry after spawning
        return None


def eval_js(t, expr: str):
    """Evaluate JS and extract value from CDP result."""
    result = t.Runtime.evaluate(expression=expr)
    if result and "result" in result:
        return result["result"].get("value")
    return result


def js_escape(s: str) -> str:
    """Escape a string for safe insertion into JavaScript.

    This prevents XSS via parameter injection.
    """
    # Escape backslashes first, then quotes, then newlines/tabs
    return (
        s.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("<", "\\x3c")
        .replace(">", "\\x3e")
        .replace("&", "\\x26")
    )


def js_selector(selector: str) -> str:
    """Escape a CSS selector for safe use in document.querySelector."""
    # For selectors, we need to be more careful - single quotes are common in CSS
    # Use JSON.stringify which properly escapes for JS strings
    return f"JSON.stringify(['{js_escape(selector)}'])"


@mcp.tool()
def htmx_check() -> dict:
    """Check if htmx is loaded on page and get version."""
    t = get_tab()
    if t is None:
        return {
            "error": "Cannot connect to Chrome on port 9222. Is Chrome running with --remote-debugging-port=9222?"
        }

    try:
        import json

        result = eval_js(
            t,
            """JSON.stringify(
            typeof window.htmx !== 'undefined' 
            ? { loaded: true, version: window.htmx.version }
            : { loaded: false }
            )""",
        )
        return json.loads(result) if result else {"loaded": False}
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
            expr = f"""JSON.stringify(window._htmxTool.events().filter(e=>e.name.includes('{filter}')).slice(-{limit}))"""
        else:
            expr = f"JSON.stringify(window._htmxTool.events().slice(-{limit}))"

        result = eval_js(t, expr)
        import json

        return json.loads(result) if result else []
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
        result = eval_js(t, "JSON.stringify(window._htmxTool.elements())")
        import json

        return json.loads(result) if result else []
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
        result = eval_js(t, "JSON.stringify(window._htmxTool.errors())")
        import json

        return json.loads(result) if result else []
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
        result = eval_js(t, "JSON.stringify(window._htmxTool.state())")
        import json

        return json.loads(result) if result else {}
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
        import time

        time.sleep(4)
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

    # Validate inputs - reject suspicious patterns
    if not selector or len(selector) > 500:
        return {"error": "Invalid selector"}
    if not event or len(event) > 100:
        return {"error": "Invalid event name"}

    try:
        escaped_selector = js_escape(selector)
        escaped_event = js_escape(event)
        js_expr = f"""(function() {{
            var selector = '{escaped_selector}';
            var eventName = '{escaped_event}';
            try {{
                var el = document.querySelector(selector);
                if (!el) return JSON.stringify({{ error: 'Element not found: ' + selector }});
                htmx.trigger(el, eventName);
                return JSON.stringify({{ success: true, event: eventName, selector: selector }});
            }} catch(e) {{
                return JSON.stringify({{ error: e.message }});
            }}
        }})()"""
        result = eval_js(t, js_expr)
        import json

        return json.loads(result) if result else {"error": "No result"}
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

    if not url:
        return {"error": "url is required"}

    escaped_method = js_escape(method.upper())
    escaped_url = js_escape(url)
    escaped_source = js_escape(source)
    escaped_target = js_escape(target)
    escaped_swap = js_escape(swap)

    try:
        js_expr = f"""(function() {{
            if (!window.htmx) return JSON.stringify({{ error: 'htmx not loaded' }});
            const detail = {{
                swap: '{escaped_swap}'
            }};
            if ('{escaped_source}') detail.source = document.querySelector('{escaped_source}');
            if ('{escaped_target}') detail.target = document.querySelector('{escaped_target}');
            
            htmx.ajax('{escaped_method}', '{escaped_url}', detail);
            return JSON.stringify({{ success: true, method: '{escaped_method}', url: '{escaped_url}', swap: '{escaped_swap}' }});
        }})()"""
        result = eval_js(t, js_expr)
        import json

        return json.loads(result) if result else {"error": "No result"}
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
