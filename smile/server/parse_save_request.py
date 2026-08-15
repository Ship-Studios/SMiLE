"""parse_save_request: turn a script's `__save__` declaration into a
SaveRequest, or None if the script is not trying to publish anything."""

from __future__ import annotations

import ast

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE
from smile.server.constants import (
    MAX_SAVED_SCRIPT_CHARS,
    SAVE_ABSENT,
    SAVE_INVALID,
    SAVE_MAGIC,
)
from smile.server.description_from_docstring import description_from_docstring
from smile.server.function_def_source import function_def_source
from smile.server.render_function_signature import render_function_signature
from smile.server.save_assignment_value import save_assignment_value
from smile.server.save_request import SaveRequest
from smile.server.saved_script_error import SavedScriptError
from smile.server.synthesize_function_example import synthesize_function_example
from smile.server.top_level_function_defs import top_level_function_defs
from smile.server.validate_saved_function import validate_saved_function
from smile.server.validate_saved_script_name import validate_saved_script_name


def parse_save_request(code: str) -> SaveRequest | None:
    """Return a SaveRequest if `code` assigns `__save__ = True` (or a
    name string), else None.

    Syntax errors return None so execute_script's own run_script path
    reports them -- this helper must not steal that error. Every other
    problem with a requested save raises SavedScriptError.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    save_value = save_assignment_value(tree)
    if save_value is SAVE_ABSENT or save_value is False:
        return None
    if save_value is SAVE_INVALID:
        raise SavedScriptError(
            f"{SAVE_MAGIC} must be True or a name string, e.g. "
            f"{SAVE_MAGIC} = True or {SAVE_MAGIC} = \"paid_total\"."
        )

    funcs = top_level_function_defs(tree)
    if not funcs:
        raise SavedScriptError(
            f"{SAVE_MAGIC} is set but the script defines no top-level "
            f"function. Write one `def` with type hints and a docstring."
        )
    if len(funcs) > 1:
        names = [fn.name for fn in funcs]
        raise SavedScriptError(
            f"{SAVE_MAGIC} requires exactly one top-level function; "
            f"found {len(funcs)}: {names}. Nested helpers are fine; "
            f"sibling `def`s are not."
        )

    func = funcs[0]
    validate_saved_function(func)

    if save_value is True:
        name = func.name
    else:
        name = save_value
    validate_saved_script_name(name)

    source = function_def_source(code, func)
    if len(source) > MAX_SAVED_SCRIPT_CHARS:
        raise SavedScriptError(
            f"Cannot save '{name}': function source is {len(source)} "
            f"characters, over the {MAX_SAVED_SCRIPT_CHARS} character limit. "
            f"Shorten it, or split the work across smaller functions."
        )

    doc = ast.get_docstring(func) or ""
    exposed = f"{SAVED_SCRIPTS_NAMESPACE}.{name}"
    return SaveRequest(
        name=name,
        func_name=func.name,
        source=source,
        description=description_from_docstring(doc),
        signature=render_function_signature(func, exposed),
        example=synthesize_function_example(func, exposed),
    )
