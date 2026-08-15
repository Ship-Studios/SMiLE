"""synthesize_function_example: placeholder call built from an AST
function signature, mirroring synthesize_example for live callables."""

from __future__ import annotations

import ast


def synthesize_function_example(
    node: ast.FunctionDef | ast.AsyncFunctionDef, exposed_name: str
) -> str:
    """Build `scripts.foo(x=...)` from required parameters only."""
    args = node.args
    parts: list[str] = []
    all_pos = list(args.posonlyargs) + list(args.args)
    n_no_default = len(all_pos) - len(args.defaults)
    for arg in all_pos[:n_no_default]:
        parts.append(f"{arg.arg}=...")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        if default is None:
            parts.append(f"{arg.arg}=...")
    return f"{exposed_name}({', '.join(parts)})"
