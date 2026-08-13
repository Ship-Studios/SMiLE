"""build_payload: assembles the dict the worker sends back to the parent,
guaranteeing it is picklable before it is handed to the queue.

This runs inside the child process. It exists as its own function because
the picklability fallback has to happen *before* `Queue.put()` is called,
not around it: `Queue.put()` serializes on a background feeder thread and
returns immediately, so a `try`/`except` wrapped around the `put()` call
never observes a PicklingError -- the exception surfaces in the feeder
thread, the payload is silently dropped, and the parent sees only a
process that exited with no result. Pickling here, at the call site,
is what makes the fallback actually reachable.
"""

from __future__ import annotations

import pickle
from typing import Any


def build_payload(
    stdout: str,
    stderr: str,
    return_value: Any,
    error: str | None,
) -> dict[str, Any]:
    """Build the result payload, replacing `return_value` with its repr if
    it can't survive the trip across the process boundary.

    A script is free to assign anything at all to `__result__` -- an open
    file handle, a lock, a live SDK client. Those can't be pickled back to
    the parent, but that shouldn't cost the caller the script's stdout,
    stderr, and traceback too. The repr keeps the result legible to the
    agent while the rest of the payload survives intact.

    Note this deliberately does NOT apply the output budgets (see
    truncate_value/truncate_stream). Truncation happens in the parent, so
    the parent still receives the complete value and can offer it as a
    resource the agent can fetch on demand -- truncating here would
    destroy the data before anything had a chance to store it. The cost is
    that a large result crosses the process boundary in full, which is
    bounded work: it's already in memory in the child, and the queue
    handles multi-megabyte payloads fine now that the parent drains it
    while the child writes (see await_payload.py).
    """
    try:
        pickle.dumps(return_value, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        return_value = repr(return_value)

    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_value": return_value,
        "error": error,
    }
