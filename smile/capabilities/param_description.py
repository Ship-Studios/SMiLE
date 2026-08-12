"""param_description: extracts a per-parameter description string from a
single resolved type hint, if it's an Annotated[...] type carrying one."""

from __future__ import annotations

import typing
from typing import Any


def param_description(hint: Any) -> str | None:
    """Given one resolved type hint (from typing.get_type_hints(...,
    include_extras=True)), return the first string found in its
    Annotated[...] metadata, e.g. `Annotated[int, "amount in cents"]` ->
    "amount in cents". Returns None if `hint` isn't Annotated, or carries
    no string metadata (non-string metadata, e.g. validator objects, is
    silently ignored rather than erroring).
    """
    if typing.get_origin(hint) is not typing.Annotated:
        return None

    for extra in typing.get_args(hint)[1:]:
        if isinstance(extra, str):
            return extra
    return None
