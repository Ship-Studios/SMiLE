"""git_log capability."""

from __future__ import annotations

from smile.repo_tools.registry import registry
from smile.repo_tools.require_subprocess_success import require_subprocess_success
from smile.repo_tools.run_subprocess import run_subprocess


_MAX_COUNT = 500


@registry.register
def git_log(max_count: int = 20) -> list[str]:
    """Return the last `max_count` commits as "hash subject" lines,
    most recent first. `max_count` must be in 1..500 -- git treats
    `--max-count=-1` as unlimited, which would dump the full history
    into the sandbox. Raises ValueError if `max_count` is out of
    range, or RuntimeError if `git log` times out, exits non-zero, or
    cannot be started.

    >>> git_log(max_count=5)
    """
    if max_count < 1 or max_count > _MAX_COUNT:
        raise ValueError(
            f"max_count must be between 1 and {_MAX_COUNT} (got {max_count!r}); "
            f"git treats a non-positive --max-count as unlimited."
        )
    result = run_subprocess(
        ["git", "log", f"--max-count={max_count}", "--pretty=%h %s"]
    )
    require_subprocess_success(result, "git log")
    if not result["stdout"]:
        return []
    return result["stdout"].splitlines()
