"""_AsyncCapability.__call__ implementation. Attached to the
_AsyncCapability class in async_capability.py."""

from __future__ import annotations

import typing
from typing import Any

if typing.TYPE_CHECKING:
    from smile.capabilities.async_capability import _AsyncCapability


def async_capability_call(self: "_AsyncCapability", *args: Any, **kwargs: Any) -> Any:
    # Sandboxed scripts run inside worker.py's exec(), which has no
    # running event loop -- so asyncio.run() here never conflicts with an
    # existing loop. A fresh loop is created and torn down per call.
    import asyncio

    return asyncio.run(self._func(*args, **kwargs))
