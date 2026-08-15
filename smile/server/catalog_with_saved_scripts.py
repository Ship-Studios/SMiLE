"""catalog_with_saved_scripts: list_capabilities entries for the
operator registry plus this session's saved scripts."""

from __future__ import annotations

import typing
from typing import Any

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE
from smile.server.constants import SOURCE_SAVED_SCRIPT

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry
    from smile.server.script_store import ScriptStore


def catalog_with_saved_scripts(
    registry: "CapabilityRegistry", store: "ScriptStore"
) -> list[dict[str, Any]]:
    """Structured catalog: operator capabilities, then saved scripts,
    sorted by name so a newly saved function is not glued to the end
    where an agent skimming the top would miss it."""
    entries = list(registry.list_capabilities())
    for record in store.list():
        entries.append(
            {
                "name": f"{SAVED_SCRIPTS_NAMESPACE}.{record.name}",
                "signature": record.signature,
                "description": record.description,
                "example": record.example,
                "source": SOURCE_SAVED_SCRIPT,
            }
        )
    entries.sort(key=lambda entry: entry["name"])
    return entries
