"""function_def_source: recover a function's source from the script it
was parsed out of."""

from __future__ import annotations

import ast


def function_def_source(
    code: str, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> str:
    """Return the original source of `node`, falling back to ast.unparse
    if the segment can't be recovered (e.g. the tree was synthesized)."""
    segment = ast.get_source_segment(code, node)
    if segment is not None:
        return segment
    return ast.unparse(node)
