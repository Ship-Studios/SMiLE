"""Capability.name property implementation. Attached to the Capability
class in capability.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.capability import Capability


def capability_name(self: "Capability") -> str:
    return self._name or self.func.__name__
