"""magic_assignment_value: finds a module-level assignment to a magic
name (`__save__`, `__unpublish__`) and returns its constant value.
"""

from __future__ import annotations

import ast

from smile.server.constants import SAVE_ABSENT, SAVE_INVALID


def magic_assignment_value(tree: ast.Module, magic: str) -> object:
    """Return True, False, a name string, SAVE_ABSENT, or SAVE_INVALID.

    Only simple module-level `<magic> = <constant>` (or an annotated
    assignment of the same shape) counts. A value computed at runtime
    is invalid -- these are publish declarations, not data-plane flags.
    The last such assignment wins, matching Python's own name binding.
    """
    found: object = SAVE_ABSENT
    for node in tree.body:
        value_node: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == magic:
                value_node = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == magic
            and node.value is not None
        ):
            value_node = node.value
        if value_node is None:
            continue
        if isinstance(value_node, ast.Constant) and value_node.value is False:
            found = False
        elif isinstance(value_node, ast.Constant) and value_node.value is True:
            found = True
        elif isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            found = value_node.value
        else:
            found = SAVE_INVALID
    return found
