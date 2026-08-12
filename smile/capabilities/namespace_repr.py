"""_Namespace.__repr__ implementation. Attached to the _Namespace class
in namespace.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.namespace import _Namespace


def namespace_repr(self: "_Namespace") -> str:  # pragma: no cover - debugging aid only
    return f"<namespace {sorted(self.__dict__)}>"
