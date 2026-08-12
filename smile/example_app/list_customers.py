"""list_customers capability."""

from __future__ import annotations

from smile.example_app.data import CUSTOMERS
from smile.example_app.registry import registry


@registry.register
def list_customers(tier: str | None = None) -> list[dict]:
    """List all customers, optionally filtered by subscription tier
    ('starter', 'pro', 'enterprise').

    >>> list_customers(tier="enterprise")
    """
    customers = list(CUSTOMERS.values())
    if tier is not None:
        customers = [c for c in customers if c["tier"] == tier]
    return [dict(c) for c in customers]
