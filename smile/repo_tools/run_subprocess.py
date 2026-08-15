"""run_subprocess: shared subprocess execution for every git/gh/test
capability in this package.

Always called with a fixed argument list (never `shell=True`, never a
string built by concatenating caller input) so argv entries go to
execve, not a shell. cwd is REPO_ROOT so results stay scoped to this
repository regardless of where smile-mcp was launched from.

The child starts in its own process group (`start_new_session=True`)
and is killed as a group on timeout or when the sandbox worker is
SIGTERM'd -- otherwise `uv run` / `git` grandchildren outlive the
script. The timeout is also capped at SMILE_TIMEOUT_S so a 120s test
suite cannot be started under a shorter script budget.
"""

from __future__ import annotations

import subprocess

from smile.repo_tools.cap_subprocess_timeout import cap_subprocess_timeout
from smile.repo_tools.install_worker_term_handler import install_worker_term_handler
from smile.repo_tools.kill_process_group import kill_process_group
from smile.repo_tools.register_live_subprocess import register_live_subprocess
from smile.repo_tools.repo_root import REPO_ROOT
from smile.repo_tools.unregister_live_subprocess import unregister_live_subprocess

DEFAULT_TIMEOUT_S = 30


def run_subprocess(argv: list[str], timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    timeout_s = cap_subprocess_timeout(timeout_s)
    install_worker_term_handler()
    try:
        proc = subprocess.Popen(
            argv,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }

    register_live_subprocess(proc)
    try:
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            kill_process_group(proc.pid)
            stdout, stderr = proc.communicate()
            return {
                "returncode": None,
                "stdout": stdout or "",
                "stderr": stderr or "",
                "timed_out": True,
            }
        return {
            "returncode": proc.returncode,
            "stdout": stdout or "",
            "stderr": stderr or "",
            "timed_out": False,
        }
    finally:
        unregister_live_subprocess(proc)
