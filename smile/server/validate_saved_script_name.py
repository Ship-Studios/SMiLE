"""validate_saved_script_name: the exposed `scripts.<name>` tail must be
a safe Python identifier."""

from __future__ import annotations

import keyword

from smile.server.saved_script_error import SavedScriptError


def validate_saved_script_name(name: str) -> None:
    """Raise SavedScriptError if `name` cannot be an attribute of the
    `scripts` namespace object."""
    if not name or not name.isidentifier() or keyword.iskeyword(name):
        raise SavedScriptError(
            f"Cannot save as {name!r}: the name must be a Python "
            f"identifier (and not a keyword), so it can be called as "
            f"scripts.{name if name.isidentifier() else 'name'}(...)."
        )
    if name.startswith("_"):
        raise SavedScriptError(
            f"Cannot save as {name!r}: names starting with '_' are reserved."
        )
