"""Errors raised by example_app capabilities. Available inside the
sandbox since it's part of the traceback a failed capability call
raises."""

from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a lookup fails. Available inside the sandbox."""
