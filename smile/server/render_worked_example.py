"""render_worked_example: builds the short worked example embedded in
execute_script's tool description. Split into its own module per the
project's one-def-per-file rule."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry


def render_worked_example(registry: "CapabilityRegistry") -> str:
    """Build a short, runnable-looking script from the first capability in
    the catalog, so the agent sees the `__result__` convention
    demonstrated against real capability names rather than invented ones.

    Returns "" for an empty registry, where any example would have to be
    fabricated -- an example naming a nonexistent function is worse than
    no example, since the agent may copy it verbatim.
    """
    capabilities = registry.list_capabilities()
    if not capabilities:
        return ""

    first = capabilities[0]
    call = first["example"] or f"{first['name']}()"
    return f"    result = {call}\n    __result__ = result"
