"""validate_picklable: registration-time check that a capability callable
will survive being pickled across the sandbox's multiprocessing.spawn
process boundary."""

from __future__ import annotations

import pickle
import sys
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
    known-bad shape. A pickle.dumps() dry-run then runs as the
    authoritative check for everything else -- pickling a plain function
    reference is cheap (it serializes a module+qualname reference, not
    the function body), so this is negligible overhead for capabilities
    that are registered once at startup.

    pickle resolves a plain function by looking it up as an attribute of
    its defining module (`getattr(sys.modules[func.__module__],
    func.__qualname__)`). For the common `@registry.register` pattern,
    validate_picklable runs *during* that module's own top-level
    execution -- the `def`/decorator statement hasn't finished, so the
    name isn't in the module's namespace yet, and the lookup fails even
    though the function is a perfectly ordinary, picklable, module-level
    function that will be bound under that exact name by the time the
    module finishes importing (i.e. before anything ever actually
    pickles it). That specific failure shape is treated as picklable
    rather than an error; every other pickling failure still raises.
    """
    diagnosis = describe_unpicklable_callable(func)

    try:
        pickle.dumps(func, protocol=pickle.HIGHEST_PROTOCOL)
    except (pickle.PicklingError, AttributeError, TypeError) as exc:
        if diagnosis is None and _pending_module_binding(func):
            return
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


def _pending_module_binding(func: Callable[..., Any]) -> bool:
    """True if `func` is a plain top-level function whose defining
    module is still executing (so it isn't in the module's namespace
    yet under its own name) -- the specific, benign cause of a pickle
    dry-run failure that validate_picklable should not treat as a real
    unpicklability error. describe_unpicklable_callable has already
    ruled out closures/lambdas/locally-defined-class methods by the time
    this runs, so a qualname with no '<locals>' really is a module-level
    function.
    """
    module_name = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None)
    if not module_name or not qualname or "<locals>" in qualname:
        return False

    module = sys.modules.get(module_name)
    if module is None:
        return False

    return getattr(module, qualname, None) is not func
