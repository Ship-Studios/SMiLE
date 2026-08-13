"""build_http_capability: constructs a picklable HTTP-backed capability
callable from a CapabilitySpec."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from smile.capabilities.capability_spec import CapabilitySpec
from smile.capabilities.constants import PY_TYPE_NAMES
from smile.capabilities.errors import CapabilityDefinitionError
from smile.capabilities.http_capability import _HttpCapability


def build_http_capability(spec: CapabilitySpec) -> Callable[..., Any]:
    """Build a picklable callable that performs the HTTP call described by
    `spec.target`, with a real (annotated) signature synthesized from
    `spec.parameters` so it passes the same validation as any other
    capability."""
    target = spec.target
    if "url_template" not in target:
        raise CapabilityDefinitionError(
            f"Capability '{spec.name}': target kind 'http' requires a "
            f"'url_template' field (e.g. "
            f"'https://api.example.com/orders/{{order_id}}'). Got keys: "
            f"{sorted(target)}"
        )
    call = _HttpCapability(
        name=spec.name,
        description=spec.description,
        method=target.get("method", "GET").upper(),
        url_template=target["url_template"],
        headers=target.get("headers", {}),
        timeout_s=target.get("timeout_s", 10.0),
    )

    # Synthesize a real signature (with annotations) so the validator and
    # the stub generator work exactly as they would for a hand-written
    # function -- this is what lets an HTTP-backed capability show up
    # with a proper `def name(order_id: str) -> Any: ...` stub instead of
    # a bare `**kwargs`.
    sig_params = []
    for pname, pinfo in spec.parameters.items():
        py_type = PY_TYPE_NAMES.get(pinfo.get("type", "Any"), Any)
        required = pinfo.get("required", True)
        default = inspect.Parameter.empty if required else pinfo.get("default")
        sig_params.append(
            inspect.Parameter(
                pname,
                kind=inspect.Parameter.KEYWORD_ONLY,
                annotation=py_type,
                default=default,
            )
        )
    # Every {placeholder} in the URL must correspond to a declared
    # parameter, or the .format() in http_capability_call raises a bare
    # KeyError at call time -- inside the sandbox, where the agent sees an
    # opaque traceback for what is really a typo in the spec file.
    undeclared = sorted(call._template_params - set(spec.parameters))
    if undeclared:
        raise CapabilityDefinitionError(
            f"Capability '{spec.name}': url_template references "
            f"{undeclared}, which {'is' if len(undeclared) == 1 else 'are'} "
            f"not declared in `parameters` "
            f"({sorted(spec.parameters) or 'none declared'}). Add "
            f"{'it' if len(undeclared) == 1 else 'them'} to `parameters`, or "
            f"fix the placeholder name in the template."
        )

    return_type = PY_TYPE_NAMES.get(spec.returns, Any)
    call.__signature__ = inspect.Signature(sig_params, return_annotation=return_type)
    return call
