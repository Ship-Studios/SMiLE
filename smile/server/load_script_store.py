"""load_script_store: build the process ScriptStore from settings,
replaying any persisted `{name}.json` files when SMILE_SCRIPTS_DIR is set.
"""

from __future__ import annotations

import typing

from smile.capabilities.errors import CapabilityDefinitionError
from smile.server.read_persisted_scripts import read_persisted_scripts
from smile.server.script_store import ScriptStore

if typing.TYPE_CHECKING:
    from smile.server.server_settings import ServerSettings


def load_script_store(settings: "ServerSettings") -> ScriptStore:
    """Construct a ScriptStore sized and (optionally) hydrated from
    `settings`. Persisted files are ingested directly into the map so
    startup does not rewrite every file."""
    store = ScriptStore(
        max_scripts=settings.max_saved_scripts,
        persist_dir=settings.scripts_dir,
    )
    if settings.scripts_dir is None:
        return store

    records = read_persisted_scripts(settings.scripts_dir)
    if len(records) > settings.max_saved_scripts:
        raise CapabilityDefinitionError(
            f"SMILE_SCRIPTS_DIR={settings.scripts_dir!r} contains "
            f"{len(records)} saved scripts, more than "
            f"SMILE_MAX_SAVED_SCRIPTS={settings.max_saved_scripts}. "
            f"Raise the limit or remove files from the directory."
        )
    for record in records:
        store._scripts[record.name] = record
    return store
