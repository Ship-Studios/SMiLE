"""CapabilitySpec.from_dict classmethod implementation. Attached to the
CapabilitySpec class in capability_spec.py."""

from __future__ import annotations

import typing
from typing import Any

from smile.capabilities.errors import CapabilityDefinitionError

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_spec import CapabilitySpec


def capability_spec_from_dict(cls: type, data: dict[str, Any]) -> "CapabilitySpec":
    """Build a CapabilitySpec from a plain dict -- the shape a JSON/YAML
    capability definition parses into. Raises CapabilityDefinitionError
    if `name`, `description`, or `target` is missing; `parameters`,
    `returns`, and `example` fall back to their dataclass defaults."""
    required = {"name", "description", "target"}
    missing = required - data.keys()
    if missing:
        raise CapabilityDefinitionError(
            f"Capability spec is missing required field(s): {sorted(missing)}. "
            f"Got keys: {sorted(data.keys())}"
        )
    return cls(
        name=data["name"],
        description=data["description"],
        target=data["target"],
        parameters=data.get("parameters", {}),
        returns=data.get("returns", "Any"),
        example=data.get("example"),
    )
