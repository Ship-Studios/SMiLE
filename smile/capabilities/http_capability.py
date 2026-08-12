"""_HttpCapability: a picklable callable that performs the HTTP call
described by a CapabilitySpec's "http" target.

Field declarations only -- __init__ and __call__ are defined in their
own files (http_capability_init.py, http_capability_call.py) and
attached below, per the project's one-def-per-file rule.

This has to be a module-level class rather than a closure: sandbox
scripts run in a spawned subprocess (see smile/sandbox/), so every
capability callable is pickled to cross that process boundary. A
closure over local variables (the obvious way to write this) cannot be
pickled -- `AttributeError: Can't get local object '...'.<locals>.
_call'` -- because pickle can only reference module-level names. An
instance of a module-level class with plain-data attributes pickles
fine; __call__ does what the closure would have done. Attaching
__init__/__call__ after class definition (rather than defining them
inline) doesn't change this -- pickle only needs the class itself to be
importable by dotted path, which it still is.
"""

from __future__ import annotations

from smile.capabilities.http_capability_call import http_capability_call
from smile.capabilities.http_capability_init import http_capability_init


class _HttpCapability:
    """A picklable callable that performs the HTTP call described by a
    CapabilitySpec's "http" target. See module docstring for why this
    is a class rather than a closure."""


_HttpCapability.__init__ = http_capability_init
_HttpCapability.__call__ = http_capability_call
