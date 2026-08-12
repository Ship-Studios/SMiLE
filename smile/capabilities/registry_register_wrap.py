"""The wrapping step used by CapabilityRegistry.register -- extracted
from what was originally a nested closure (`_wrap`) inside `register` so
it complies with the one-def-per-file rule. Takes the values the closure
used to capture (`registry`, `name`, `description`, `example`) as
explicit parameters instead."""

from __future__ import annotations

import typing
from typing import Any, Callable

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_register_wrap(
    registry: "CapabilityRegistry",
    f: Callable[..., Any],
    *,
    name: str | None,
    description: str | None,
    example: str | None,
) -> Callable[..., Any]:
    registry._add(
        f,
        name=name,
        description=description,
        example=example,
        source="decorator",
    )
    return f
