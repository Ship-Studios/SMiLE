"""terminate_process: shuts down a sandbox child process that is still
alive, escalating from SIGTERM to SIGKILL if it doesn't go quietly."""

from __future__ import annotations

import multiprocessing

from smile.sandbox.constants import REAP_TIMEOUT_S


def terminate_process(proc: "multiprocessing.Process") -> None:
    """Terminate `proc`, escalating to kill() if it ignores terminate().

    A script stuck in a tight C-level loop, or one that has installed a
    SIGTERM handler, may not die on terminate() alone -- kill() is the
    backstop so run_script can never leave an orphaned sandbox process
    behind holding the timeout budget of every subsequent call.
    """
    if not proc.is_alive():
        return

    proc.terminate()
    proc.join(REAP_TIMEOUT_S)
    if proc.is_alive():
        proc.kill()
        proc.join(REAP_TIMEOUT_S)
