"""ScriptResult: the outcome of running a script via run_script()."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScriptResult:
    stdout: str
    stderr: str
    return_value: Any
    error: str | None  # formatted traceback, if the script raised
    timed_out: bool
