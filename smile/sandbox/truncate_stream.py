"""truncate_stream: shrink oversized stdout/stderr to a character budget,
keeping both ends of the stream."""

from __future__ import annotations

from smile.sandbox.head_tail_excerpt import head_tail_excerpt


def truncate_stream(text: str, budget: int, stream_name: str) -> str:
    """Return `text` unchanged if it fits in `budget`, else a head+tail
    excerpt with an explicit marker naming how much was dropped.

    The marker sits inline between the two halves so it cannot be
    mistaken for program output.
    """
    if len(text) <= budget:
        return text

    omitted = len(text) - budget
    marker = (
        f"\n\n... [SMiLE truncated {omitted:,} characters of {stream_name} "
        f"({len(text):,} total). This is an excerpt, not the complete "
        f"{stream_name}. Print less, or aggregate before printing.] ...\n\n"
    )
    return head_tail_excerpt(text, budget, marker)
