"""execute_script MCP tool."""

from __future__ import annotations

from smile.server.build_execute_script_description import (
    build_execute_script_description,
)
from smile.server.mcp_instance import mcp
from smile.server.perform_execute_script import perform_execute_script
from smile.server.registry_instance import registry


@mcp.tool(description=build_execute_script_description(registry))
def execute_script(code: str, intent: str) -> dict:
    """Execute a Python script in a sandboxed environment.

    The agent-facing description for this tool is NOT this docstring --
    it's generated from the served registry by
    build_execute_script_description() and passed to @mcp.tool(above),
    so the capability catalog and worked example always match the
    capabilities actually configured (see load_registry.py). A hardcoded
    docstring here could only ever describe one registry, not the one
    actually being served.

    `__save__` (publish a function as `scripts.<name>` for later calls)
    is handled by perform_execute_script, not here -- this file stays
    the thin MCP adapter.
    """
    return perform_execute_script(code, intent)
