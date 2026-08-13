"""describe_shape: a compact, human/agent-readable description of a
value's structure, used in truncation notes."""

from __future__ import annotations

from typing import Any

from smile.sandbox.constants import SHAPE_KEY_SAMPLE


def describe_shape(value: Any) -> str:
    """Describe `value`'s structure without reproducing its contents.

    This is what lets a truncation note stay useful while staying small:
    the agent can't see 10,000 rows, but "list of 10000 dicts with keys
    ['id', 'name', 'email', 'tier']" tells it enough to write a script
    that aggregates them correctly on the next attempt.
    """
    if isinstance(value, list):
        if not value:
            return "empty list"
        first = value[0]
        if isinstance(first, dict):
            keys = list(first)[:SHAPE_KEY_SAMPLE]
            suffix = ", ..." if len(first) > SHAPE_KEY_SAMPLE else ""
            return f"list of {len(value):,} dicts with keys {keys}{suffix}"
        return f"list of {len(value):,} {type(first).__name__} values"

    if isinstance(value, dict):
        keys = list(value)[:SHAPE_KEY_SAMPLE]
        suffix = ", ..." if len(value) > SHAPE_KEY_SAMPLE else ""
        return f"dict with {len(value):,} keys {keys}{suffix}"

    if isinstance(value, str):
        return f"string of {len(value):,} characters"

    return f"{type(value).__name__} value"
