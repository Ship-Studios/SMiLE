"""first_paragraph: PEP 257 summary-paragraph extraction shared by
infer_description.py (operator capabilities, from a live callable's
docstring) and smile/server/description_from_docstring.py (saved
scripts, from an AST-extracted docstring string) -- both want the same
"first paragraph, newlines collapsed" shape, just starting from
different sources.
"""

from __future__ import annotations


def first_paragraph(doc: str) -> str:
    """First paragraph of `doc` (everything up to the first blank line),
    collapsed to one line."""
    first = doc.split("\n\n", 1)[0].strip()
    return " ".join(line.strip() for line in first.splitlines() if line.strip())
