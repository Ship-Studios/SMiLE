"""Assembles the CapabilityRegistry for the order-support example app,
using every SMiLE registration path against real (if simplified) app
code -- nothing here was written with SMiLE in mind except
notifications.send_refund_email and log_support_action's @capability
marker.
"""

from __future__ import annotations

from smile.capabilities import CapabilityRegistry

from examples.order_support import notifications, orders
from examples.order_support.notifications import send_refund_email
from examples.order_support.payment_client import PaymentClient


def build_registry(payment_api_key: str) -> CapabilityRegistry:
    registry = CapabilityRegistry()

    # 1. register_module: wrap the existing, SMiLE-unaware orders module.
    #    _internal_audit_dump is skipped automatically (leading underscore).
    registry.register_module(orders)

    # 2. register_class: wrap an already-constructed client instance --
    #    already holding its API key -- with zero changes to the client.
    payment_client = PaymentClient(api_key=payment_api_key)
    registry.register_class(payment_client, prefix="payments.")

    # 3. register (decorator): a fresh async capability, registered directly.
    registry.register(send_refund_email)

    # 4. collect: gather every @capability-marked function out of
    #    notifications.py, with no registry reference inside that module.
    registry.collect(notifications)

    return registry
