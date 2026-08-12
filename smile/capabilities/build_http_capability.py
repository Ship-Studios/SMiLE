"""build_http_capability: constructs a picklable HTTP-backed capability
callable from a CapabilitySpec."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from smile.capabilities.capability_spec import CapabilitySpec
from smile.capabilities.constants import PY_TYPE_NAMES
from smile.capabilities.http_capability import _HttpCapability


def build_http_capability(spec: CapabilitySpec) -> Callable[..., Any]:
    """Build a picklable callable that performs the HTTP call described by
    `spec.target`, with a real (annotated) signature synthesized from
    `spec.parameters` so it passes the same validation as any other
    capability."""
    target = spec.target
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
    return_type = PY_TYPE_NAMES.get(spec.returns, Any)
    call.__signature__ = inspect.Signature(sig_params, return_annotation=return_type)
    return call
