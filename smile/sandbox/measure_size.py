"""measure_size: how large a script result will be once it reaches the
agent's context window."""

from __future__ import annotations

import json
from typing import Any


def measure_size(value: Any) -> int:
    """Return the size of `value` in characters, as the agent will see it.

    Measured against the JSON serialization rather than `len(repr(value))`
    or a raw byte count, because JSON is what actually crosses the MCP
    boundary into context -- and it is routinely much larger than the
    in-memory object suggests (dict keys are repeated per row, floats
    expand, non-ASCII escapes to \\uXXXX).

    Falls back to `repr` for values JSON can't represent. Anything that
    reaches this point has already survived the picklability check in
    build_payload, so the fallback is about JSON's narrower type support
    (sets, datetimes, custom classes), not about broken values.
    """
    try:
        return len(json.dumps(value, default=repr))
    except (TypeError, ValueError):
        return len(repr(value))
