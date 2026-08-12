"""list_orders capability."""

from __future__ import annotations

from smile.example_app.data import ORDERS
from smile.example_app.registry import registry


@registry.register
def list_orders(customer_id: str, status: str | None = None) -> list[dict]:
    """List orders for a customer, optionally filtered by status
    ('paid', 'pending', 'refunded').

    >>> list_orders("cust_1", status="paid")
    """
    orders = ORDERS.get(customer_id, [])
    if status is not None:
        orders = [o for o in orders if o["status"] == status]
    return [dict(o) for o in orders]
