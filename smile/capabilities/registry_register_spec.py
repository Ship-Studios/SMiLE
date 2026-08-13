"""CapabilityRegistry.register_spec implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing

from smile.capabilities.build_http_capability import build_http_capability
from smile.capabilities.capability_spec import CapabilitySpec
from smile.capabilities.errors import CapabilityDefinitionError
from smile.capabilities.resolve_dotted import resolve_dotted

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_register_spec(self: "CapabilityRegistry", spec: CapabilitySpec) -> None:
    """Register a single declarative CapabilitySpec."""
    target_kind = spec.target.get("kind")
    if target_kind == "python":
        if "path" not in spec.target:
            raise CapabilityDefinitionError(
                f"Capability '{spec.name}': target kind 'python' requires a "
                f"'path' field (a dotted path to the callable, e.g. "
                f"'myapp.integrations.stripe.charge_card'). Got keys: "
                f"{sorted(spec.target)}"
            )
        func = resolve_dotted(spec.target["path"])
        if not callable(func):
            raise CapabilityDefinitionError(
                f"Capability '{spec.name}': target '{spec.target['path']}' is not callable."
            )
    elif target_kind == "http":
        func = build_http_capability(spec)
    else:
        raise CapabilityDefinitionError(
            f"Capability '{spec.name}': unknown target kind {target_kind!r} "
            f"(expected 'python' or 'http')."
        )

    self._add(
        func,
        name=spec.name,
        description=spec.description,
        example=spec.example,
        source=f"spec:{target_kind}",
    )
