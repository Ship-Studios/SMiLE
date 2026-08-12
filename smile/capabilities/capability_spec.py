"""CapabilitySpec: declarative capability definition (JSON/YAML-friendly).

Field declarations only -- its `from_dict` classmethod is defined in
capability_spec_from_dict.py and attached below, per the project's
one-def-per-file rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from smile.capabilities.capability_spec_from_dict import capability_spec_from_dict


@dataclass
class CapabilitySpec:
    """A declarative capability definition -- the JSON/YAML-friendly
    shape for exposing something as a SMiLE capability without writing a
    Python wrapper function by hand.

    Two target kinds are supported:

      - "python": dotted path to an existing callable, e.g.
        "myapp.integrations.stripe.charge_card". Registered as-is,
        subject to the same signature validation as any other capability
        (so it still needs real type hints on the target function).

      - "http": a templated HTTP call. `url_template` may reference
        parameters by name (e.g. "https://api.example.com/orders/{order_id}"),
        and any parameter not consumed by the template is sent as a JSON
        body (POST/PUT/PATCH) or query string (GET/DELETE).

    Parameters are declared explicitly (name -> {type, description,
    required}) since a declarative spec has no function signature to
    infer them from.
    """

    name: str
    description: str
    target: dict[str, Any]  # {"kind": "python"|"http", ...kind-specific fields}
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)
    returns: str = "Any"
    example: str | None = None


CapabilitySpec.from_dict = classmethod(capability_spec_from_dict)
