"""synthesize_example: last-resort placeholder example built from a
function's signature."""

from __future__ import annotations

import inspect
from typing import Any, Callable


def synthesize_example(func: Callable[..., Any], *, exposed_name: str) -> str:
    """Last resort: build a placeholder call from the signature so the
    stub always has *something* runnable-looking, even with no docstring.

    Uses `exposed_name` (the registry name, which may carry a namespace
    prefix like "stripe.charge_card") rather than `func.__name__`, so the
    synthesized example always matches how the agent actually calls it.
    """
    try:
        sig = inspect.signature(func, eval_str=True)
    except (ValueError, TypeError, NameError):
        sig = inspect.signature(func)
    args = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.default is not inspect.Parameter.empty:
            continue  # optional params omitted from the synthesized call
        args.append(f'{pname}=...')
    return f"{exposed_name}({', '.join(args)})"
