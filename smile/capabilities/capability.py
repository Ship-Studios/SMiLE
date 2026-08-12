"""Capability: a single callable exposed to sandboxed scripts.

Field declarations only -- its `name` property and `stub_signature`
method are defined in their own files (capability_name.py,
capability_stub_signature.py) and attached below, per the project's
one-def-per-file rule. A bare dataclass field block defines no `def`, so
this file is exempt on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from smile.capabilities.capability_name import capability_name
from smile.capabilities.capability_stub_signature import capability_stub_signature


@dataclass
class Capability:
    """A single callable exposed to sandboxed scripts."""

    func: Callable[..., Any]
    description: str
    # Optional short usage example shown alongside the stub.
    example: str | None = None
    # Where this capability came from -- used only in error messages and
    # in the catalog, to help a large registry's owner trace a capability
    # back to its source (a decorator, a wrapped module, a spec file, ...).
    source: str = "decorator"
    # Overrides the exposed name -- lets register_module/register_class
    # register e.g. "crm.get_customer" while `func.__name__` stays
    # "get_customer".
    _name: str | None = field(default=None, repr=False)


Capability.name = property(capability_name)
Capability.stub_signature = capability_stub_signature
