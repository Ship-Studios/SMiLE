"""get_customer capability."""

from __future__ import annotations

from smile.example_app.data import CUSTOMERS
from smile.example_app.errors import NotFoundError
from smile.example_app.registry import registry


@registry.register
def get_customer(customer_id: str) -> dict:
    """Look up a customer record by ID. Raises NotFoundError if the
    customer doesn't exist.

    >>> get_customer("cust_1")
    """
    if customer_id not in CUSTOMERS:
        raise NotFoundError(f"No customer with id {customer_id!r}")
    return dict(CUSTOMERS[customer_id])
