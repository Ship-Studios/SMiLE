"""description_from_docstring: first-paragraph summary, same shape as
infer_description but from an already-extracted docstring string."""

from __future__ import annotations


def description_from_docstring(doc: str) -> str:
    """First paragraph of `doc`, collapsed to one line."""
    first_para = doc.split("\n\n", 1)[0].strip()
    return " ".join(line.strip() for line in first_para.splitlines() if line.strip())
