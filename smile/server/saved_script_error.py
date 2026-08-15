"""SavedScriptError: raised when a script cannot be published into the
session's `scripts.*` namespace. A plain exception class with no methods
of its own -- exempt from the one-def-per-file rule.
"""

from __future__ import annotations


class SavedScriptError(ValueError):
    """Raised when `__save__` is set but the script cannot be published
    -- missing type hints, no docstring, a name collision, a full store,
    a reserved `scripts` namespace already taken by the operator
    registry, etc. Surfaced to the agent as execute_script's `error`
    rather than as an unhandled server exception.
    """
