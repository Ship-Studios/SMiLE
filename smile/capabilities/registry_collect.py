"""CapabilityRegistry.collect implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import inspect
import types
import typing
from typing import Iterable

from smile.capabilities.is_marked_capability import is_marked_capability
from smile.capabilities.registry_register_bulk import registry_register_bulk

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry
    from smile.capabilities.registration_report import RegistrationReport


def registry_collect(
    self: "CapabilityRegistry",
    *modules: types.ModuleType,
    prefix: str = "",
    include: Iterable[str] | None = None,
    exclude: Iterable[str] = (),
    strict: bool = False,
) -> "RegistrationReport":
    """Register every function marked with `@capability` (see
    capability_marker.py) across one or more modules -- the registry-free
    counterpart to register_module, for capabilities that are defined
    without a CapabilityRegistry in scope and gathered centrally later.

    Unmarked functions in the given modules are ignored, even if they're
    otherwise well-typed and documented -- use register_module for
    "everything public in this module" instead. Same include/exclude/
    prefix/strict semantics as register_module, and the same skip-with-
    reason behavior via the returned RegistrationReport.
    """
    report = registry_register_bulk(
        self,
        candidates=(
            (attr_name, attr, None)
            for module in modules
            for attr_name, attr in inspect.getmembers(module, inspect.isfunction)
            if attr.__module__ == module.__name__ and is_marked_capability(attr)
        ),
        prefix=prefix,
        include=include,
        exclude=exclude,
        source="collect",
        strict=strict,
    )
    return report
