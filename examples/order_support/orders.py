"""Plain order-lookup functions -- the kind of module a real app already
has, written with no awareness of SMiLE. Registered in full via
registry.register_module() in app.py, which is the point: no rewrite
needed to make an existing module agent-callable.
"""

from __future__ import annotations

_ORDERS: dict[str, dict] = {
    "ord_101": {"id": "ord_101", "customer_id": "cust_1", "amount_cents": 420000, "status": "paid"},
    "ord_102": {"id": "ord_102", "customer_id": "cust_1", "amount_cents": 180000, "status": "pending"},
    "ord_201": {"id": "ord_201", "customer_id": "cust_2", "amount_cents": 9900, "status": "paid"},
    "ord_301": {"id": "ord_301", "customer_id": "cust_3", "amount_cents": 65000, "status": "paid"},
}

_CUSTOMERS: dict[str, dict] = {
    "cust_1": {"id": "cust_1", "name": "Ada Lovelace", "email": "ada@example.com"},
    "cust_2": {"id": "cust_2", "name": "Grace Hopper", "email": "grace@example.com"},
    "cust_3": {"id": "cust_3", "name": "Alan Turing", "email": "alan@example.com"},
}


def get_order(order_id: str) -> dict:
    """Look up an order by ID."""
    if order_id not in _ORDERS:
        raise ValueError(f"No order with id {order_id!r}")
    return dict(_ORDERS[order_id])


def list_orders_for_customer(customer_id: str) -> list[dict]:
    """List every order placed by a customer."""
    return [dict(o) for o in _ORDERS.values() if o["customer_id"] == customer_id]


def get_customer(customer_id: str) -> dict:
    """Look up a customer by ID."""
    if customer_id not in _CUSTOMERS:
        raise ValueError(f"No customer with id {customer_id!r}")
    return dict(_CUSTOMERS[customer_id])


def _internal_audit_dump() -> dict:
    """Not meant to be agent-callable -- register_module skips names
    starting with '_' automatically, which is why this is safe to leave
    in a module that otherwise gets bulk-registered."""
    return {"orders": _ORDERS, "customers": _CUSTOMERS}
