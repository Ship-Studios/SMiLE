"""enforce_run_tests_interval: file-backed floor between run_tests calls.

Uses flock (POSIX only) so concurrent execute_script children cannot
each pass the check against a stale stamp. `fcntl` doesn't exist on
Windows; importing it at module level would break every capability in
the default registry (repo_tools/__init__.py imports this module
unconditionally), not just run_tests(), so the import is optional and
the interval check degrades to unlocked (best-effort, racy under
concurrent callers) rather than taking the whole server down.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]


def enforce_run_tests_interval(min_interval_s: float, stamp_path: Path) -> None:
    """Raise RuntimeError if the previous run was fewer than
    `min_interval_s` seconds ago. Records `time.time()` on success so
    later processes can see it.
    """
    stamp_path.touch(exist_ok=True)
    with stamp_path.open("r+") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        raw = handle.read().strip()
        now = time.time()
        if raw:
            try:
                last = float(raw)
            except ValueError:
                last = None
            if last is not None:
                elapsed = now - last
                if elapsed < min_interval_s:
                    wait_s = min_interval_s - elapsed
                    raise RuntimeError(
                        f"run_tests() was called too recently; "
                        f"wait {wait_s:.0f}s before retrying."
                    )
        handle.seek(0)
        handle.truncate()
        handle.write(f"{now}\n")
        handle.flush()
        os.fsync(handle.fileno())
