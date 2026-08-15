"""render_function_signature: call-style stub for a saved function."""

from __future__ import annotations

import ast

from smile.server.format_function_arg import format_function_arg


def render_function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef, exposed_name: str
) -> str:
    """Render `scripts.foo(x: int, y: str = 'a') -> int`.

    Namespaced, so this is call-style rather than a `def` statement --
    the same reason capability_stub_signature uses call-style for
    prefixed capabilities.
    """
    args = node.args
    parts: list[str] = []

    all_pos = list(args.posonlyargs) + list(args.args)
    n_no_default = len(all_pos) - len(args.defaults)
    pos_defaults: dict[int, ast.expr] = {
        n_no_default + i: default for i, default in enumerate(args.defaults)
    }

    for i, arg in enumerate(args.posonlyargs):
        parts.append(format_function_arg(arg, pos_defaults.get(i)))
    if args.posonlyargs:
        parts.append("/")

    for i, arg in enumerate(args.args):
        parts.append(format_function_arg(arg, pos_defaults.get(len(args.posonlyargs) + i)))

    if args.vararg is not None:
        var = args.vararg
        if var.annotation is not None:
            parts.append(f"*{var.arg}: {ast.unparse(var.annotation)}")
        else:
            parts.append(f"*{var.arg}")
    elif args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        parts.append(format_function_arg(arg, default))

    if args.kwarg is not None:
        kw = args.kwarg
        if kw.annotation is not None:
            parts.append(f"**{kw.arg}: {ast.unparse(kw.annotation)}")
        else:
            parts.append(f"**{kw.arg}")

    ret = ast.unparse(node.returns) if node.returns is not None else "Any"
    return f"{exposed_name}({', '.join(parts)}) -> {ret}"
