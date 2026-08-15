"""install_worker_term_handler: make SIGTERM kill live capability
subprocesses before the sandbox worker exits.

Installs at most once per process. run_subprocess() calls this on every
invocation (there's no dedicated worker-startup hook to call it from --
smile/sandbox/worker.py is capability-agnostic and shouldn't know about
repo_tools-specific setup), so the guard is what keeps that from being
a redundant signal.signal() syscall on every git/gh/test call.
"""

from __future__ import annotations

import signal

from smile.repo_tools.on_worker_sigterm import on_worker_sigterm

_installed = False


def install_worker_term_handler() -> None:
    global _installed
    if _installed:
        return
    signal.signal(signal.SIGTERM, on_worker_sigterm)
    _installed = True
