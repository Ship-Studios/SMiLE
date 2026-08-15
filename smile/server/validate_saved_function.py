"""validate_saved_function: registration-style checks against an AST
function that is about to be published as `scripts.<name>`."""

from __future__ import annotations

import ast

from smile.server.saved_script_error import SavedScriptError


def validate_saved_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    """Raise SavedScriptError if `node` can't be a saved script: async,
    decorated, missing type hints, or missing a docstring.

    Same bar as CapabilityRegistry._add -- a saved script is advertised
    in list_capabilities with a stub, so an untyped or undocumented
    function would give the agent the same bad catalog entry that
    validate_signature exists to prevent for operator capabilities.
    """
    if isinstance(node, ast.AsyncFunctionDef):
        raise SavedScriptError(
            f"Cannot save '{node.name}': saved scripts cannot be "
            f"`async def`. Write a synchronous function."
        )
    if node.decorator_list:
        raise SavedScriptError(
            f"Cannot save '{node.name}': saved functions cannot have "
            f"decorators. Move that logic into the function body."
        )

    args = node.args
    missing = [
        arg.arg
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)
        if arg.annotation is None
    ]
    if missing:
        raise SavedScriptError(
            f"Cannot save '{node.name}': missing type hints on "
            f"parameter(s) {missing}. Every parameter needs a type hint "
            f"so later scripts (and list_capabilities) can see what to pass."
        )
    if node.returns is None:
        raise SavedScriptError(
            f"Cannot save '{node.name}': missing a return type hint. "
            f"Add one (e.g. `-> dict`, `-> int`) so later scripts know "
            f"what to expect back."
        )

    doc = ast.get_docstring(node)
    if not doc or not doc.strip():
        raise SavedScriptError(
            f"Cannot save '{node.name}': add a docstring. The first "
            f"paragraph becomes the description shown by list_capabilities."
        )
