"""file_lock: best-effort POSIX flock context manager shared by every
caller that needs to serialize concurrent processes touching one file.

`fcntl` doesn't exist on Windows; importing it at module level would
break every importer unconditionally, so the import is optional and
locking degrades to a no-op (best-effort, racy under concurrent
callers) rather than taking the whole process down.
"""

from __future__ import annotations

import contextlib
import typing

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]


@contextlib.contextmanager
def file_lock(handle: typing.IO[typing.Any]) -> typing.Iterator[None]:
    """Hold an exclusive lock on `handle` for the duration of the `with`
    block. No-op when `fcntl` is unavailable (non-POSIX platforms)."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
