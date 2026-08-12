"""capability_marker: a registry-free decorator that marks a function as
capability-ready without registering it anywhere. Exported as `capability`
from smile.capabilities.

Lets capabilities be defined across many files/modules with no
CapabilityRegistry in scope, then collected centrally later via
registry.collect(*modules) (smile/capabilities/registry_collect.py).
"""

from __future__ import annotations

import functools
from typing import Any, Callable

from smile.capabilities.capability_marker_wrap import capability_marker_wrap


def capability_marker(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    example: str | None = None,
):
    """Decorator: mark a function as capability-ready, for later collection
    by `registry.collect(module)`. Does not register the function anywhere
    by itself.

    Usage (bare):
        @capability
        def get_customer(customer_id: str) -> dict:
            '''Look up a customer by ID.'''
            ...

    Usage (with explicit metadata):
        @capability(description="Look up a customer by ID.")
        def get_customer(customer_id: str) -> dict: ...

    `description`/`example` given here are used as a fallback by
    CapabilityRegistry._add() -- below explicit registration-time kwargs,
    above docstring inference -- so they apply whether the function is
    later picked up by `registry.collect(...)` or registered directly via
    `@registry.register`.

    The two call shapes are handled without a nested `def`, the same way
    registry_register.py does: functools.partial binds the metadata kwargs
    onto capability_marker_wrap so the returned decorator is a plain
    partial application, not a locally-defined closure (which also matters
    here since a marked function must stay picklable).
    """
    wrap = functools.partial(
        capability_marker_wrap,
        name=name,
        description=description,
        example=example,
    )

    if func is not None:
        return wrap(func)
    return wrap
