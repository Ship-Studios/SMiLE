"""param_descriptions: collects per-parameter Annotated[...] descriptions
for a capability function, for use in stub rendering."""

from __future__ import annotations

import typing
from typing import Any, Callable

from smile.capabilities.param_description import param_description


def param_descriptions(func: Callable[..., Any]) -> dict[str, str]:
    """Return {param_name: description} for every parameter of `func`
    whose type hint is `Annotated[SomeType, "a description"]`. Params
    without Annotated metadata are omitted -- an empty dict means "render
    the stub exactly as before" (the common, backward-compatible case).

    Degrades to {} rather than raising on a hint that can't be resolved
    (e.g. an unresolvable forward reference) -- this runs on every stub
    render, not just at registration, where validate_signature has
    already guaranteed the signature is sound.
    """
    try:
        hints = typing.get_type_hints(func, include_extras=True)
    except (NameError, TypeError):
        return {}

    return {
        name: desc
        for name, hint in hints.items()
        if (desc := param_description(hint)) is not None
    }
