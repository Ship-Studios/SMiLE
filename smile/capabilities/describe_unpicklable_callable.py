"""describe_unpicklable_callable: static heuristic that names the specific
reason a callable is likely unpicklable, before any pickling is attempted."""

from __future__ import annotations

import inspect
from typing import Any, Callable


def describe_unpicklable_callable(func: Callable[..., Any]) -> str | None:
    """Return a human-readable diagnosis if `func` matches a known
    unpicklable shape (closure, lambda, or a bound method on a
    locally-defined class), else None.

    None does not mean "definitely picklable" -- it means this heuristic
    found nothing to report; the pickle dry-run in validate_picklable is
    the authoritative check. functools.partial and other wrapper objects
    have no __qualname__, so the qualname-based checks below are skipped
    for them rather than raising.
    """
    if inspect.ismethod(func):
        owner_qualname = getattr(type(func.__self__), "__qualname__", "")
        if "<locals>" in owner_qualname:
            return (
                f"bound method whose instance is of a locally-defined class "
                f"'{owner_qualname}'"
            )

    name = getattr(func, "__name__", None)
    if name == "<lambda>":
        return "a lambda expression"

    qualname = getattr(func, "__qualname__", None)
    if qualname is not None and "<locals>" in qualname:
        return f"a closure or nested function (qualname '{qualname}')"

    return None
