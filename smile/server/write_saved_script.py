"""write_saved_script: persist one SavedScriptRecord as `{name}.json`."""

from __future__ import annotations

import json
import os
from pathlib import Path

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.saved_script_error import SavedScriptError

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]


def write_saved_script(persist_dir: str, record: SavedScriptRecord) -> None:
    """Atomically write `record` to `{persist_dir}/{record.name}.json`.

    The temp-then-replace is so a crash mid-write cannot leave a half
    JSON file that load_script_store would refuse to boot from. The temp
    name includes the PID so two separate server processes sharing the
    same SMILE_SCRIPTS_DIR (e.g. two smile-mcp instances pointed at one
    directory) cannot race on the same tmp path -- ScriptStore's lock
    only guards concurrency within a single process. The `.lock` file
    (POSIX flock, best-effort elsewhere -- see enforce_run_tests_interval
    for the same tradeoff) serializes the final replace() itself across
    those processes, so the last writer to acquire the lock is also the
    last to replace() -- without it, two processes could interleave
    replace() calls in an order that leaves the on-disk file not matching
    either process's in-memory ScriptStore.
    """
    directory = Path(persist_dir)
    path = directory / f"{record.name}.json"
    payload = {
        "name": record.name,
        "func_name": record.func_name,
        "source": record.source,
        "description": record.description,
        "signature": record.signature,
        "example": record.example,
    }
    tmp = path.with_suffix(f".json.{os.getpid()}.tmp")
    lock_path = path.with_suffix(".json.lock")
    try:
        with lock_path.open("a+") as lock_handle:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                tmp.write_text(json.dumps(payload, indent=2) + "\n")
                tmp.replace(path)
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        raise SavedScriptError(
            f"Cannot save '{record.name}': failed to write "
            f"{str(path)!r}: {exc}"
        ) from exc
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
