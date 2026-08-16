"""description_from_docstring: first-paragraph summary, same shape as
infer_description but from an already-extracted docstring string."""

from __future__ import annotations

from smile.capabilities.first_paragraph import first_paragraph


def description_from_docstring(doc: str) -> str:
    """First paragraph of `doc`, collapsed to one line."""
    return first_paragraph(doc)
