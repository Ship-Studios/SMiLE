"""infer_example: pulls an example call from a docstring."""

from __future__ import annotations

from typing import Any, Callable

from smile.capabilities.constants import DOCTEST_LINE_RE, EXAMPLE_SECTION_RE


def infer_example(func: Callable[..., Any]) -> str | None:
    """Pull an example call from the docstring, if one is written as
    either a doctest-style `>>> ` line or an `Example:` section."""
    import inspect

    doc = inspect.getdoc(func)
    if not doc:
        return None

    doctest_match = DOCTEST_LINE_RE.search(doc)
    if doctest_match:
        return doctest_match.group(1).strip()

    section_match = EXAMPLE_SECTION_RE.search(doc)
    if section_match:
        # First non-blank line of the Example: section.
        for line in section_match.group(1).splitlines():
            if line.strip():
                return line.strip()

    return None
