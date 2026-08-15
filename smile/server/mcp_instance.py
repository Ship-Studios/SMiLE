"""The shared MCPServer instance that every tool function registers
against. Not a function/method -- just the shared object, analogous to
repo_tools/registry.py."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("smile")
