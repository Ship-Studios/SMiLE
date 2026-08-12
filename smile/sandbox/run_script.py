"""run_script: the public entry point for executing agent-authored
Python against a capability namespace in an isolated subprocess."""

from __future__ import annotations

import multiprocessing
from typing import Any, Callable

from smile.sandbox.constants import DEFAULT_TIMEOUT_S
from smile.sandbox.script_result import ScriptResult
from smile.sandbox.worker import worker


def run_script(
    code: str,
    capability_namespace: dict[str, Callable[..., Any]],
    *,
    extra_names: dict[str, Any] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> ScriptResult:
    """Execute `code` in a subprocess with only `capability_namespace`
    (plus a restricted builtins set) available as globals.

    The script communicates its final result by assigning to a special
    `__result__` variable -- this mirrors how a real MCP tool result is a
    single structured value, not stdout text.
    """
    ctx = multiprocessing.get_context("spawn")
    result_queue: multiprocessing.Queue = ctx.Queue()
    proc = ctx.Process(
        target=worker,
        args=(code, capability_namespace, extra_names or {}, result_queue),
    )
    proc.start()
    proc.join(timeout_s)

    if proc.is_alive():
        proc.terminate()
        proc.join(1.0)
        if proc.is_alive():
            proc.kill()
        return ScriptResult(
            stdout="", stderr="", return_value=None,
            error=f"Script exceeded {timeout_s}s timeout and was terminated.",
            timed_out=True,
        )

    try:
        payload = result_queue.get_nowait()
    except Exception:
        # Process died without reporting (e.g. segfault, OOM kill).
        return ScriptResult(
            stdout="", stderr="", return_value=None,
            error=f"Script process exited unexpectedly (code {proc.exitcode}) with no result.",
            timed_out=False,
        )

    return ScriptResult(
        stdout=payload["stdout"],
        stderr=payload["stderr"],
        return_value=payload["return_value"],
        error=payload["error"],
        timed_out=False,
    )
