"""head_tail_excerpt: shared head+tail truncation mechanics used by both
truncate_stream.py (stdout/stderr) and smile/server/truncate_log_field.py
(intent-log fields). Head *and* tail, rather than a simple prefix: the
interesting part of an oversized value (the last lines before a failure,
a final summary) is usually near the end, which a prefix-only cut would
discard. The two call sites differ only in marker wording -- a stream's
marker suggests "print less"; a logged field's does not, since the agent
did not choose how much of it to write -- so that text is the one thing
callers supply.
"""

from __future__ import annotations

from smile.sandbox.constants import STREAM_TAIL_FRACTION


def head_tail_excerpt(text: str, budget: int, marker: str) -> str:
    """Return `text` unchanged if it fits in `budget`, else `head +
    marker + tail` sized so the whole excerpt fits the budget."""
    if len(text) <= budget:
        return text

    tail_chars = int(budget * STREAM_TAIL_FRACTION)
    head_chars = budget - tail_chars

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars else ""
    return f"{head}{marker}{tail}"
