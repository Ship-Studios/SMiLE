"""parse_unpublish_request: turn a script's `__unpublish__` declaration
into the exposed name to remove, or None if the script is not removing
anything."""

from __future__ import annotations

import ast

from smile.server.constants import (
    SAVE_ABSENT,
    SAVE_INVALID,
    UNPUBLISH_MAGIC,
)
from smile.server.magic_assignment_value import magic_assignment_value
from smile.server.saved_script_error import SavedScriptError
from smile.server.validate_saved_script_name import validate_saved_script_name


def parse_unpublish_request(code: str) -> str | None:
    """Return the exposed name if `code` assigns `__unpublish__ = "name"`,
    else None.

    Syntax errors return None so execute_script's own run_script path
    reports them. `__unpublish__ = True` is invalid -- unlike `__save__`
    there is no function in the script to take the name from.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    value = magic_assignment_value(tree, UNPUBLISH_MAGIC)
    if value is SAVE_ABSENT or value is False:
        return None
    if value is True or value is SAVE_INVALID or not isinstance(value, str):
        raise SavedScriptError(
            f"{UNPUBLISH_MAGIC} must be the name of a saved script, e.g. "
            f'{UNPUBLISH_MAGIC} = "paid_total".'
        )
    validate_saved_script_name(value)
    return value
