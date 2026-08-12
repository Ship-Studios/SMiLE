"""CapabilityRegistry.load_specs implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import json
import typing
from pathlib import Path

from smile.capabilities.capability_spec import CapabilitySpec
from smile.capabilities.errors import CapabilityDefinitionError

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_load_specs(self: "CapabilityRegistry", path: str | Path) -> list[str]:
    """Load one or more CapabilitySpecs from a JSON or YAML file and
    register them all. The file may contain a single spec object or a
    list of spec objects (optionally under a top-level "capabilities"
    key). Returns the list of registered names.
    """
    path = Path(path)
    text = path.read_text()

    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise CapabilityDefinitionError(
                "Loading YAML capability specs requires PyYAML "
                "(`uv add pyyaml`)."
            ) from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    if isinstance(data, dict) and "capabilities" in data:
        data = data["capabilities"]
    if isinstance(data, dict):
        data = [data]

    registered = []
    for item in data:
        spec = CapabilitySpec.from_dict(item)
        self.register_spec(spec)
        registered.append(spec.name)
    return registered
