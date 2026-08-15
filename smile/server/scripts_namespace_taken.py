"""scripts_namespace_taken: the operator registry already owns `scripts`
or `scripts.*`, so we must not inject the saved-script namespace."""

from __future__ import annotations

import typing

from smile.sandbox.constants import SAVED_SCRIPTS_NAMESPACE

if typing.TYPE_CHECKING:
    from smile.capabilities import CapabilityRegistry


def scripts_namespace_taken(registry: "CapabilityRegistry") -> bool:
    """True if binding a `scripts` namespace object would shadow, or be
    shadowed by, an operator-registered capability."""
    head = SAVED_SCRIPTS_NAMESPACE
    return any(
        name == head or name.startswith(head + ".")
        for name in registry.capability_names()
    )
