"""run_script: the public entry point for executing agent-authored
Python against a capability namespace in an isolated subprocess."""

from __future__ import annotations

import multiprocessing
from typing import Any, Callable

from smile.sandbox.await_payload import await_payload
from smile.sandbox.build_script_result import build_script_result
from smile.sandbox.constants import (
    DEFAULT_RESULT_BUDGET,
    DEFAULT_STREAM_BUDGET,
    DEFAULT_TIMEOUT_S,
    DIED_SILENTLY as _DIED_SILENTLY,
    REAP_TIMEOUT_S as _REAP_TIMEOUT_S,
    TIMED_OUT as _TIMED_OUT,
)
from smile.sandbox.script_result import ScriptResult
from smile.sandbox.terminate_process import terminate_process
from smile.sandbox.worker import worker


def run_script(
    code: str,
    capability_namespace: dict[str, Callable[..., Any]],
    *,
    extra_names: dict[str, Any] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    result_budget: int = DEFAULT_RESULT_BUDGET,
    stream_budget: int = DEFAULT_STREAM_BUDGET,
) -> ScriptResult:
    """Execute `code` in a subprocess with only `capability_namespace`
    (plus a restricted builtins set) available as globals.

    The script communicates its final result by assigning to a special
    `__result__` variable -- this mirrors how a real MCP tool result is a
    single structured value, not stdout text.

    A result larger than `result_budget` characters is replaced with a
    summary describing what was omitted; the complete value is preserved
    on `ScriptResult.full_return_value` so a caller can offer it as a
    fetchable resource instead of forcing it into the agent's context.
    Streams over `stream_budget` are excerpted head+tail. Pass a budget of
    0 to disable the corresponding cap (useful for library callers that
    aren't feeding an LLM).
    """
    ctx = multiprocessing.get_context("spawn")
    result_queue: multiprocessing.Queue = ctx.Queue()
    proc = ctx.Process(
        target=worker,
        args=(code, capability_namespace, extra_names or {}, result_queue),
    )
    proc.start()

    # Read the result BEFORE joining, not after -- joining first deadlocks
    # on any script whose output exceeds the queue's ~64KB pipe buffer.
    # See await_payload.py for the full explanation of both failure modes
    # it handles.
    payload = await_payload(proc, result_queue, timeout_s)

    if payload is _TIMED_OUT:
        terminate_process(proc)
        return ScriptResult(
            stdout="", stderr="", return_value=None,
            error=f"Script exceeded {timeout_s}s timeout and was terminated.",
            timed_out=True,
        )

    if payload is _DIED_SILENTLY:
        # The child died without reporting (segfault, OOM kill, os._exit).
        # Distinct from a timeout, and must not be reported as one.
        return ScriptResult(
            stdout="", stderr="", return_value=None,
            error=f"Script process exited unexpectedly (code {proc.exitcode}) with no result.",
            timed_out=False,
        )

    # The payload is in hand, so the child has finished its work and is
    # exiting; this join only reaps it. The short grace period covers the
    # gap between the final put() and actual process exit.
    proc.join(_REAP_TIMEOUT_S)
    if proc.is_alive():
        terminate_process(proc)

    return build_script_result(payload, result_budget, stream_budget)
