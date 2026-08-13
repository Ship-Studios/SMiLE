"""ScriptResult: the outcome of running a script via run_script()."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScriptResult:
    """The outcome of one `run_script()` call."""

    stdout: str
    """Everything the script wrote to stdout."""

    stderr: str
    """Everything the script wrote to stderr."""

    return_value: Any
    """The value assigned to `__result__` in the script, or `None` if
    the script never assigned it (or raised before reaching the
    assignment)."""

    error: str | None
    """A formatted traceback if the script raised an unhandled
    exception, else `None`."""

    timed_out: bool
    """`True` if the script exceeded `timeout_s` and was terminated --
    `error` is set to an explanatory message in that case too."""

    truncation: dict[str, Any] | None = None
    """Set when `return_value` was too large for the output budget and was
    replaced with a summary. Holds the original shape, how many items were
    omitted, and guidance for the agent. `None` means `return_value` is
    complete."""

    full_return_value: Any = None
    """The complete, untruncated result, kept server-side so it can be
    offered as a fetchable resource rather than forced into the agent's
    context. Only meaningful when `truncation` is set; callers that just
    want what the agent should see want `return_value`."""

    stdout_truncated: bool = False
    """`True` if `stdout` is an excerpt rather than the whole stream."""

    stderr_truncated: bool = False
    """`True` if `stderr` is an excerpt rather than the whole stream."""
