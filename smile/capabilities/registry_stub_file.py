"""CapabilityRegistry.stub_file implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_stub_file(self: "CapabilityRegistry") -> str:
    """Render the whole registry as a `.pyi`-style stub block.

    This is what gets embedded in execute_script's tool description
    and/or returned by list_capabilities, so the agent can read it the
    way it already reads any Python SDK's type stubs.
    """
    lines = [
        "# Available functions in the sandboxed execution namespace.",
        "# Call these directly -- no imports, no client setup needed.",
        "",
    ]
    for cap in sorted(self._capabilities.values(), key=lambda c: c.name):
        lines.append(f"# {cap.description}")
        lines.append(cap.stub_signature())
        if cap.example:
            lines.append(f"# Example: {cap.example}")
        lines.append("")
    return "\n".join(lines)
