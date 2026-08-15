"""log_intent: appends one JSON line per execute_script call recording the
agent's stated intent alongside what the code actually called.

This is the audit trail half of intent tracking: `intent` in
execute_script's signature only captures what the agent *claims* it's
doing; extract_called_capabilities() independently determines what the
code *calls*. Neither is trusted alone -- logging both side by side is
what lets someone grep the log afterward for a script whose intent says
"look up a customer" but whose capability list includes
"delete_customer".

Appends rather than holding records in memory, since (unlike ResultStore)
there's no bounded eviction story here and this is meant to be a durable
audit log, not a debugging aid that only needs to survive one session.

Logging failures (a bad path, a full disk, a permissions error) never
raise: the audit log is a secondary concern, and a script's real result
-- already computed by the time this runs -- must never be discarded
because the log couldn't be written. They're still reported, though --
via the standard `logging` module rather than a bare `except: pass` --
so a directory that goes missing or unwritable after startup produces a
visible operator-facing signal instead of the audit trail silently
going dark.
"""

from __future__ import annotations

import json
import logging
import time
import typing

from smile.server.constants import (
    INTENT_LOG_CODE_BUDGET,
    INTENT_LOG_ERROR_BUDGET,
    INTENT_LOG_INTENT_BUDGET,
)
from smile.server.truncate_log_field import truncate_log_field

if typing.TYPE_CHECKING:
    from smile.sandbox import ScriptResult

logger = logging.getLogger(__name__)


def log_intent(
    path: str,
    intent: str,
    code: str,
    called_capabilities: list[str],
    result: "ScriptResult",
) -> None:
    logged_code = truncate_log_field(code, INTENT_LOG_CODE_BUDGET, "code")
    logged_intent = truncate_log_field(intent, INTENT_LOG_INTENT_BUDGET, "intent")
    logged_error = (
        truncate_log_field(result.error, INTENT_LOG_ERROR_BUDGET, "error")
        if result.error is not None
        else None
    )

    record = {
        "timestamp": time.time(),
        "intent": logged_intent,
        "code": logged_code,
        "called_capabilities": called_capabilities,
        "error": logged_error,
        "timed_out": result.timed_out,
    }
    try:
        line = json.dumps(record) + "\n"
        with open(path, "a") as f:
            f.write(line)
    except (OSError, TypeError, ValueError):
        logger.error("Failed to write intent log entry to %r", path, exc_info=True)
