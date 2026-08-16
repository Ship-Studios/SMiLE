"""ScriptStore.put implementation. Attached to the ScriptStore class in
script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.saved_script_error import SavedScriptError
from smile.server.write_saved_script import write_saved_script

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_put(self: "ScriptStore", record: SavedScriptRecord) -> None:
    """Store `record`, replacing any previous entry with the same name.

    A new name is refused (not evicted-around) once the store is at
    capacity -- overwriting an existing name always succeeds, so the
    agent can iterate on a function without burning a slot.

    The capacity check and dict mutation happen under `self._lock`, but
    the disk write does not: write_saved_script can block indefinitely
    on a cross-process flock (see smile/file_lock.py), and holding
    `self._lock` across that wait would stall every other save in this
    process -- including ones for unrelated names -- if another process
    ever dies or hangs while holding that file lock. Instead a new name
    is reserved in `self._reserved` under the lock first (so a
    concurrent put() for a different new name still sees an accurate
    count without a half-written record ever becoming visible through
    get()/list()/names()/sources()), the slow write happens unlocked,
    and `_scripts` is only mutated under the lock afterward. If the
    write fails, the reservation is released under the lock too.
    """
    with self._lock:
        is_new = record.name not in self._scripts
        if is_new and len(self._scripts) + len(self._reserved) >= self.max_scripts:
            raise SavedScriptError(
                f"Cannot save '{record.name}': the store already holds "
                f"{self.max_scripts} saved scripts. Overwrite an existing "
                f"name, unpublish one with __unpublish__ = \"...\", or raise "
                f"SMILE_MAX_SAVED_SCRIPTS."
            )
        if is_new:
            self._reserved.add(record.name)

    try:
        if self.persist_dir is not None:
            write_saved_script(self.persist_dir, record)
    except BaseException:
        if is_new:
            with self._lock:
                self._reserved.discard(record.name)
        raise

    with self._lock:
        if is_new:
            self._reserved.discard(record.name)
        if record.name in self._scripts:
            del self._scripts[record.name]
        self._scripts[record.name] = record
