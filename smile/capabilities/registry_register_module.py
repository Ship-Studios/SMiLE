"""CapabilityRegistry.register_module implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import inspect
import types
import typing
from typing import Iterable

from smile.capabilities.registry_register_bulk import registry_register_bulk

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry
    from smile.capabilities.registration_report import RegistrationReport


def registry_register_module(
    self: "CapabilityRegistry",
    module: types.ModuleType,
    *,
    prefix: str = "",
    include: Iterable[str] | None = None,
    exclude: Iterable[str] = (),
    strict: bool = False,
) -> "RegistrationReport":
    """Register every public, top-level function in `module` as a
    capability.

    `include`/`exclude` filter by the function's own name (not the
    prefixed name). `prefix` is prepended to every registered name
    (e.g. prefix="crm." turns get_customer into "crm.get_customer") --
    useful when wrapping several modules that might otherwise collide.

    By default, functions that fail validation (missing type hints,
    etc.) are skipped rather than aborting the whole module -- bulk-
    wrapping existing code routinely hits functions that were never
    meant to be capabilities. Pass `strict=True` to raise on the
    first failure instead. Either way, check the returned
    RegistrationReport.skipped to see what didn't make it in and why.
    """
    return registry_register_bulk(
        self,
        candidates=(
            (attr_name, attr, None)
            for attr_name, attr in inspect.getmembers(module, inspect.isfunction)
            if attr.__module__ == module.__name__  # skip re-exported functions
        ),
        prefix=prefix,
        include=include,
        exclude=exclude,
        source=f"module:{module.__name__}",
        strict=strict,
    )
