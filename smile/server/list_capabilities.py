"""list_capabilities MCP tool."""

from __future__ import annotations

from smile.example_app import registry
from smile.server.mcp_instance import mcp


@mcp.tool()
def list_capabilities() -> list[dict]:
    """List the Python functions available to execute_script.

    Call this first, before writing a script, to see what's callable --
    each entry includes a type-stub signature, a description, and an
    example call. The functions are already in scope inside
    execute_script; do not import them.
    """
    return registry.list_capabilities()
