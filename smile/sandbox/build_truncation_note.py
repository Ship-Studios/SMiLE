"""build_truncation_note: assembles the structured note that replaces an
oversized list result."""

from __future__ import annotations

from typing import Any


def build_truncation_note(
    value: list,
    sample: list,
    size: int,
    budget: int,
    shape: str,
) -> dict[str, Any]:
    """Build the note describing a truncated list result.

    Every field here exists to stop the agent drawing a wrong conclusion
    from a partial view: `omitted_items` is counted against the real
    length rather than the sample, and the guidance says outright that the
    sample must not be counted from. An agent that treats 10 of 10,000
    rows as the whole answer produces a confidently wrong result, which is
    worse than an error.
    """
    return {
        "truncated": True,
        "reason": (
            f"Result was {size:,} characters, over the {budget:,}-character "
            f"limit, and was NOT returned in full."
        ),
        "original_shape": shape,
        "returned_items": len(sample),
        "omitted_items": len(value) - len(sample),
        "guidance": (
            "The `sample` below is a partial preview, NOT the full result -- "
            "do not treat it as complete or count from it. Re-run a script "
            "that aggregates server-side (sum/len/filter inside the script, "
            "assigning only the summary to __result__), or read the full "
            "result from the resource link if one was provided."
        ),
        "sample": sample,
    }
