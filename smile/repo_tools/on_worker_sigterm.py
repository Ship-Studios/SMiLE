"""on_worker_sigterm: kill capability subprocess groups, then die.

The sandbox parent only SIGTERMs this worker; grandchildren started
with start_new_session=True will not see that signal unless we forward
it here.
"""

from __future__ import annotations

import os
import signal

from smile.repo_tools.kill_live_subprocesses import kill_live_subprocesses


def on_worker_sigterm(signum: int, frame: object) -> None:
    kill_live_subprocesses()
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)
