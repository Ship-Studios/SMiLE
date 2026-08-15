"""CapabilityRegistry.capability_names implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_capability_names(self: "CapabilityRegistry") -> frozenset[str]:
    """The set of exposed names (flat or "namespace.attr") this registry
    knows about -- the same keys `namespace()` binds into the sandbox.

    Public accessor for consumers (e.g. extract_called_capabilities) that
    only need to check membership, so they don't have to reach into the
    private `_capabilities` dict directly.
    """
    return frozenset(self._capabilities.keys())
