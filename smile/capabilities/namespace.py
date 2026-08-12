"""_Namespace: a bare attribute-holding object used to expose
prefix-registered capabilities as attribute access inside the sandbox.

Field declarations only -- its __repr__ is defined in namespace_repr.py
and attached below.
"""

from __future__ import annotations

from smile.capabilities.namespace_repr import namespace_repr


class _Namespace:
    """A bare attribute-holding object, used so prefix-registered
    capabilities (e.g. "crm.get_customer") are callable inside the
    sandbox as `crm.get_customer(...)` rather than requiring dotted
    string keys in globals (which Python doesn't support directly)."""


_Namespace.__repr__ = namespace_repr
