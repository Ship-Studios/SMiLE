"""ScriptStore.list implementation. Attached to the ScriptStore class in
script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.saved_script_record import SavedScriptRecord

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_list(self: "ScriptStore") -> list[SavedScriptRecord]:
    """Saved records in insertion order (oldest first)."""
    return list(self._scripts.values())
