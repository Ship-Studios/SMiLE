"""SavedScript.__init__ implementation. Attached to the SavedScript
class in saved_script.py."""

from __future__ import annotations

import typing
from typing import Any

from smile.sandbox.saved_script_record import SavedScriptRecord

if typing.TYPE_CHECKING:
    from smile.sandbox.saved_script import SavedScript


def saved_script_init(
    self: "SavedScript",
    record: SavedScriptRecord,
    inject: dict[str, Any],
    builtins: Any,
) -> None:
    # Built only inside the sandbox child after spawn, so `inject` may
    # hold live capability callables and the shared `scripts` namespace
    # object. Those references are never pickled.
    self.record = record
    self.inject = inject
    self.builtins = builtins
    self.__name__ = record.name
    self.__doc__ = record.description
    # Compiled lazily on first __call__, not here -- hydrate_saved_scripts
    # constructs a SavedScript for every record in the store on every
    # sandbox spawn, so compiling eagerly would pay parse+compile cost for
    # scripts a given script never calls. Cached on self after that first
    # call so a script invoked repeatedly inside a loop only pays it once.
    self.code = None
