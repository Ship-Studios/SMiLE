"""infer_description: pulls a one-line description from a docstring."""

from __future__ import annotations

import inspect
from typing import Any, Callable


def infer_description(func: Callable[..., Any]) -> str | None:
    """Pull a one-line description from the function's docstring summary
    (the first paragraph, PEP 257 style) if present."""
    doc = inspect.getdoc(func)
    if not doc:
        return None
    # First paragraph = everything up to the first blank line.
    first_para = doc.split("\n\n", 1)[0].strip()
    # Collapse internal newlines/indentation into a single line.
    return " ".join(line.strip() for line in first_para.splitlines() if line.strip())
