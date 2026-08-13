"""The MCP resource that serves a full, untruncated script result.

This is the other half of the output-budget design. execute_script caps
what it returns inline so a large result can't overrun the agent's
context; the complete value stays server-side and is exposed here, so the
agent (or the client, or a subagent) can fetch it deliberately if it
actually needs the rows -- rather than being force-fed them, or losing
them entirely to truncation.
"""

from __future__ import annotations

import json

from smile.server.constants import RESULT_MISSING
from smile.server.mcp_instance import mcp
from smile.server.result_store_instance import result_store


@mcp.resource(
    "smile://results/{result_id}",
    name="Full script result",
    description=(
        "The complete, untruncated return value of an execute_script call "
        "whose result was too large to return inline. Fetch this only if a "
        "summary won't do -- it is large by definition, which is why it "
        "wasn't returned in the first place."
    ),
    mime_type="application/json",
)
def full_result(result_id: str) -> str:
    """Return the stored result for `result_id` as JSON."""
    value = result_store.get(result_id)

    if value is RESULT_MISSING:
        # An expired id is normal, not exceptional: the store is a small
        # bounded cache. Say so in a way the agent can act on instead of
        # raising an opaque lookup error.
        return json.dumps(
            {
                "error": "result_not_found",
                "result_id": result_id,
                "detail": (
                    "No stored result with this id. It was never stored, or it "
                    "has been evicted to make room for newer results. Re-run "
                    "the script, aggregating the data inside the script so the "
                    "answer fits in the response."
                ),
            }
        )

    return json.dumps(value, default=repr)
