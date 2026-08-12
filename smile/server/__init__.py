"""
SMiLE prototype MCP server.

Exposes two tools to any MCP client:

  list_capabilities()
      Returns the structured catalog of functions available inside the
      sandbox -- names, type-stub signatures, descriptions, examples.

  execute_script(code)
      Runs agent-authored Python against that capability namespace in a
      sandboxed subprocess (see smile/sandbox/) and returns stdout/
      stderr/return value/error.

Run with:  uv run mcp dev smile/server/__init__.py   (MCP Inspector, for manual testing)
       or: uv run python3 -m smile.server            (stdio server, for a real client)

This package follows the project's one-function/method-per-file rule
(see CLAUDE.md): each tool lives in its own module, registered against
the shared `mcp` instance in mcp_instance.py. Importing them here (for
their `@mcp.tool()` side effects) and re-exporting `mcp`/`main` keeps
`from smile.server import mcp` and `python3 -m smile.server` working
exactly as when this was a single server.py file.
"""

from __future__ import annotations

from smile.server.main import main
from smile.server.mcp_instance import mcp

# Import each tool module for its registration side effect.
from smile.server import execute_script as _execute_script  # noqa: F401
from smile.server import list_capabilities as _list_capabilities  # noqa: F401

__all__ = ["mcp", "main"]
