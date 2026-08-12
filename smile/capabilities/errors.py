"""CapabilityDefinitionError: raised at registration time. A plain
exception class with no methods of its own -- exempt from the
one-def-per-file rule (it defines zero `def`s)."""

from __future__ import annotations


class CapabilityDefinitionError(ValueError):
    """Raised at registration time when a capability can't be safely
    exposed to the sandbox -- missing type hints, no description
    available, a name collision, etc. Deliberately loud and immediate:
    the alternative is the agent silently getting a bad or empty stub at
    call time, which is a much worse failure to debug.
    """
