"""write_saved_script: persist one SavedScriptRecord as `{name}.json`."""

from __future__ import annotations

import json
from pathlib import Path

from smile.sandbox.saved_script_record import SavedScriptRecord
from smile.server.saved_script_error import SavedScriptError


def write_saved_script(persist_dir: str, record: SavedScriptRecord) -> None:
    """Atomically write `record` to `{persist_dir}/{record.name}.json`.

    The temp-then-replace is so a crash mid-write cannot leave a half
    JSON file that load_script_store would refuse to boot from.
    """
    directory = Path(persist_dir)
    path = directory / f"{record.name}.json"
    payload = {
        "name": record.name,
        "func_name": record.func_name,
        "source": record.source,
        "description": record.description,
        "signature": record.signature,
        "example": record.example,
    }
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2) + "\n")
        tmp.replace(path)
    except OSError as exc:
        raise SavedScriptError(
            f"Cannot save '{record.name}': failed to write "
            f"{str(path)!r}: {exc}"
        ) from exc
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
