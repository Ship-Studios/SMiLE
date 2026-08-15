"""cap_subprocess_timeout: a capability subprocess must not outlive the
sandbox script that spawned it, or execute_script returns a timeout
while the child keeps running."""

from __future__ import annotations

import os

from smile.sandbox.constants import DEFAULT_TIMEOUT_S


def cap_subprocess_timeout(requested_s: float) -> float:
    """Return min(requested, SMILE_TIMEOUT_S), falling back to the sandbox
    default when the env var is unset or unparsable.

    Reads the env var directly rather than importing ServerSettings, so
    repo_tools does not depend on the MCP server package.
    """
    raw = os.environ.get("SMILE_TIMEOUT_S")
    if raw is None or not raw.strip():
        limit = DEFAULT_TIMEOUT_S
    else:
        try:
            parsed = float(raw.strip())
        except ValueError:
            parsed = DEFAULT_TIMEOUT_S
        limit = parsed if parsed > 0 else DEFAULT_TIMEOUT_S
    return min(requested_s, limit)
