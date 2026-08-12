"""is_marked_capability: predicate used by registry_collect to find
functions marked with @capability."""

from __future__ import annotations

from typing import Any


def is_marked_capability(obj: Any) -> bool:
    return callable(obj) and hasattr(obj, "__smile_capability__")
