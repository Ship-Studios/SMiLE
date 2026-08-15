"""run_tests capability."""

from __future__ import annotations

import sys

from smile.repo_tools.enforce_run_tests_interval import enforce_run_tests_interval
from smile.repo_tools.registry import registry
from smile.repo_tools.run_subprocess import run_subprocess
from smile.repo_tools.run_tests_stamp_path import run_tests_stamp_path
from smile.sandbox.truncate_stream import truncate_stream

_TEST_TIMEOUT_S = 120
_OUTPUT_BUDGET = 4000
_MIN_INTERVAL_S = 30.0


@registry.register
def run_tests() -> dict:
    """Run the project's capability-registration test suite
    (tests/test_capabilities.py) and return a structured pass/fail
    result. Output is capped to keep a noisy failure from flooding the
    caller's context -- see stdout/stderr for an excerpt if truncated.
    Raises RuntimeError if called again within 30 seconds of the
    previous call (the floor is file-backed so it survives across
    execute_script processes). Timeout is min(120s, SMILE_TIMEOUT_S);
    the default SMILE_TIMEOUT_S of 30s is what this is meant to run
    under.

    >>> run_tests()
    """
    enforce_run_tests_interval(_MIN_INTERVAL_S, run_tests_stamp_path())

    result = run_subprocess(
        [sys.executable, "tests/test_capabilities.py"],
        timeout_s=_TEST_TIMEOUT_S,
    )
    return {
        "passed": result["returncode"] == 0 and not result["timed_out"],
        "timed_out": result["timed_out"],
        "stdout": truncate_stream(result["stdout"], _OUTPUT_BUDGET, "stdout"),
        "stderr": truncate_stream(result["stderr"], _OUTPUT_BUDGET, "stderr"),
    }
