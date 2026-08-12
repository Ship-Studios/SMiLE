"""The candidate-method-finding step used by
CapabilityRegistry.register_class -- extracted from what was originally
a nested closure (`_candidates`) inside `register_class` so it complies
with the one-def-per-file rule. Takes `instance` as an explicit
parameter instead of capturing it."""

from __future__ import annotations

import inspect
from typing import Any, Iterator


def registry_register_class_candidates(
    instance: Any,
) -> Iterator[tuple[str, Any, None]]:
    for attr_name in dir(instance):
        if attr_name.startswith("_"):
            continue
        attr = getattr(instance, attr_name)
        if not callable(attr) or inspect.isclass(attr):
            continue
        # Bound methods only -- skip plain data attributes that
        # happen to hold something callable-looking.
        if not (inspect.ismethod(attr) or inspect.isfunction(attr)):
            continue
        yield attr_name, attr, None
