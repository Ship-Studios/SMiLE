"""resolve_registry_path: imports and resolves a "module.path:attr"
reference to a CapabilityRegistry instance.

Colon-separated (module.path:attr) rather than resolve_dotted's
last-dot convention (smile/capabilities/resolve_dotted.py), since a
registry reference's module path routinely contains dots of its own
(e.g. "myapp.integrations.registry:registry") and the attribute is
always a plain top-level name, never another dotted lookup -- the colon
makes that split unambiguous instead of guessing at the last dot."""

from __future__ import annotations

import importlib
from typing import Any

from smile.capabilities.errors import CapabilityDefinitionError


def resolve_registry_path(path: str) -> Any:
    """Import and resolve a 'module.path:attr' reference."""
    if ":" not in path:
        raise CapabilityDefinitionError(
            f"'{path}' is not a valid registry reference -- expected "
            f"'module.path:attr_name' (e.g. 'myapp.registry:registry')."
        )
    module_path, attr_name = path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise CapabilityDefinitionError(
            f"Could not import module '{module_path}': {exc}"
        ) from exc
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise CapabilityDefinitionError(
            f"Module '{module_path}' has no attribute '{attr_name}'."
        ) from exc
