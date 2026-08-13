"""truncate_stream: shrink oversized stdout/stderr to a character budget,
keeping both ends of the stream."""

from __future__ import annotations

from smile.sandbox.constants import STREAM_TAIL_FRACTION


def truncate_stream(text: str, budget: int, stream_name: str) -> str:
    """Return `text` unchanged if it fits in `budget`, else a head+tail
    excerpt with an explicit marker naming how much was dropped.

    Head *and* tail, rather than a simple prefix: a stray `print` inside a
    loop pushes the interesting output (the last lines before a failure,
    a final summary) past any prefix-only cut, which is exactly the case
    that most often produces an oversized stream in the first place. The
    marker sits inline between the two halves so it cannot be mistaken
    for program output.
    """
    if len(text) <= budget:
        return text

    omitted = len(text) - budget
    tail_chars = int(budget * STREAM_TAIL_FRACTION)
    head_chars = budget - tail_chars

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars else ""

    marker = (
        f"\n\n... [SMiLE truncated {omitted:,} characters of {stream_name} "
        f"({len(text):,} total). This is an excerpt, not the complete "
        f"{stream_name}. Print less, or aggregate before printing.] ...\n\n"
    )
    return f"{head}{marker}{tail}"
