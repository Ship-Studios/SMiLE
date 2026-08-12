"""build_restricted_globals: assembles the globals dict a sandboxed
script executes against -- a restricted builtins set plus the injected
capability namespace."""

from __future__ import annotations

from typing import Any, Callable

from smile.sandbox.constants import SAFE_BUILTIN_NAMES


def build_restricted_globals(
    capability_namespace: dict[str, Callable[..., Any]],
    extra_names: dict[str, Any],
) -> dict[str, Any]:
    import builtins as _builtins_module

    safe_builtins = {
        name: getattr(_builtins_module, name)
        for name in SAFE_BUILTIN_NAMES
        if hasattr(_builtins_module, name)
    }
    g: dict[str, Any] = {"__builtins__": safe_builtins}
    g.update(capability_namespace)
    g.update(extra_names)
    return g
