"""Capability.stub_signature method implementation. Attached to the
Capability class in capability.py."""

from __future__ import annotations

import inspect
import typing

from smile.capabilities.param_descriptions import param_descriptions
from smile.capabilities.render_param_descriptions import render_param_descriptions

if typing.TYPE_CHECKING:
    from smile.capabilities.capability import Capability


def capability_stub_signature(self: "Capability") -> str:
    """Render a signature string for this capability, in the exact
    form the agent should write to call it.

    Plain (non-namespaced) capabilities render as a real, syntactically
    valid function stub: `def get_customer(customer_id: str) -> dict: ...`

    Namespaced capabilities (registered with a `prefix=` -- see
    register_module/register_class) are exposed at call time as
    attribute access on a namespace object (`stripe.charge_card(...)`),
    which is NOT valid syntax as a `def` statement (`def
    stripe.charge_card(...)` is a SyntaxError). Those render as a
    call-style signature instead, so the stub always shows exactly
    what the agent should type.

    Parameters typed with `Annotated[SomeType, "a description"]` get an
    extra trailing comment line per parameter, e.g.:

        def charge_card(amount_cents: int) -> dict: ...
        #   amount_cents: amount to charge, in the smallest currency unit

    Capabilities with no Annotated parameters render exactly as before.
    """
    # eval_str=True resolves `from __future__ import annotations` string
    # annotations back to real type objects, so the stub reads as
    # `-> dict` instead of `-> 'dict'`.
    try:
        sig = inspect.signature(self.func, eval_str=True)
    except (ValueError, TypeError, NameError):
        sig = inspect.signature(self.func)
    # Bound methods and spec-generated wrappers may still carry a
    # `self`/positional-only first param that shouldn't be shown.
    # Annotated[SomeType, "a description"] params are unwrapped back to
    # SomeType here -- the description moves to its own trailing comment
    # line (below) instead of being duplicated inline in the signature.
    params = [
        p.replace(annotation=typing.get_args(p.annotation)[0])
        if typing.get_origin(p.annotation) is typing.Annotated
        else p
        for p in sig.parameters.values()
        if p.name != "self"
    ]
    return_annotation = sig.return_annotation
    if typing.get_origin(return_annotation) is typing.Annotated:
        return_annotation = typing.get_args(return_annotation)[0]
    rendered = sig.replace(parameters=params, return_annotation=return_annotation)

    if "." in self.name:
        base = f"{self.name}{rendered}"
    else:
        base = f"def {self.name}{rendered}: ..."

    extra = render_param_descriptions(param_descriptions(self.func))
    if not extra:
        return base
    return f"{base}\n{extra}"
