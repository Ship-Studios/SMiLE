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
    against this `registry` -- reserved namespace taken.

    The capacity check lives solely in ScriptStore.put, under its lock:
    checking capacity here too would be a check-then-act race against
    concurrent execute_script calls (MCP dispatches tool calls from a
    thread pool), since two calls could both pass this outer check
    before either actually inserts. put() is the single source of truth.
    """
    if scripts_namespace_taken(registry):
        raise SavedScriptError(
            f"Cannot save scripts: the capability registry already uses "
            f"the '{SAVED_SCRIPTS_NAMESPACE}' namespace. Rename or "
            f"re-prefix that capability so saved scripts can bind "
            f"'{SAVED_SCRIPTS_NAMESPACE}'."
        )
