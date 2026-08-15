"""ScriptStore.sources implementation. Attached to the ScriptStore class
in script_store.py."""

from __future__ import annotations

import typing

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE

if typing.TYPE_CHECKING:
    from smile.server.script_store import ScriptStore


def script_store_sources(self: "ScriptStore") -> dict[str, str]:
    """Map `scripts.<name>` -> function source, for transitive capability
    extraction."""
    return {
        f"{SAVED_SCRIPTS_NAMESPACE}.{record.name}": record.source
        for record in self._scripts.values()
    }
