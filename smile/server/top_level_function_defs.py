"""top_level_function_defs: the module-level `def` / `async def` nodes
in a parsed script."""

from __future__ import annotations

import ast


def top_level_function_defs(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return top-level function definitions, in source order.

    Nested functions are ignored -- a saved script is one published
    callable, and helpers have to live inside it.
    """
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
