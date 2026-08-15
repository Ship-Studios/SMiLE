"""require_subprocess_success: turn a failed or timed-out capability
subprocess into a RuntimeError so callers cannot mistake it for empty
success (a clean tree, no commits, etc.)."""

from __future__ import annotations


def require_subprocess_success(result: dict, action: str) -> None:
    """Raise RuntimeError unless `result` is a completed, zero-exit run.

    `action` is the human-facing verb in the error ("git diff", "git log").
    """
    if result["timed_out"]:
        raise RuntimeError(f"{action} timed out")
    if result["returncode"] != 0:
        stderr = result["stderr"] or "(no stderr)"
        raise RuntimeError(f"{action} failed: {stderr}")
