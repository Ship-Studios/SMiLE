"""load_settings: resolves the server's runtime output budgets from
environment configuration, so a consumer can tune them in .mcp.json
without forking SMiLE."""

from __future__ import annotations

import os
from pathlib import Path

from smile.capabilities.errors import CapabilityDefinitionError
from smile.sandbox.constants import (
    DEFAULT_RESULT_BUDGET,
    DEFAULT_STREAM_BUDGET,
    DEFAULT_TIMEOUT_S,
)
from smile.server.constants import (
    DEFAULT_INTENT_LOG_PATH,
    MAX_SAVED_SCRIPTS,
    MAX_STORED_RESULTS,
)
from smile.server.env_int import env_int
from smile.server.server_settings import ServerSettings

ENV_RESULT_BUDGET = "SMILE_RESULT_BUDGET"
ENV_STREAM_BUDGET = "SMILE_STREAM_BUDGET"
ENV_TIMEOUT_S = "SMILE_TIMEOUT_S"
ENV_MAX_STORED_RESULTS = "SMILE_MAX_STORED_RESULTS"
ENV_INTENT_LOG_PATH = "SMILE_INTENT_LOG"
ENV_MAX_SAVED_SCRIPTS = "SMILE_MAX_SAVED_SCRIPTS"
ENV_SCRIPTS_DIR = "SMILE_SCRIPTS_DIR"


def load_settings() -> ServerSettings:
    """Build the server's ServerSettings from environment config:

      SMILE_RESULT_BUDGET=12000
          Max characters of `return_value` returned inline before the
          result is truncated to a summary (the full value stays
          fetchable via its resource link). 0 disables truncation.

      SMILE_STREAM_BUDGET=4000
          Max characters of stdout and of stderr returned before each is
          excerpted head+tail. 0 disables truncation.

      SMILE_TIMEOUT_S=30
          Seconds a script may run before it is terminated.

      SMILE_MAX_STORED_RESULTS=32
          How many full results are kept server-side for resource fetches
          before the oldest are evicted. Each entry can be several
          megabytes, so this is a memory ceiling.

      SMILE_INTENT_LOG=/var/log/smile/intent.log
          File each execute_script call's stated intent and the
          capabilities its code actually called are appended to, one
          JSON line per call. Defaults to smile_intent.log in the
          working directory.

      SMILE_MAX_SAVED_SCRIPTS=32
          How many agent-saved functions (`__save__`) the session
          library may hold. A new name is refused at this ceiling;
          overwriting an existing name always succeeds.

      SMILE_SCRIPTS_DIR=.smile/scripts
          Directory of `{name}.json` files to persist saved scripts
          across process restarts. Unset (the default) keeps the
          library in memory only. Created if missing.

    Budgets are in characters, not tokens -- see smile/sandbox/constants.py
    for why, and for how the defaults were derived against a 100k-token
    context window. Consumers with a larger window (or a non-LLM caller)
    can raise them; consumers on a smaller one should lower them.

    Every value is validated here, at startup, rather than at first use:
    a malformed budget in .mcp.json should stop the server with a clear
    message, not surface later as mysteriously truncated results.
    """
    timeout_raw = os.environ.get(ENV_TIMEOUT_S)

    if timeout_raw is None or not timeout_raw.strip():
        timeout_s = DEFAULT_TIMEOUT_S
    else:
        try:
            timeout_s = float(timeout_raw.strip())
        except ValueError as exc:
            raise CapabilityDefinitionError(
                f"{ENV_TIMEOUT_S}={timeout_raw!r} is not a valid number of "
                f"seconds (e.g. '10' or '2.5')."
            ) from exc
        if timeout_s <= 0:
            raise CapabilityDefinitionError(
                f"{ENV_TIMEOUT_S}={timeout_raw!r} must be greater than zero -- "
                f"a script needs some time budget to run at all."
            )

    max_stored = env_int(ENV_MAX_STORED_RESULTS, MAX_STORED_RESULTS)
    if max_stored < 1:
        raise CapabilityDefinitionError(
            f"{ENV_MAX_STORED_RESULTS}={max_stored} must be at least 1 -- a "
            f"store of zero would hand out resource links that never resolve."
        )

    intent_log_raw = os.environ.get(ENV_INTENT_LOG_PATH)
    intent_log_path = (
        intent_log_raw.strip()
        if intent_log_raw is not None and intent_log_raw.strip()
        else DEFAULT_INTENT_LOG_PATH
    )
    intent_log_parent = Path(intent_log_path).parent
    if not intent_log_parent.is_dir():
        raise CapabilityDefinitionError(
            f"{ENV_INTENT_LOG_PATH}={intent_log_path!r} can't be opened for "
            f"logging -- its parent directory {str(intent_log_parent)!r} "
            f"doesn't exist. Create the directory first, or point "
            f"{ENV_INTENT_LOG_PATH} at a path whose parent already exists."
        )
    if Path(intent_log_path).is_dir():
        raise CapabilityDefinitionError(
            f"{ENV_INTENT_LOG_PATH}={intent_log_path!r} is a directory, not "
            f"a file -- point {ENV_INTENT_LOG_PATH} at the log file itself."
        )
    try:
        with open(intent_log_path, "a"):
            pass
    except OSError as exc:
        raise CapabilityDefinitionError(
            f"{ENV_INTENT_LOG_PATH}={intent_log_path!r} can't be opened for "
            f"logging: {exc}."
        ) from exc

    max_saved = env_int(ENV_MAX_SAVED_SCRIPTS, MAX_SAVED_SCRIPTS)
    if max_saved < 1:
        raise CapabilityDefinitionError(
            f"{ENV_MAX_SAVED_SCRIPTS}={max_saved} must be at least 1 -- a "
            f"library of zero could never accept a __save__."
        )

    scripts_raw = os.environ.get(ENV_SCRIPTS_DIR)
    if scripts_raw is None or not scripts_raw.strip():
        scripts_dir: str | None = None
    else:
        scripts_dir = scripts_raw.strip()
        scripts_path = Path(scripts_dir)
        if scripts_path.is_file():
            raise CapabilityDefinitionError(
                f"{ENV_SCRIPTS_DIR}={scripts_dir!r} is a file, not a "
                f"directory -- point {ENV_SCRIPTS_DIR} at a directory "
                f"to hold {{name}}.json saved scripts."
            )
        try:
            scripts_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise CapabilityDefinitionError(
                f"{ENV_SCRIPTS_DIR}={scripts_dir!r} can't be created: {exc}."
            ) from exc

    return ServerSettings(
        result_budget=env_int(ENV_RESULT_BUDGET, DEFAULT_RESULT_BUDGET),
        stream_budget=env_int(ENV_STREAM_BUDGET, DEFAULT_STREAM_BUDGET),
        timeout_s=timeout_s,
        max_stored_results=max_stored,
        intent_log_path=intent_log_path,
        max_saved_scripts=max_saved,
        scripts_dir=scripts_dir,
    )
