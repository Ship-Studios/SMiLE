"""validate_no_namespace_shadowing: registration-time check that a new
capability name can't collide with an existing one once the registry is
flattened into the sandbox namespace."""

from __future__ import annotations

import typing

from smile.capabilities.errors import CapabilityDefinitionError

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def validate_no_namespace_shadowing(
    self: "CapabilityRegistry", exposed_name: str, source: str
) -> None:
    """Raise CapabilityDefinitionError if `exposed_name` would shadow, or
    be shadowed by, a capability already in the registry.

    The plain duplicate-name check in registry_add only catches exact key
    collisions, which misses the case that actually bites: a flat
    capability named `crm` and a prefixed one named `crm.get_customer`
    are different registry keys, so both register happily -- but
    registry_namespace() has to expose the prefixed one as a `_Namespace`
    object bound to the global name `crm`, which overwrites the flat
    callable. Both then appear in list_capabilities(), while calling
    `crm(...)` inside the sandbox fails with "'_Namespace' object is not
    callable". Catching it here keeps the failure at registration time,
    where the fix is obvious, instead of surfacing it to the agent as a
    capability the catalog advertises but the sandbox can't call.
    """
    head = exposed_name.split(".", 1)[0]

    # Case 1: registering "crm" (or "crm.x") when a namespace "crm.*"
    # already exists.
    shadowed = [
        existing
        for existing in self._capabilities
        if existing.split(".", 1)[0] == head and existing != exposed_name
    ]
    conflicting = [
        existing
        for existing in shadowed
        # A collision only occurs when one of the two names is the bare
        # namespace head; two capabilities sharing a prefix (the normal
        # "crm.a" + "crm.b" case) coexist fine as attributes of one object.
        if existing == head or exposed_name == head
    ]

    if conflicting:
        other = conflicting[0]
        flat, namespaced = (exposed_name, other) if exposed_name == head else (other, exposed_name)
        raise CapabilityDefinitionError(
            f"Capability '{exposed_name}' ({source}) collides with "
            f"'{other}': '{flat}' is a plain capability while '{namespaced}' "
            f"needs '{head}' to be a namespace object, so one would silently "
            f"shadow the other inside the sandbox. Rename one of them, or "
            f"register '{flat}' under a `prefix=` of its own."
        )
