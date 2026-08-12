"""A stand-in for a third-party payment SDK client -- the kind of object
you'd construct once at app startup, already holding its API key/base
URL/connection. Registered in full via registry.register_class() in
app.py: every public method becomes a capability bound to this instance,
with zero rewriting of the client itself.
"""

from __future__ import annotations


class PaymentClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key  # not a capability -- private, and not typed as one anyway
        self._refunds_issued: list[dict] = []

    def refund(self, order_id: str, amount_cents: int) -> dict:
        """Issue a refund for an order."""
        record = {"order_id": order_id, "amount_cents": amount_cents, "status": "refunded"}
        self._refunds_issued.append(record)
        return record

    def get_refund_total_cents(self) -> int:
        """Total amount refunded so far, in cents, across this client instance."""
        return sum(r["amount_cents"] for r in self._refunds_issued)

    @property
    def api_key_suffix(self) -> str:
        """A property, not a method -- register_class never considers
        this a capability candidate, the same way it skips private
        attributes."""
        return self._api_key[-4:]
