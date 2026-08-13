"""execute_script MCP tool."""

from __future__ import annotations

from smile.sandbox import run_script
from smile.server.build_execute_script_description import (
    build_execute_script_description,
)
from smile.server.build_tool_response import build_tool_response
from smile.server.mcp_instance import mcp
from smile.server.registry_instance import registry
from smile.server.settings_instance import settings


@mcp.tool(description=build_execute_script_description(registry))
def execute_script(code: str) -> dict:
    """Execute a Python script in a sandboxed environment.

    The agent-facing description for this tool is NOT this docstring --
    it's generated from the served registry by
    build_execute_script_description() and passed to @mcp.tool(above),
    so the capability catalog and worked example always match the
    capabilities actually configured (see load_registry.py). A hardcoded
    docstring here could only ever describe the bundled demo app.
    """
    return build_tool_response(
        run_script(
            code,
            registry.namespace(),
            timeout_s=settings.timeout_s,
            result_budget=settings.result_budget,
            stream_budget=settings.stream_budget,
        )
    )
