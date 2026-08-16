"""catalog_entry: the one dict shape every list_capabilities() entry
takes, regardless of whether it describes an operator capability or a
saved script. Centralizing the shape means a field added/renamed here
cannot silently diverge between the two catalog builders
(registry_list_capabilities.py and
smile/server/catalog_with_saved_scripts.py).
"""

from __future__ import annotations

from typing import Any


def catalog_entry(
    *, name: str, signature: str, description: str, example: str | None, source: str
) -> dict[str, Any]:
    """Build one list_capabilities() catalog entry."""
    return {
        "name": name,
        "signature": signature,
        "description": description,
        "example": example,
        "source": source,
    }
