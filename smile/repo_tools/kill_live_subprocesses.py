"""kill_live_subprocesses: SIGKILL every process group run_subprocess
still has open. Called from the worker SIGTERM handler."""

from __future__ import annotations

from smile.repo_tools.kill_process_group import kill_process_group
from smile.repo_tools.live_subprocesses import live


def kill_live_subprocesses() -> None:
    for proc in list(live):
        if proc.pid is not None:
            kill_process_group(proc.pid)
