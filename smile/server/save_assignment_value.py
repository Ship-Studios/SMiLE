"""save_assignment_value: `__save__` specialization of
magic_assignment_value."""

from __future__ import annotations

import ast

from smile.server.constants import SAVE_MAGIC
from smile.server.magic_assignment_value import magic_assignment_value


def save_assignment_value(tree: ast.Module) -> object:
    """Return True, False, a name string, SAVE_ABSENT, or SAVE_INVALID
    for the module-level `__save__` assignment."""
    return magic_assignment_value(tree, SAVE_MAGIC)

