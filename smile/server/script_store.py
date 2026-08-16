"""ScriptStore: library of agent-saved functions, exposed inside later
execute_script calls as `scripts.<name>(...)`. In-memory by default;
set persist_dir (SMILE_SCRIPTS_DIR) to keep `{name}.json` files.

Field declarations only -- its methods live in their own files and are
attached below, per the project's one-def-per-file rule.

Bounded on purpose, but unlike ResultStore this is reject-when-full
rather than evict-oldest: a saved function is something later scripts
call by name, and silently dropping it would turn `scripts.foo()` into
an AttributeError with no marker that the function used to exist.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass, field

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.constants import MAX_SAVED_SCRIPTS
from smile.server.script_store_delete import script_store_delete
from smile.server.script_store_get import script_store_get
from smile.server.script_store_list import script_store_list
from smile.server.script_store_names import script_store_names
from smile.server.script_store_put import script_store_put
from smile.server.script_store_sources import script_store_sources


@dataclass
class ScriptStore:
    """An in-memory, bounded, insertion-ordered store of saved scripts,
    keyed by the exposed name (without the `scripts.` prefix)."""

    max_scripts: int = MAX_SAVED_SCRIPTS
    """How many scripts to retain before refusing a new name. A field
    rather than a module constant so tests can use a small store without
    monkeypatching, and so the server can size it from
    SMILE_MAX_SAVED_SCRIPTS."""

    persist_dir: str | None = None
    """Directory of `{name}.json` files to keep in sync with put/delete.
    None means in-memory only -- the default, and what tests use."""

    _scripts: "OrderedDict[str, SavedScriptRecord]" = field(default_factory=OrderedDict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    """Guards check-then-insert in put() -- MCP dispatches tool calls
    from a thread pool, so two concurrent execute_script calls saving
    distinct names could otherwise both pass the capacity check before
    either writes, exceeding max_scripts."""

    _reserved: "set[str]" = field(default_factory=set)
    """New names claimed by an in-flight put() that hasn't finished its
    (possibly slow, cross-process-locked) disk write yet. Counted
    against max_scripts in the capacity check so put() doesn't have to
    hold `_lock` across that write, but kept separate from `_scripts`
    so a half-written record is never visible through get()/list()/
    names()/sources()."""


ScriptStore.put = script_store_put
ScriptStore.get = script_store_get
ScriptStore.delete = script_store_delete
ScriptStore.list = script_store_list
ScriptStore.names = script_store_names
ScriptStore.sources = script_store_sources
