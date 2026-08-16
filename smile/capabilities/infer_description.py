"""infer_description: pulls a one-line description from a docstring."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from smile.capabilities.first_paragraph import first_paragraph


def infer_description(func: Callable[..., Any]) -> str | None:
    """Pull a one-line description from the function's docstring summary
    (the first paragraph, PEP 257 style) if present."""
    doc = inspect.getdoc(func)
    if not doc:
        return None
    return first_paragraph(doc)
