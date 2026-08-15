"""validate_saved_script: store/registry policy checks that parse-time
validation of the function body cannot see."""

from __future__ import annotations

import typing

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE
from smile.server.save_request import SaveRequest
from smile.server.saved_script_error import SavedScriptError
from smile.server.scripts_namespace_taken import scripts_namespace_taken

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry
    from smile.server.script_store import ScriptStore


def validate_saved_script(
    request: SaveRequest,
    registry: "CapabilityRegistry",
    store: "ScriptStore",
) -> None:
    """Raise SavedScriptError if `request` cannot be put in `store`
    against this `registry` -- reserved namespace taken, or the store
    is at capacity and this is a new name."""
    if scripts_namespace_taken(registry):
        raise SavedScriptError(
            f"Cannot save scripts: the capability registry already uses "
            f"the '{SAVED_SCRIPTS_NAMESPACE}' namespace. Rename or "
            f"re-prefix that capability so saved scripts can bind "
            f"'{SAVED_SCRIPTS_NAMESPACE}'."
        )
    existing = {record.name for record in store.list()}
    if request.name not in existing and len(existing) >= store.max_scripts:
        raise SavedScriptError(
            f"Cannot save '{request.name}': the store already holds "
            f"{store.max_scripts} saved scripts. Overwrite an existing "
            f"name, unpublish one with __unpublish__ = \"...\", or raise "
            f"SMILE_MAX_SAVED_SCRIPTS."
        )
