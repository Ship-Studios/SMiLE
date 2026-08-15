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

# How many saved scripts a session may hold. Unlike ResultStore this is a
# reject-when-full ceiling, not an eviction cache: silently dropping a
# function another script still calls is worse than a clear error.
MAX_SAVED_SCRIPTS = 32

# Max characters of extracted function source we will store. Matches the
# spirit of INTENT_LOG_CODE_BUDGET -- this is a session library, not an
# archive of arbitrarily large agent programs.
MAX_SAVED_SCRIPT_CHARS = 8_000

# Assignment name that publishes a script's single top-level function.
SAVE_MAGIC = "__save__"

# Assignment name that removes a previously published function.
# Value must be the exposed name string (not True) -- unlike __save__,
# there is no function in the script to infer the name from.
UNPUBLISH_MAGIC = "__unpublish__"

# catalog `source=` value for agent-saved scripts, distinct from the
# operator-registration sources (decorator, module, class, spec, ...).
SOURCE_SAVED_SCRIPT = "saved_script"

# Sentinel for ScriptStore.get on an unknown name. Distinct from any
# stored record (records are SavedScriptRecord instances).
SCRIPT_MISSING = object()

# Sentinels for save_assignment_value(): no __save__ at module level, vs
# an assignment whose value isn't True / False / a name string.
SAVE_ABSENT = object()
SAVE_INVALID = object()

# Path each execute_script call's intent/capability-usage record is
# appended to, as one JSON line per call. Overridable via SMILE_INTENT_LOG
# (see load_settings.py) so a consumer can point it at their own log
# aggregation instead of a local file.
DEFAULT_INTENT_LOG_PATH = "smile_intent.log"

# Max characters of a script's `code` kept in each intent-log record. The
# log is meant to be grepped for a mismatch between stated intent and
# actual capability calls, not to be a full script archive -- an agent
# can regenerate arbitrarily large code, and an unbounded per-call record
# would let the log grow the same way an unbounded script result would
# (see smile/sandbox/constants.py's output-budget rationale).
INTENT_LOG_CODE_BUDGET = 4_000

# Max characters of `intent` kept in each record. intent is supposed to
# be one sentence; without a cap, a caller can put the same oversized
# payload there and bypass INTENT_LOG_CODE_BUDGET.
INTENT_LOG_INTENT_BUDGET = 500

# Max characters of `result.error` kept in each record. Capability
# failures (git/gh stderr, a raised message) can be as large as a
# script; without a cap they bypass the code/intent budgets.
INTENT_LOG_ERROR_BUDGET = 4_000
