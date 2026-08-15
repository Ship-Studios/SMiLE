"""called_names_in_code: the subset of `known` names that `code` actually
calls. Shared by extract_called_capabilities and its transitive walk of
saved-script bodies.
"""

from __future__ import annotations

import ast
from collections.abc import Collection

from smile.server.dotted_call_name import dotted_call_name


def called_names_in_code(code: str, known: Collection[str]) -> set[str]:
    """Return the set of `known` names that appear as call sites in
    `code`. Unparseable source yields an empty set rather than raising,
    matching extract_called_capabilities.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    called: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = dotted_call_name(node.func)
        if dotted in known:
            called.add(dotted)
    return called
