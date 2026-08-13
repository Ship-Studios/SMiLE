"""await_payload: waits for the child process to deliver its result,
distinguishing a genuine timeout from a child that died without reporting.

This is the parent half of the sandbox's process handoff, and the reason
it can't be a plain `queue.get(timeout=...)`:

  - It must keep *reading* while the child is still writing. A
    multiprocessing.Queue is backed by a pipe with a bounded OS buffer
    (~64KB); the child's feeder thread blocks once that fills, and the
    child cannot exit until the parent drains it. So the parent must not
    join() first -- that deadlocks, and every script producing more than
    a bufferful of output gets reported as a spurious timeout.

  - It must also notice a child that will *never* write. A crashed child
    (segfault, OOM kill, os._exit) does not raise EOFError in the reader
    here -- the queue simply stays empty -- so a single long get() would
    block for the entire timeout and mislabel a crash as a timeout.

Polling the queue in short slices satisfies both: the pipe keeps draining,
and process death is noticed within roughly one slice.
"""

from __future__ import annotations

import multiprocessing
import queue
import time
from typing import Any

from smile.sandbox.constants import DIED_SILENTLY, POLL_INTERVAL_S, TIMED_OUT


def await_payload(
    proc: "multiprocessing.Process",
    result_queue: "multiprocessing.Queue",
    timeout_s: float,
) -> Any:
    """Return the child's result payload, or the TIMED_OUT / DIED_SILENTLY
    sentinel describing why there isn't one.

    The sentinels are module-level singletons rather than None so a script
    that legitimately produces no payload can never be confused with a
    failure to produce one.
    """
    deadline = time.monotonic() + timeout_s

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return TIMED_OUT

        try:
            return result_queue.get(timeout=min(POLL_INTERVAL_S, remaining))
        except queue.Empty:
            pass

        # Empty queue plus a dead process means the result is never coming.
        # Checked only after a failed get(): the child may exit immediately
        # after a successful put(), and that payload is still valid, so the
        # queue must always be given the chance to yield it first.
        if not proc.is_alive():
            try:
                return result_queue.get_nowait()
            except queue.Empty:
                return DIED_SILENTLY
