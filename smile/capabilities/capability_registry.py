"""CapabilityRegistry: holds the set of capabilities available to
sandboxed scripts.

Field declarations only -- every method is defined in its own file
(registry_register.py, registry_register_module.py, ...) and attached
below, per the project's one-def-per-file rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from smile.capabilities.capability import Capability
from smile.capabilities.registry_add import registry_add
from smile.capabilities.registry_collect import registry_collect
from smile.capabilities.registry_list_capabilities import registry_list_capabilities
from smile.capabilities.registry_load_specs import registry_load_specs
from smile.capabilities.registry_namespace import registry_namespace
from smile.capabilities.registry_register import registry_register
from smile.capabilities.registry_register_bulk import registry_register_bulk
from smile.capabilities.registry_register_class import registry_register_class
from smile.capabilities.registry_register_module import registry_register_module
from smile.capabilities.registry_register_spec import registry_register_spec
from smile.capabilities.registry_stub_file import registry_stub_file


@dataclass
class CapabilityRegistry:
    """Holds the set of capabilities available to sandboxed scripts."""

    _capabilities: dict[str, Capability] = field(default_factory=dict)


CapabilityRegistry.register = registry_register
CapabilityRegistry.register_module = registry_register_module
CapabilityRegistry.register_class = registry_register_class
CapabilityRegistry._register_bulk = registry_register_bulk
CapabilityRegistry.register_spec = registry_register_spec
CapabilityRegistry.load_specs = registry_load_specs
CapabilityRegistry.collect = registry_collect
CapabilityRegistry._add = registry_add
CapabilityRegistry.namespace = registry_namespace
CapabilityRegistry.list_capabilities = registry_list_capabilities
CapabilityRegistry.stub_file = registry_stub_file
