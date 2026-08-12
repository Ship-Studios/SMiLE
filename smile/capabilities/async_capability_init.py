"""_AsyncCapability.__init__ implementation. Attached to the
_AsyncCapability class in async_capability.py."""

from __future__ import annotations

import inspect
import typing
from typing import Any, Callable, Coroutine

if typing.TYPE_CHECKING:
    from smile.capabilities.async_capability import _AsyncCapability


def async_capability_init(
    self: "_AsyncCapability",
    *,
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> None:
    self._func = func
    # __signature__ is captured once, here, so inspect.signature() on this
    # wrapper (used by capability_stub_signature.py / synthesize_example.py)
    # transparently reports the original async function's signature instead
    # of __call__'s (self, *args, **kwargs). eval_str=True resolves
    # `from __future__ import annotations` string annotations back to real
    # type objects, matching what capability_stub_signature.py does when it
    # introspects a capability directly.
    self.__name__ = func.__name__
    self.__doc__ = func.__doc__
    try:
        self.__signature__ = inspect.signature(func, eval_str=True)
    except (ValueError, TypeError, NameError):
        self.__signature__ = inspect.signature(func)
