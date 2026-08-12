"""wrap_async_capability: builds the picklable sync wrapper for an async
capability function. Called from registry_add.py."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from smile.capabilities.async_capability import _AsyncCapability


def wrap_async_capability(
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> _AsyncCapability:
    return _AsyncCapability(func=func)
