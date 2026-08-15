"""
SMiLE prototype MCP server.

Exposes two tools to any MCP client:

  list_capabilities()
      Returns the structured catalog of functions available inside the
      sandbox -- names, type-stub signatures, descriptions, examples.

  execute_script(code, intent)
      Runs agent-authored Python against that capability namespace in a
      sandboxed subprocess (see smile/sandbox/) and returns stdout/
      stderr/return value/error. `intent` is a required plain-English
      sentence describing the script's goal, logged alongside the
      capabilities the script actually called (see log_intent.py).
      `__save__` / `__unpublish__` publish or remove a function on
      `scripts.*` for later calls (see perform_execute_script.py).

Run with:  uv run mcp dev smile/server/__init__.py   (MCP Inspector, for manual testing)
       or: uv run python3 -m smile.server            (stdio server, for a real client)

The capability set served is resolved once at import time by
load_registry() (registry_instance.py) from environment config, so a
consumer of the packaged smile-mcp entry point can supply their own
capabilities without forking SMiLE -- see load_registry.py for the
SMILE_CAPABILITIES / SMILE_CAPABILITY_SPEC env vars. With neither set,
it falls back to smile.repo_tools's registry for working in this repo.

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

# Import each tool/resource module for its registration side effect.
from smile.server import execute_script as _execute_script  # noqa: F401
from smile.server import full_result_resource as _full_result_resource  # noqa: F401
from smile.server import list_capabilities as _list_capabilities  # noqa: F401

__all__ = ["mcp", "main"]
