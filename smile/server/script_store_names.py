"""ScriptStore.names implementation. Attached to the ScriptStore class in
script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_names(self: "ScriptStore") -> frozenset[str]:
    """Exposed names including the `scripts.` prefix -- the same keys
    extract_called_capabilities matches against call sites."""
    return frozenset(
        f"{SAVED_SCRIPTS_NAMESPACE}.{record.name}" for record in self._scripts.values()
    )
