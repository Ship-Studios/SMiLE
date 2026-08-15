"""ScriptStore.get implementation. Attached to the ScriptStore class in
script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.constants import SCRIPT_MISSING

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_get(
    self: "ScriptStore", name: str
) -> SavedScriptRecord | object:
    """Return the stored record for `name` (no `scripts.` prefix), or
    the SCRIPT_MISSING sentinel if it was never saved."""
    return self._scripts.get(name, SCRIPT_MISSING)
