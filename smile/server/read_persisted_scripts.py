"""read_persisted_scripts: load every `{name}.json` in a scripts dir."""

from __future__ import annotations

from pathlib import Path

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.parse_saved_script_file import parse_saved_script_file


def read_persisted_scripts(persist_dir: str) -> list[SavedScriptRecord]:
    """Return records for `*.json` files in `persist_dir`, oldest-name
    sort so a full store fails deterministically. Missing directory
    yields an empty list -- load_settings creates the dir when the
    env var is set, but a test can point at an empty path."""
    directory = Path(persist_dir)
    if not directory.is_dir():
        return []
    records: list[SavedScriptRecord] = []
    for path in sorted(directory.glob("*.json")):
        records.append(parse_saved_script_file(path))
    return records
