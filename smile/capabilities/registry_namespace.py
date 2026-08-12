"""CapabilityRegistry.namespace implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import typing
from typing import Any, Callable

from smile.capabilities.namespace import _Namespace

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_namespace(self: "CapabilityRegistry") -> dict[str, Callable[..., Any]]:
    """The {name: callable} dict to inject into the sandbox globals.

    Names may contain dots (e.g. "crm.get_customer") when registered
    via a prefix -- the sandbox exposes those as attribute access on
    a lightweight namespace object, not literal dotted globals, so
    `crm.get_customer(...)` works as written.
    """
    flat: dict[str, Callable[..., Any]] = {}
    namespaces: dict[str, _Namespace] = {}

    for exposed_name, cap in self._capabilities.items():
        if "." not in exposed_name:
            flat[exposed_name] = cap.func
            continue
        ns_name, attr_name = exposed_name.split(".", 1)
        namespaces.setdefault(ns_name, _Namespace()).__dict__[attr_name] = cap.func

    flat.update(namespaces)
    return flat
