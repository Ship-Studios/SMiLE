"""write_saved_script: persist one SavedScriptRecord as `{name}.json`."""

from __future__ import annotations

import json
import os
from pathlib import Path

from smile.file_lock import file_lock
from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.saved_script_error import SavedScriptError
from smile.server.saved_script_lock_path import saved_script_lock_path


def write_saved_script(persist_dir: str, record: SavedScriptRecord) -> None:
    """Atomically write `record` to `{persist_dir}/{record.name}.json`.

    The temp-then-replace is so a crash mid-write cannot leave a half
    JSON file that load_script_store would refuse to boot from. The temp
    name includes the PID so two separate server processes sharing the
    same SMILE_SCRIPTS_DIR (e.g. two smile-mcp instances pointed at one
    directory) cannot race on the same tmp path -- ScriptStore's lock
    only guards concurrency within a single process. The `.lock` file
    (POSIX flock, best-effort elsewhere -- see smile/file_lock.py)
    serializes the final replace()/unlink() across those processes (see
    delete_saved_script_file.py, which takes the same lock), so the last
    writer to acquire the lock is also the last to touch the file on
    disk. This does NOT make cross-process SMILE_SCRIPTS_DIR sharing
    fully safe: each process's in-memory ScriptStore is loaded once at
    startup and never re-reads the persist directory, so two processes
    sharing a directory will still serve/report diverging catalogs even
    though the on-disk file itself is race-free.
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
    lock_path = saved_script_lock_path(directory, record.name)
    try:
        with lock_path.open("a+") as lock_handle, file_lock(lock_handle):
            tmp.write_text(json.dumps(payload, indent=2) + "\n")
            tmp.replace(path)
    except OSError as exc:
        raise SavedScriptError(
            f"Cannot save '{record.name}': failed to write "
            f"{str(path)!r}: {exc}"
        ) from exc
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
