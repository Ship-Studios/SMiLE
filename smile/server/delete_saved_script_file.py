"""delete_saved_script_file: remove one persisted `{name}.json`."""

from __future__ import annotations

from pathlib import Path

from smile.server.saved_script_error import SavedScriptError


def delete_saved_script_file(persist_dir: str, name: str) -> None:
    """Unlink `{persist_dir}/{name}.json`. Missing is fine -- the
    in-memory store is the source of truth for 'is it published'."""
    path = Path(persist_dir) / f"{name}.json"
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise SavedScriptError(
            f"Cannot unpublish '{name}': failed to remove {str(path)!r}: {exc}"
        ) from exc
