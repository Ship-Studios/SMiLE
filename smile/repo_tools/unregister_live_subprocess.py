"""unregister_live_subprocess: drop a Popen that has finished or been
killed, so the SIGTERM handler does not signal a stale pid."""

from __future__ import annotations

import subprocess

from smile.repo_tools.live_subprocesses import live


def unregister_live_subprocess(proc: subprocess.Popen) -> None:
    try:
        live.remove(proc)
    except ValueError:
        pass
