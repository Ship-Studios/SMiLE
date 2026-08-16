"""saved_script_lock_path: shared `.lock` path derivation so
write_saved_script and delete_saved_script_file lock the same file for
the same script name."""

from __future__ import annotations

from pathlib import Path


def saved_script_lock_path(directory: Path, name: str) -> Path:
    """Return the flock path guarding `{directory}/{name}.json`."""
    return (directory / f"{name}.json").with_suffix(".json.lock")
