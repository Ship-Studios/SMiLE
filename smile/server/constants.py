"""Shared constants for the server package. No functions/methods here --
exempt from the one-def-per-file rule."""

from __future__ import annotations

# How many full script results are retained for resource fetches before
# the oldest are evicted. Each entry can be multi-megabyte, so this is a
# deliberate memory ceiling, not a generous one -- the store exists to
# cover the window between a truncated response and the agent deciding to
# fetch the rest, which is a matter of seconds.
MAX_STORED_RESULTS = 32

# URI scheme/template under which full results are exposed. Must stay in
# sync with the @mcp.resource template in full_result_resource.py.
RESULT_URI_TEMPLATE = "smile://results/{result_id}"

# Sentinel for "no such result" -- distinct from None, which is a value a
# script may legitimately have returned.
RESULT_MISSING = object()
