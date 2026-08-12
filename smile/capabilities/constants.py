"""Shared constants and compiled regexes for the capabilities package. No
functions/methods here -- exempt from the one-def-per-file rule."""

from __future__ import annotations

import re
from typing import Any

# Recognizes a Google/NumPy-ish "Example:" section, or a doctest-style
# ">>> " line, whichever comes first. Either becomes the example string.
EXAMPLE_SECTION_RE = re.compile(r"^\s*Example[s]?:\s*\n(.+)", re.MULTILINE | re.DOTALL)
DOCTEST_LINE_RE = re.compile(r"^\s*>>>\s*(.+)$", re.MULTILINE)

PY_TYPE_NAMES = {
    "str": str, "int": int, "float": float, "bool": bool, "dict": dict,
    "list": list, "None": type(None), "Any": Any,
}
