"""build_script_result: turns the raw child payload into a ScriptResult,
applying the output budgets that keep a result from overrunning the
agent's context window."""

from __future__ import annotations

from typing import Any

from smile.sandbox.script_result import ScriptResult
from smile.sandbox.truncate_stream import truncate_stream
from smile.sandbox.truncate_value import truncate_value


def build_script_result(
    payload: dict[str, Any],
    result_budget: int,
    stream_budget: int,
) -> ScriptResult:
    """Apply the output budgets to a completed child payload.

    Runs in the parent, after the full payload has crossed the process
    boundary, so the complete result is still available to hand to a
    resource store even when the agent-facing copy is truncated. A budget
    of 0 disables that cap entirely.
    """
    stdout, stderr = payload["stdout"], payload["stderr"]
    full_value = payload["return_value"]

    if stream_budget:
        new_stdout = truncate_stream(stdout, stream_budget, "stdout")
        new_stderr = truncate_stream(stderr, stream_budget, "stderr")
    else:
        new_stdout, new_stderr = stdout, stderr

    if result_budget:
        return_value, truncation = truncate_value(full_value, result_budget)
    else:
        return_value, truncation = full_value, None

    return ScriptResult(
        stdout=new_stdout,
        stderr=new_stderr,
        return_value=return_value,
        error=payload["error"],
        timed_out=False,
        truncation=truncation,
        # Only retained when it differs from what the agent sees -- holding
        # a second reference to an untruncated result would keep a large
        # object alive for no reason.
        full_return_value=full_value if truncation else None,
        stdout_truncated=new_stdout != stdout,
        stderr_truncated=new_stderr != stderr,
    )
