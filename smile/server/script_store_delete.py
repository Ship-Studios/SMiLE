"""ScriptStore.delete implementation. Attached to the ScriptStore class
in script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.delete_saved_script_file import delete_saved_script_file
from smile.server.saved_script_error import SavedScriptError

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_delete(self: "ScriptStore", name: str) -> SavedScriptRecord:
    """Remove `name` (no `scripts.` prefix) from the store and, when
    configured, from disk. Raises SavedScriptError if it was never saved.
    """
    if name not in self._scripts:
        raise SavedScriptError(
            f"Cannot unpublish '{name}': no saved script with that name. "
            f"Call list_capabilities() to see scripts.* entries."
        )
    if self.persist_dir is not None:
        delete_saved_script_file(self.persist_dir, name)
    return self._scripts.pop(name)
