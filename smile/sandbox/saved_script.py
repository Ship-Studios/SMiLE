"""SavedScript: a callable hydrated inside the sandbox child from a
SavedScriptRecord.

Field declarations only -- __init__ and __call__ live in their own
files and are attached below. Instances are created after spawn, so
they may hold live references to the capability namespace (those
would not be picklable if built in the parent).
"""

from __future__ import annotations

from smile.sandbox.saved_script_call import saved_script_call
from smile.sandbox.saved_script_init import saved_script_init


class SavedScript:
    """A saved agent function, callable as `scripts.<name>(...)`."""


SavedScript.__init__ = saved_script_init
SavedScript.__call__ = saved_script_call
