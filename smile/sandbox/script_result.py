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
