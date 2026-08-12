"""load_registry: resolves the CapabilityRegistry the server should
expose, from environment configuration -- so a consumer of the
smile-mcp entry point can supply their own capability set without
forking or editing SMiLE itself."""

from __future__ import annotations

import os

from smile.capabilities import CapabilityRegistry
from smile.capabilities.errors import CapabilityDefinitionError
from smile.server.resolve_registry_path import resolve_registry_path

ENV_CAPABILITIES = "SMILE_CAPABILITIES"
ENV_CAPABILITY_SPEC = "SMILE_CAPABILITY_SPEC"


def load_registry() -> CapabilityRegistry:
    """Build the registry smile-mcp serves, from environment config:

      SMILE_CAPABILITIES=pkg.module.path:registry_attr
          A "module.path:attr" reference to a consumer-owned
          CapabilityRegistry instance -- for capability sets authored in
          Python (decorators, register_module, register_class).
          Importing the module is expected to register everything, the
          same way importing smile.example_app does.

      SMILE_CAPABILITY_SPEC=/path/to/capabilities.yaml
          Path to a JSON/YAML capability spec file (see
          CapabilityRegistry.load_specs) -- for capability sets with no
          Python wrapper code at all.

    Setting both is an error -- pick one source. Setting neither falls
    back to smile.example_app's registry (the bundled demo capability
    set), preserving the pre-existing default behavior.
    """
    dotted_path = os.environ.get(ENV_CAPABILITIES)
    spec_path = os.environ.get(ENV_CAPABILITY_SPEC)

    if dotted_path and spec_path:
        raise CapabilityDefinitionError(
            f"Both {ENV_CAPABILITIES} and {ENV_CAPABILITY_SPEC} are set -- "
            f"pick one capability source, not both."
        )

    if dotted_path:
        registry = resolve_registry_path(dotted_path)
        if not isinstance(registry, CapabilityRegistry):
            raise CapabilityDefinitionError(
                f"{ENV_CAPABILITIES}='{dotted_path}' resolved to "
                f"{type(registry).__name__}, not a CapabilityRegistry."
            )
        return registry

    if spec_path:
        registry = CapabilityRegistry()
        registry.load_specs(spec_path)
        return registry

    from smile.example_app import registry as default_registry

    return default_registry
