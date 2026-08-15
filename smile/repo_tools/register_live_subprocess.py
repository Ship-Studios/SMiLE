"""register_live_subprocess: track a Popen so the worker SIGTERM
handler can kill its process group."""

from __future__ import annotations

import subprocess

from smile.repo_tools.live_subprocesses import live


def register_live_subprocess(proc: subprocess.Popen) -> None:
    live.append(proc)
