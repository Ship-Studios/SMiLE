"""Shared in-memory data store for the example CRM capabilities.

Not a function/method, so it's exempt from the one-def-per-file rule --
this is just module-level state shared by every capability in this
package, the same way it was module-level state in the original
single-file example_app.py.
"""

from __future__ import annotations

CUSTOMERS: dict[str, dict] = {
    "cust_1": {"id": "cust_1", "name": "Ada Lovelace", "email": "ada@example.com", "tier": "enterprise"},
    "cust_2": {"id": "cust_2", "name": "Grace Hopper", "email": "grace@example.com", "tier": "starter"},
    "cust_3": {"id": "cust_3", "name": "Alan Turing", "email": "alan@example.com", "tier": "pro"},
}

ORDERS: dict[str, list[dict]] = {
    "cust_1": [
        {"id": "ord_101", "customer_id": "cust_1", "amount": 4200.00, "status": "paid"},
        {"id": "ord_102", "customer_id": "cust_1", "amount": 1800.00, "status": "pending"},
    ],
    "cust_2": [
        {"id": "ord_201", "customer_id": "cust_2", "amount": 99.00, "status": "paid"},
    ],
    "cust_3": [
        {"id": "ord_301", "customer_id": "cust_3", "amount": 650.00, "status": "refunded"},
        {"id": "ord_302", "customer_id": "cust_3", "amount": 650.00, "status": "paid"},
    ],
}

SENT_EMAILS: list[dict] = []
