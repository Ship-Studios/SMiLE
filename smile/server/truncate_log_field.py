"""truncate_log_field: shrink an oversized intent-log field (code, intent,
error) to a character budget, keeping both ends.

Distinct from smile/sandbox/truncate_stream.py: that helper's marker text
is stdout/stderr-specific ("Print less, or aggregate before printing"),
which is nonsensical spliced into a logged code/intent/error string. This
keeps the same head+tail shape (the interesting part of a stack trace or
a script's tail is usually at the end) but with marker wording that reads
correctly for an arbitrary named field in a log record.
"""

from __future__ import annotations

from smile.sandbox.constants import STREAM_TAIL_FRACTION


def truncate_log_field(text: str, budget: int, field_name: str) -> str:
    """Return `text` unchanged if it fits in `budget`, else a head+tail
    excerpt with an explicit marker naming how much was dropped.
    """
    if len(text) <= budget:
        return text

    omitted = len(text) - budget
    tail_chars = int(budget * STREAM_TAIL_FRACTION)
    head_chars = budget - tail_chars

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars else ""

    marker = (
        f"\n\n... [SMiLE truncated {omitted:,} characters of {field_name} "
        f"({len(text):,} total) for the intent log. This is an excerpt, "
        f"not the complete {field_name}.] ...\n\n"
    )
    return f"{head}{marker}{tail}"
