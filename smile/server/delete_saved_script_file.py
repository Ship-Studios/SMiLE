"""delete_saved_script_file: remove one persisted `{name}.json`."""

from __future__ import annotations

from pathlib import Path

from smile.file_lock import file_lock
from smile.server.saved_script_error import SavedScriptError
from smile.server.saved_script_lock_path import saved_script_lock_path


def delete_saved_script_file(persist_dir: str, name: str) -> None:
    """Unlink `{persist_dir}/{name}.json`. Missing is fine -- the
    in-memory store is the source of truth for 'is it published'.

    Takes the same flock write_saved_script uses for this name, so a
    concurrent save and unpublish of one script across two processes
    sharing SMILE_SCRIPTS_DIR are mutually exclusive rather than racing
    unlink() against replace().
    """
    directory = Path(persist_dir)
    path = directory / f"{name}.json"
    lock_path = saved_script_lock_path(directory, name)
    try:
        with lock_path.open("a+") as lock_handle, file_lock(lock_handle):
            path.unlink(missing_ok=True)
    except OSError as exc:
        raise SavedScriptError(
            f"Cannot unpublish '{name}': failed to remove {str(path)!r}: {exc}"
        ) from exc
