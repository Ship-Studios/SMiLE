"""validate_signature: registration-time validation that a function can
be safely exposed as a capability."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from smile.capabilities.errors import CapabilityDefinitionError


def validate_signature(func: Callable[..., Any], *, source: str) -> None:
    """Raise CapabilityDefinitionError if `func` can't be safely exposed:
    every parameter (besides *args/**kwargs) needs a type hint, and so
    does the return value. Without hints the generated stub is either
    misleading (bare `param` with no type) or an agent has to guess the
    shape of the response -- both produce bad scripts."""
    try:
        sig = inspect.signature(func, eval_str=True)
    except (ValueError, TypeError) as exc:
        raise CapabilityDefinitionError(
            f"Capability '{func.__name__}' ({source}): could not inspect signature: {exc}"
        ) from exc
    except NameError as exc:
        raise CapabilityDefinitionError(
            f"Capability '{func.__name__}' ({source}): a type hint references a name "
            f"that isn't defined/importable ({exc}). Check for typos or missing imports "
            f"in the module where this function is defined."
        ) from exc

    missing_params = [
        name
        for name, param in sig.parameters.items()
        if param.annotation is inspect.Parameter.empty
        and param.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and name != "self"
    ]
    if missing_params:
        raise CapabilityDefinitionError(
            f"Capability '{func.__name__}' ({source}): missing type hints on "
            f"parameter(s) {missing_params}. Every parameter needs a type hint so "
            f"the agent can see what to pass."
        )

    if sig.return_annotation is inspect.Signature.empty:
        raise CapabilityDefinitionError(
            f"Capability '{func.__name__}' ({source}): missing a return type hint. "
            f"Add one (e.g. `-> dict`, `-> None`) so the agent knows what to expect back."
        )
