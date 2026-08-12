"""resolve_dotted: imports and resolves a dotted path to a callable."""

from __future__ import annotations

from typing import Any

from smile.capabilities.errors import CapabilityDefinitionError


def resolve_dotted(path: str) -> Any:
    """Import and resolve a dotted path like 'pkg.module.func_or_class'."""
    import importlib

    if "." not in path:
        raise CapabilityDefinitionError(
            f"'{path}' is not a valid dotted path (need at least 'module.name')."
        )
    module_path, attr_name = path.rsplit(".", 1)
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise CapabilityDefinitionError(f"Could not import module '{module_path}': {exc}") from exc
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise CapabilityDefinitionError(
            f"Module '{module_path}' has no attribute '{attr_name}'."
        ) from exc
