"""The marking step used by capability_marker -- extracted from what would
otherwise be a nested closure, so it complies with the one-def-per-file
rule. Takes the values the closure would have captured (name, description,
example) as explicit parameters instead."""

from __future__ import annotations

from typing import Any, Callable


def capability_marker_wrap(
    f: Callable[..., Any],
    *,
    name: str | None,
    description: str | None,
    example: str | None,
) -> Callable[..., Any]:
    f.__smile_capability__ = {
        "name": name,
        "description": description,
        "example": example,
    }
    return f
