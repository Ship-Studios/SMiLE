"""truncate_value: shrink an oversized script result to fit a character
budget, while telling the agent exactly what was removed."""

from __future__ import annotations

from typing import Any

from smile.sandbox.build_truncation_note import build_truncation_note
from smile.sandbox.constants import TRUNCATION_SAMPLE_ROWS
from smile.sandbox.describe_shape import describe_shape
from smile.sandbox.measure_size import measure_size


def truncate_value(value: Any, budget: int) -> tuple[Any, dict[str, Any] | None]:
    """Return `(value, None)` if `value` fits in `budget` characters, else
    `(replacement, note)` where `note` describes what was dropped.

    The note is the whole point of this function. An agent that receives
    20 of 10,000 rows with no indication of the other 9,980 will happily
    conclude there were 20 and report a wrong answer to the user -- a
    silently incorrect result is worse than a loud failure. So every
    truncation carries the original count, the original shape, and an
    explicit instruction about how to get the rest. The replacement value
    is deliberately a dict (not a bare list) so it cannot be mistaken for
    the real result by a script or a human skimming the output.

    Lists are sampled rather than cut mid-structure: the agent gets whole
    leading elements it can inspect for shape, which is what it needs in
    order to write a better script. Other types degrade to a described
    placeholder, since there's no meaningful "first N" of a large dict or
    a giant string beyond a prefix.

    The note has an irreducible floor of a few hundred characters (its
    fixed explanatory prose), so a budget smaller than that is honored as
    far as dropping every sample row and no further. That's deliberate:
    the warning about what was omitted is the part that keeps the agent
    from reporting a wrong answer, so it is the last thing to go. Budgets
    that small aren't a sensible configuration anyway -- a result cap
    below ~1,000 characters can't carry a useful preview.
    """
    size = measure_size(value)
    if size <= budget:
        return value, None

    shape = describe_shape(value)

    if isinstance(value, list):
        # Shrink the sample against the size of the *assembled note*, not
        # of the sample alone: the note's fixed prose (reason, guidance,
        # shape) is several hundred characters, so measuring only the rows
        # lets the finished note overshoot the very budget it reports.
        sample = value[:TRUNCATION_SAMPLE_ROWS]
        note = build_truncation_note(value, sample, size, budget, shape)
        while sample and measure_size(note) > budget:
            sample = sample[: len(sample) // 2]
            note = build_truncation_note(value, sample, size, budget, shape)
        return note, note

    truncated_repr = repr(value)[:budget]
    note = {
        "truncated": True,
        "reason": (
            f"Result was {size:,} characters, over the {budget:,}-character "
            f"limit, and was NOT returned in full."
        ),
        "original_shape": shape,
        "guidance": (
            "The `preview` below is the beginning of the value's repr, NOT the "
            "full result. Re-run a script that reduces the value before "
            "assigning it to __result__, or read the full result from the "
            "resource link if one was provided."
        ),
        "preview": truncated_repr,
    }
    return note, note
