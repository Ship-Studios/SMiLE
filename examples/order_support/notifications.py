"""Notification capabilities. Two different registration paths on purpose:

  - send_refund_email is registered directly with @registry.register in
    app.py (the common case for a fresh, SMiLE-aware function) and is
    `async def` -- SMiLE runs it to completion transparently, no asyncio
    awareness needed in the agent's script.

  - log_support_action is marked with @capability and picked up later by
    registry.collect() in app.py, showing the registry-free path: this
    module has no CapabilityRegistry import or reference at all.
"""

from __future__ import annotations

import asyncio

from smile.capabilities import capability

_SENT_EMAILS: list[dict] = []
_ACTION_LOG: list[str] = []


async def send_refund_email(customer_email: str, order_id: str, amount_cents: int) -> dict:
    """Email a customer confirming their refund. Simulates network I/O
    with a short async sleep, the way a real email-provider SDK call
    would await a response.
    """
    await asyncio.sleep(0)  # stand-in for an awaited HTTP call
    record = {"to": customer_email, "order_id": order_id, "amount_cents": amount_cents}
    _SENT_EMAILS.append(record)
    return record


@capability
def log_support_action(summary: str) -> None:
    """Record a one-line audit entry for a support action taken.

    >>> log_support_action("Refunded ord_101")
    """
    _ACTION_LOG.append(summary)
