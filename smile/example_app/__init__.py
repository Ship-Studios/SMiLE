"""
Example capability set: a fake in-memory CRM.

Stands in for "the real application" SMiLE would front in production. All
state lives in module-level dicts (data.py), reset on server restart --
this is a prototype, not a database.

Every capability uses the plain `@registry.register` decorator with no
explicit description/example -- both are inferred from the docstring.
This is deliberate: it's the intended common case now, and doubles as a
live example of what capability authors should write.

This package follows the project's one-function/method-per-file rule
(see CLAUDE.md): each capability lives in its own module. Importing them
here (for their `@registry.register` side effects) and re-exporting
`registry` keeps `from smile.example_app import registry` working
exactly as when this was a single example_app.py file.
"""

from __future__ import annotations

from smile.example_app.registry import registry

# Import each capability module for its registration side effect.
# (The imported names aren't used directly here -- registration happens
# at import time via the @registry.register decorator in each module.)
from smile.example_app import get_customer as _get_customer  # noqa: F401
from smile.example_app import get_sent_emails as _get_sent_emails  # noqa: F401
from smile.example_app import list_customers as _list_customers  # noqa: F401
from smile.example_app import list_orders as _list_orders  # noqa: F401
from smile.example_app import send_email as _send_email  # noqa: F401

__all__ = ["registry"]
