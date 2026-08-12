"""CapabilityRegistry.register_class implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing
from typing import Any, Iterable

from smile.capabilities.registry_register_bulk import registry_register_bulk
from smile.capabilities.registry_register_class_candidates import (
    registry_register_class_candidates,
)

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry
    from smile.capabilities.registration_report import RegistrationReport


def registry_register_class(
    self: "CapabilityRegistry",
    instance: Any,
    *,
    prefix: str = "",
    include: Iterable[str] | None = None,
    exclude: Iterable[str] = (),
    strict: bool = False,
) -> "RegistrationReport":
    """Register every public method on `instance` as a capability,
    bound to that instance.

    This is the "wrap an existing SDK/client" path: point it at an
    already-constructed client object (already holding its API key,
    base URL, connection, etc.) and every public method becomes
    callable from the sandbox with no further wiring.

    Skips (always, regardless of `strict`): dunder/private methods,
    properties, and class attributes that aren't callable -- these
    aren't validation failures, just not method candidates at all.

    Skips (unless `strict=True`, in which case it raises): methods
    that fail capability validation (missing type hints, etc.) --
    bulk-wrapping an existing class routinely hits internal helpers
    that were never meant to be capabilities. Check
    RegistrationReport.skipped either way to see what happened.
    """
    cls_name = type(instance).__name__

    return registry_register_bulk(
        self,
        candidates=registry_register_class_candidates(instance),
        prefix=prefix,
        include=include,
        exclude=exclude,
        source=f"class:{cls_name}",
        strict=strict,
    )
