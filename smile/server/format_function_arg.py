"""format_function_arg: render one AST argument for a stub signature."""

from __future__ import annotations

import ast


def format_function_arg(arg: ast.arg, default: ast.expr | None = None) -> str:
    """Render `name: T` or `name: T = default` from an AST arg."""
    piece = arg.arg
    if arg.annotation is not None:
        piece = f"{piece}: {ast.unparse(arg.annotation)}"
    if default is not None:
        piece = f"{piece} = {ast.unparse(default)}"
    return piece
