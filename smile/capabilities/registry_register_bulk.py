"""CapabilityRegistry._register_bulk implementation. Attached to the
CapabilityRegistry class in capability_registry.py.

Shared internal used by register_module and register_class."""

from __future__ import annotations

import typing
from typing import Any, Callable, Iterable

from smile.capabilities.errors import CapabilityDefinitionError
from smile.capabilities.registration_report import RegistrationReport

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_register_bulk(
    self: "CapabilityRegistry",
    *,
    candidates: Iterable[tuple[str, Callable[..., Any], None]],
    prefix: str,
    include: Iterable[str] | None,
    exclude: Iterable[str],
    source: str,
    strict: bool,
) -> RegistrationReport:
    include_set = set(include) if include is not None else None
    exclude_set = set(exclude)
    report = RegistrationReport()

    for attr_name, attr, _ in candidates:
        if attr_name.startswith("_"):
            continue
        if include_set is not None and attr_name not in include_set:
            continue
        if attr_name in exclude_set:
            continue

        exposed_name = f"{prefix}{attr_name}"
        try:
            self._add(attr, name=exposed_name, source=source)
            report.registered.append(exposed_name)
        except CapabilityDefinitionError as exc:
            if strict:
                raise
            report.skipped.append((exposed_name, str(exc)))

    return report
