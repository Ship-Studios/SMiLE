"""build_tool_response: turns a ScriptResult into the dict execute_script
returns, storing an oversized result and linking to it.

Kept separate from the tool function itself so the store-and-link policy
can be tested without going through MCP, and so execute_script stays a
thin adapter.
"""

from __future__ import annotations

import typing
from typing import Any

from smile.server.constants import RESULT_URI_TEMPLATE
from smile.server.result_store_instance import result_store

if typing.TYPE_CHECKING:
    from smile.sandbox import ScriptResult


def build_tool_response(result: "ScriptResult") -> dict[str, Any]:
    """Build execute_script's response, attaching a resource link when the
    return value was truncated.

    The full result is only stored when there is something the agent
    can't already see. Storing every result would pin large objects in
    memory for results that were returned in full anyway.
    """
    response: dict[str, Any] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_value": result.return_value,
        "error": result.error,
        "timed_out": result.timed_out,
    }

    if result.stdout_truncated:
        response["stdout_truncated"] = True
    if result.stderr_truncated:
        response["stderr_truncated"] = True

    if result.truncation is not None:
        result_id = result_store.put(result.full_return_value)
        uri = RESULT_URI_TEMPLATE.format(result_id=result_id)
        response["full_result_uri"] = uri
        # Restate the fetch path inside the truncation note itself. The
        # note is what an agent actually reads when it sees a truncated
        # result, and a URI sitting in a sibling key is easy to miss.
        response["return_value"] = {
            **result.return_value,
            "full_result_uri": uri,
            "how_to_read_full_result": (
                f"Read the MCP resource {uri} to get the complete value. "
                f"Prefer re-running an aggregating script instead -- the full "
                f"result is large, which is why it was not returned inline."
            ),
        }

    return response
