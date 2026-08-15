"""kill_process_group: SIGKILL a process group started with
start_new_session=True. The direct child is not enough -- `uv run` and
`git` spawn grandchildren that would otherwise be reparented to PID 1."""

from __future__ import annotations

import os
import signal


def kill_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
