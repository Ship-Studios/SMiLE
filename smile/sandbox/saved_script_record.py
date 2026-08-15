"""SavedScriptRecord: the picklable data handed across the sandbox
process boundary so the child can hydrate `scripts.*` callables.

A plain dataclass field block -- exempt from the one-def-per-file rule.
Must stay plain data (strings only): spawn pickles this into the child,
and a closure or live function object would fail that pickle the same
way an HTTP capability closure does.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SavedScriptRecord:
    """One saved agent function, ready to inject as `scripts.<name>`."""

    name: str
    """Exposed name without the `scripts.` prefix."""

    func_name: str
    """The `def` name inside `source`, which may differ from `name` when
    the agent saved with `__save__ = "other"`."""

    source: str
    """The function's source only -- not the surrounding script -- so
    re-executing it does not re-run `__result__` / `__save__` side
    effects from the original call."""

    description: str
    """First paragraph of the function's docstring."""

    signature: str
    """Call-style stub, e.g. `scripts.paid_total(customer_id: str) -> int`."""

    example: str
    """A short example call against the exposed name."""
