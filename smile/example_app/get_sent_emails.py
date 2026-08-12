"""get_sent_emails capability."""

from __future__ import annotations

from smile.example_app.data import SENT_EMAILS
from smile.example_app.registry import registry


@registry.register
def get_sent_emails() -> list[dict]:
    """Return all emails sent so far via send_email(), for
    verification/testing.

    >>> get_sent_emails()
    """
    return list(SENT_EMAILS)
