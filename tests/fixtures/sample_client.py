"""A fake "existing SDK client" -- used to test register_class. Module-
level so instances (and their bound methods) are picklable across the
sandbox's process boundary."""

from __future__ import annotations


class FakeStripeClient:
    """Stands in for an already-constructed third-party client (already
    holding its own API key/connection state) that a user wants to wrap
    wholesale as SMiLE capabilities."""

    def __init__(self, api_key: str = "sk_test_fake") -> None:
        self.api_key = api_key  # plain attribute, not a capability

    def charge_card(self, amount_cents: int, currency: str = "usd") -> dict:
        """Charge a card for the given amount.

        >>> charge_card(1000)
        """
        return {"charged": amount_cents, "currency": currency}

    def refund(self, charge_id: str) -> dict:
        """Refund a previous charge."""
        return {"refunded": charge_id}

    def _internal_auth_refresh(self) -> None:
        """Should be skipped -- private."""
        return None

    @property
    def account_id(self) -> str:
        """Should be skipped -- a property, not a method."""
        return "acct_123"
