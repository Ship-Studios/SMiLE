"""CapabilityRegistry._add implementation. Attached to the
CapabilityRegistry class in capability_registry.py.

This is the shared internal every registration path funnels through --
does registration-time validation and builds the final Capability
object.
"""

from __future__ import annotations

import inspect
import re
import typing
from typing import Any, Callable

from smile.capabilities.capability import Capability
from smile.capabilities.errors import CapabilityDefinitionError
from smile.capabilities.infer_description import infer_description
from smile.capabilities.infer_example import infer_example
from smile.capabilities.synthesize_example import synthesize_example
from smile.capabilities.validate_no_namespace_shadowing import (
    validate_no_namespace_shadowing,
)
from smile.capabilities.validate_picklable import validate_picklable
from smile.capabilities.validate_signature import validate_signature
from smile.capabilities.wrap_async_capability import wrap_async_capability

if typing.TYPE_CHECKING:
    from smile.capabilities.capability_registry import CapabilityRegistry


def registry_add(
    self: "CapabilityRegistry",
    func: Callable[..., Any],
    *,
    name: str | None = None,
    description: str | None = None,
    example: str | None = None,
    source: str = "decorator",
) -> None:
    # A function marked with @capability (capability_marker.py) carries
    # metadata that acts as a fallback tier: below explicit kwargs passed
    # here, above docstring inference. Bulk paths (register_module et al.)
    # always pass an explicit `name=`, so marker["name"] only ever takes
    # effect for the decorator-only path.
    marker: dict[str, Any] = getattr(func, "__smile_capability__", None) or {}

    exposed_name = name or marker.get("name") or func.__name__

    if exposed_name in self._capabilities:
        existing = self._capabilities[exposed_name]
        raise CapabilityDefinitionError(
            f"Capability name '{exposed_name}' is already registered "
            f"(from {existing.source}). Use a different name, or a "
            f"`prefix=` when bulk-registering, to avoid the collision."
        )

    # Exact-key duplicates are caught above; this catches the subtler
    # flat-vs-namespace collision ("crm" alongside "crm.get_customer")
    # that would otherwise register cleanly and only fail in the sandbox.
    validate_no_namespace_shadowing(self, exposed_name, source)

    validate_signature(func, source=source)

    resolved_description = description or marker.get("description") or infer_description(func)
    if not resolved_description:
        raise CapabilityDefinitionError(
            f"Capability '{exposed_name}' ({source}): no description given and "
            f"none could be inferred -- add a docstring or pass "
            f"description=... explicitly."
        )

    resolved_example = example or marker.get("example") or infer_example(func)
    if resolved_example and func.__name__ != exposed_name:
        # A docstring-sourced example was written against the bare
        # function name before it was registered under a namespace
        # prefix (e.g. "stripe.") -- rewrite the leading call so the
        # example matches how the agent actually has to call it.
        resolved_example = re.sub(
            rf"^{re.escape(func.__name__)}\b", exposed_name, resolved_example
        )
    resolved_example = resolved_example or synthesize_example(func, exposed_name=exposed_name)

    # Description/example are resolved against the original func (above)
    # so docstring inference keeps working -- the wrapper below never
    # needs to look doc-complete on its own. validate_picklable, by
    # contrast, must run against the final (possibly wrapped) func, since
    # that's what's actually pickled into the sandbox namespace.
    if inspect.iscoroutinefunction(func):
        func = wrap_async_capability(func)

    validate_picklable(func, source=source)

    cap = Capability(
        func=func,
        description=resolved_description,
        example=resolved_example,
        source=source,
    )
    cap._name = name
    self._capabilities[exposed_name] = cap
