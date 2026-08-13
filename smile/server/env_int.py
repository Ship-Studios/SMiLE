"""env_int: reads a non-negative integer setting from the environment,
failing loudly on anything malformed."""

from __future__ import annotations

import os

from smile.capabilities.errors import CapabilityDefinitionError


def env_int(name: str, default: int) -> int:
    """Return the integer value of environment variable `name`, or
    `default` if it is unset or empty.

    Raises CapabilityDefinitionError on a value that isn't a non-negative
    integer. Silently falling back to the default would be worse than
    failing: a consumer who writes SMILE_RESULT_BUDGET=100k in .mcp.json
    would get SMiLE's default budget instead, and the only symptom would
    be results truncated at a size they never chose -- with nothing
    anywhere saying their setting was ignored.

    Underscores are accepted as digit separators (SMILE_RESULT_BUDGET=
    12_000), since these values are read by humans in a JSON config and
    Python's own int() allows them.
    """
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default

    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise CapabilityDefinitionError(
            f"{name}={raw!r} is not a valid integer. Expected a whole number "
            f"of characters (e.g. '12000'), or 0 to disable the limit."
        ) from exc

    if value < 0:
        raise CapabilityDefinitionError(
            f"{name}={raw!r} must not be negative. Use a positive character "
            f"budget, or 0 to disable the limit entirely."
        )

    return value
