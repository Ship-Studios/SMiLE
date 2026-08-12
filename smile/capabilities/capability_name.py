"""Capability.name property implementation. Attached to the Capability
class in capability.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.capability import Capability


def capability_name(self: "Capability") -> str:
    """The name this capability is exposed under -- the registered
    `name=`/prefix override if one was given, else the function's own
    `__name__`."""
    return self._name or self.func.__name__
