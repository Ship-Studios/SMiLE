"""worker: the function that runs inside the spawned child process.

Must stay a plain, module-level function (not a closure, not a bound
method of a locally-constructed object) -- multiprocessing's `spawn`
context pickles the `target=` callable by dotted import path to hand it
to the child process, so it has to be importable as
`smile.sandbox.worker.worker`.
"""

from __future__ import annotations

import io
import multiprocessing
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Callable

from smile.sandbox.build_payload import build_payload
from smile.sandbox.build_restricted_globals import build_restricted_globals


def worker(
    code: str,
    capability_namespace: dict[str, Callable[..., Any]],
    extra_names: dict[str, Any],
    result_queue: "multiprocessing.Queue",
) -> None:
    """Runs inside the child process. Executes `code`, captures everything."""
    stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
    return_value: Any = None
    error: str | None = None

    g = build_restricted_globals(capability_namespace, extra_names)
    # `__result__` is how the script hands back a value: assign to it,
    # like a return statement for the whole script.
    g["__result__"] = None

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(code, "<agent_script>", "exec"), g)
        return_value = g.get("__result__")
    except Exception:
        error = traceback.format_exc()

    # build_payload pickles return_value up front and substitutes its repr
    # if that fails -- the substitution has to happen before put(), since
    # put() serializes on a feeder thread where a PicklingError would be
    # invisible here. See build_payload.py.
    result_queue.put(
        build_payload(
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
            return_value=return_value,
            error=error,
        )
    )
