"""namespace_head_collides: shared predicate for the one namespace
collision that matters once a registry is flattened into the sandbox --
a bare name colliding with something that needs to be a `_Namespace`
object. Used by both operator-capability registration
(validate_no_namespace_shadowing) and saved-script publishing
(scripts_namespace_taken), which both bind a name into the same
flattened sandbox globals and so share the same failure mode.
"""

from __future__ import annotations

from typing import Iterable


def namespace_head_collides(head: str, names: Iterable[str]) -> bool:
    """True if `head`, used as a bare namespace name, would shadow or be
    shadowed by any name in `names` once the sandbox namespace is
    flattened -- i.e. `head` itself is present, or some `head.*` is.

    Ordinary siblings sharing a prefix (`crm.a` + `crm.b`) are not a
    collision; only the bare namespace head participates in one.
    """
    return any(name == head or name.startswith(head + ".") for name in names)
