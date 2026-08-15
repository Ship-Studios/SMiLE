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
