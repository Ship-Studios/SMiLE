"""_AsyncCapability: a picklable callable that runs an async capability
function to completion and returns its resolved value.

Field declarations only -- __init__ and __call__ are defined in their own
files (async_capability_init.py, async_capability_call.py) and attached
below, per the project's one-def-per-file rule.

This has to be a module-level class rather than a closure, for the same
reason _HttpCapability is (see smile/capabilities/http_capability.py):
sandbox scripts run in a spawned subprocess, so every capability callable
is pickled to cross that process boundary, and a closure over local
variables cannot be pickled. An instance of a module-level class with a
plain-data attribute (the original async function) pickles fine, as long
as that original function is itself picklable (i.e. also module-level,
not a closure).
"""

from __future__ import annotations

from smile.capabilities.async_capability_call import async_capability_call
from smile.capabilities.async_capability_init import async_capability_init


class _AsyncCapability:
    """A picklable callable that runs an async capability function to
    completion via asyncio.run() and returns its resolved value. See
    module docstring for why this is a class rather than a closure."""


_AsyncCapability.__init__ = async_capability_init
_AsyncCapability.__call__ = async_capability_call
