"""CapabilityRegistry.register implementation. Attached to the
CapabilityRegistry class in capability_registry.py."""

from __future__ import annotations

import functools
import typing
from typing import Any, Callable

from smile.capabilities.registry_register_wrap import registry_register_wrap

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_register(
    self: "CapabilityRegistry",
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    example: str | None = None,
):
    """Decorator: register a function as a callable capability.

    `description` and `example` are optional -- if omitted, they're
    inferred from the function's docstring (summary line for the
    description; a `>>> ` doctest line or `Example:` section for the
    example; a synthesized placeholder call if neither is present).

    Usage (fully explicit, same as before):
        @registry.register(description="Look up a customer by ID.")
        def get_customer(customer_id: str) -> dict: ...

    Usage (inferred from docstring -- the common case now):
        @registry.register
        def get_customer(customer_id: str) -> dict:
            '''Look up a customer by ID.

            >>> get_customer("cust_1")
            '''
            ...

    The two call shapes (`@registry.register` bare, vs.
    `@registry.register(description=...)`) are handled without a nested
    `def` -- `functools.partial` binds the registry/name/description/
    example arguments onto `registry_register_wrap` so the returned
    decorator is a plain partial application, not a locally-defined
    closure.
    """
    wrap = functools.partial(
        registry_register_wrap,
        self,
        name=name,
        description=description,
        example=example,
    )

    if func is not None:
        return wrap(func)
    return wrap
