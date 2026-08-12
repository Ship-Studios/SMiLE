"""validate_picklable: registration-time check that a capability callable
will survive being pickled across the sandbox's multiprocessing.spawn
process boundary."""

from __future__ import annotations

import pickle
from typing import Any, Callable

from smile.capabilities.describe_unpicklable_callable import (
    describe_unpicklable_callable,
)
from smile.capabilities.errors import CapabilityDefinitionError


def validate_picklable(func: Callable[..., Any], *, source: str) -> None:
    """Raise CapabilityDefinitionError if `func` can't be pickled.

    smile/sandbox/ runs scripts in a multiprocessing.spawn subprocess,
    which pickles the entire capability namespace to hand it across the
    process boundary -- so every registered capability must be picklable.
    Without this check, an unpicklable capability (most commonly a
    closure or lambda) registers fine and only fails much later, deep
    inside a spawned subprocess, as a raw pickle/AttributeError far from
    the actual mistake.

    A cheap static heuristic (describe_unpicklable_callable) runs first
    to produce a specific, actionable diagnosis when it recognizes a
    known-bad shape. A pickle.dumps() dry-run then runs unconditionally
    as the authoritative check -- pickling a plain function reference is
    cheap (it serializes a module+qualname reference, not the function
    body), so this is negligible overhead for capabilities that are
    registered once at startup.
    """
    diagnosis = describe_unpicklable_callable(func)

    try:
        pickle.dumps(func, protocol=pickle.HIGHEST_PROTOCOL)
    except (pickle.PicklingError, AttributeError, TypeError) as exc:
        name = getattr(func, "__name__", repr(func))
        reason = f" it is {diagnosis}." if diagnosis else f" {exc}"
        raise CapabilityDefinitionError(
            f"Capability '{name}' ({source}) can't be registered:{reason} "
            f"Sandboxed scripts run in a separate subprocess, so every "
            f"capability callable must be picklable -- define it as a "
            f"plain module-level function, or (for stateful wrappers) an "
            f"instance of a module-level class with plain-data __init__ "
            f"state, not a closure. See _HttpCapability in "
            f"smile/capabilities/http_capability.py for the pattern to "
            f"follow."
        ) from exc
