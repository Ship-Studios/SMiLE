"""send_email capability."""

from __future__ import annotations

from smile.example_app.data import SENT_EMAILS
from smile.example_app.registry import registry


@registry.register
def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email to an address. Returns True on success. In this
    prototype, emails are recorded in-memory, not actually sent.

    >>> send_email("ada@example.com", "Invoice ready", "Your invoice is attached.")
    """
    SENT_EMAILS.append({"to": to, "subject": subject, "body": body})
    return True
