"""validate_no_namespace_shadowing: registration-time check that a new
capability name can't collide with an existing one once the registry is
flattened into the sandbox namespace."""

from __future__ import annotations

import typing

from smile.capabilities.errors import CapabilityDefinitionError
from smile.capabilities.namespace_head_collides import namespace_head_collides

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
    # registry_add already rejects an exact-key duplicate of exposed_name
    # before this runs, so self._capabilities cannot contain it here.
    existing_names = list(self._capabilities)
    is_bare_head = exposed_name == head

    # Only the bare namespace head participates in a collision (two
    # capabilities sharing a prefix, e.g. "crm.a" + "crm.b", coexist fine
    # as attributes of one object), so this only needs to check in the
    # direction that's actually being registered: either exposed_name
    # itself is the bare head and some "head.*" already exists, or
    # exposed_name is "head.*" and the bare "head" already exists.
    if is_bare_head:
        collides = namespace_head_collides(head, existing_names)
    else:
        collides = head in existing_names

    if collides:
        if is_bare_head:
            other = next(existing for existing in existing_names if existing.startswith(head + "."))
        else:
            other = head
        flat, namespaced = (exposed_name, other) if is_bare_head else (other, exposed_name)
        raise CapabilityDefinitionError(
            f"Capability '{exposed_name}' ({source}) collides with "
            f"'{other}': '{flat}' is a plain capability while '{namespaced}' "
            f"needs '{head}' to be a namespace object, so one would silently "
            f"shadow the other inside the sandbox. Rename one of them, or "
            f"register '{flat}' under a `prefix=` of its own."
        )
