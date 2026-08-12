"""main: entry point for running the MCP server (stdio transport)."""

from __future__ import annotations

from smile.server.mcp_instance import mcp


def main() -> None:
    mcp.run()
