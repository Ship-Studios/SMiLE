"""CapabilityRegistry.list_capabilities implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing
from typing import Any

from smile.capabilities.catalog_entry import catalog_entry

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_list_capabilities(self: "CapabilityRegistry") -> list[dict[str, Any]]:
    """Structured catalog for the `list_capabilities` MCP tool."""
    return [
        catalog_entry(
            name=cap.name,
            signature=cap.stub_signature(),
            description=cap.description,
            example=cap.example,
            source=cap.source,
        )
        for cap in sorted(self._capabilities.values(), key=lambda c: c.name)
    ]
