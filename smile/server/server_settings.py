"""ServerSettings: the runtime knobs a consumer can tune via environment
variables in .mcp.json.

A plain dataclass field block with no methods -- exempt from the
one-def-per-file rule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServerSettings:
    """Resolved runtime configuration for the MCP server.

    Frozen because these are read once at import time and shared by every
    tool call -- mutating them mid-flight would change behavior between
    calls with nothing recording that it happened.
    """

    result_budget: int
    """Max characters of `return_value` returned inline; 0 disables
    truncation."""

    stream_budget: int
    """Max characters of stdout/stderr returned each; 0 disables
    truncation."""

    timeout_s: float
    """Seconds a sandboxed script may run before termination."""

    max_stored_results: int
    """How many full results are retained for resource fetches before the
    oldest are evicted."""

    intent_log_path: str
    """File each execute_script call's intent/capability-usage record is
    appended to, as one JSON line per call."""

    max_saved_scripts: int
    """How many saved scripts the session library may hold before a new
    name is refused."""

    scripts_dir: str | None
    """Directory of persisted `{name}.json` saved scripts, or None for
    an in-memory store that dies with the process."""
