"""parse_saved_script_file: load one persisted `{name}.json` into a
SavedScriptRecord. Used at startup; failures are CapabilityDefinitionError
so a corrupt file stops the server rather than silently dropping a
function later scripts still call."""

from __future__ import annotations

import json
from pathlib import Path

from smile.capabilities.errors import CapabilityDefinitionError
from smile.sandbox.saved_script_record import SavedScriptRecord


_REQUIRED = ("name", "func_name", "source", "description", "signature", "example")


def parse_saved_script_file(path: Path) -> SavedScriptRecord:
    """Parse `path` as a SavedScriptRecord. The file stem must match
    the stored `name` so a renamed file cannot publish under the wrong
    attribute."""
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityDefinitionError(
            f"Saved script file {str(path)!r} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CapabilityDefinitionError(
            f"Saved script file {str(path)!r} must be a JSON object, "
            f"not {type(payload).__name__}."
        )
    missing = [key for key in _REQUIRED if key not in payload]
    if missing:
        raise CapabilityDefinitionError(
            f"Saved script file {str(path)!r} is missing field(s) {missing}."
        )
    for key in _REQUIRED:
        if not isinstance(payload[key], str):
            raise CapabilityDefinitionError(
                f"Saved script file {str(path)!r} field {key!r} must be "
                f"a string, not {type(payload[key]).__name__}."
            )
    name = payload["name"]
    if path.stem != name:
        raise CapabilityDefinitionError(
            f"Saved script file {str(path)!r} is named {path.stem!r} "
            f"but its 'name' field is {name!r}. Rename the file or fix "
            f"the field so they match."
        )
    return SavedScriptRecord(
        name=name,
        func_name=payload["func_name"],
        source=payload["source"],
        description=payload["description"],
        signature=payload["signature"],
        example=payload["example"],
    )
