"""hydrate_saved_scripts: bind `scripts.<name>` callables into the
sandbox globals from picklable SavedScriptRecords.

Runs inside the child, after spawn -- that is why the resulting
SavedScript instances may close over the live capability namespace.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from smile.capabilities.namespace import _Namespace
from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE
from smile.sandbox.saved_script import SavedScript
from smile.sandbox.saved_script_record import SavedScriptRecord


def hydrate_saved_scripts(
    sandbox_globals: dict[str, Any],
    records: Sequence[SavedScriptRecord],
) -> None:
    """Inject a `scripts` namespace object into `sandbox_globals`.

    Raises RuntimeError if `scripts` is already bound -- the parent is
    supposed to skip hydration when the operator registry owns that
    name; this is the child's last line of defense against a silent
    overwrite.
    """
    if SAVED_SCRIPTS_NAMESPACE in sandbox_globals:
        raise RuntimeError(
            f"Cannot inject saved scripts: {SAVED_SCRIPTS_NAMESPACE!r} "
            f"is already bound in the sandbox namespace."
        )

    inject = {
        key: value
        for key, value in sandbox_globals.items()
        if key not in {"__builtins__", "__result__"}
    }
    scripts_ns = _Namespace()
    inject[SAVED_SCRIPTS_NAMESPACE] = scripts_ns
    builtins = sandbox_globals["__builtins__"]
    for record in records:
        scripts_ns.__dict__[record.name] = SavedScript(record, inject, builtins)
    sandbox_globals[SAVED_SCRIPTS_NAMESPACE] = scripts_ns
