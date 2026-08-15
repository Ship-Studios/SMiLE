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
    """
    with self._lock:
        if record.name not in self._scripts and len(self._scripts) >= self.max_scripts:
            raise SavedScriptError(
                f"Cannot save '{record.name}': the store already holds "
                f"{self.max_scripts} saved scripts. Overwrite an existing "
                f"name, unpublish one with __unpublish__ = \"...\", or raise "
                f"SMILE_MAX_SAVED_SCRIPTS."
            )
        if self.persist_dir is not None:
            write_saved_script(self.persist_dir, record)
        if record.name in self._scripts:
            del self._scripts[record.name]
        self._scripts[record.name] = record
