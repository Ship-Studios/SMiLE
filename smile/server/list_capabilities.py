"""list_capabilities MCP tool."""

from __future__ import annotations

from smile.server.catalog_with_saved_scripts import catalog_with_saved_scripts
from smile.server.mcp_instance import mcp
from smile.server.registry_instance import registry
from smile.server.script_store_instance import script_store


@mcp.tool()
def list_capabilities() -> list[dict]:
    """List the Python functions available to execute_script.

    Call this first, before writing a script, to see what's callable --
    each entry includes a type-stub signature, a description, and an
    example call. The functions are already in scope inside
    execute_script; do not import them.

    Includes this session's saved scripts (`source="saved_script"`,
    called as `scripts.<name>`) as well as the operator-registered
    capabilities. Saved scripts are not in execute_script's tool
    description -- that text is built once at import -- so this is
    the live catalog.
    """
    return catalog_with_saved_scripts(registry, script_store)
