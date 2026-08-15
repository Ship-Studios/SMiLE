"""get_pr capability."""

from __future__ import annotations

import json

from smile.repo_tools.errors import NotFoundError
from smile.repo_tools.registry import registry
from smile.repo_tools.run_subprocess import run_subprocess

# Substrings `gh` emits on stderr specifically when the PR doesn't exist,
# as opposed to other failures (auth, rate limit, no remote configured).
# Matched case-insensitively since `gh` doesn't guarantee wording, only
# that these phrases identify a resolution failure.
_NOT_FOUND_MARKERS = ("could not resolve to a pullrequest", "no pull requests found")


@registry.register
def get_pr(number: int) -> dict:
    """Get details (title, body, state, author, files changed) for one
    pull request by number. Raises ValueError if `number` is not a
    positive integer (negative values would be parsed by `gh` as
    flags), NotFoundError if no such PR exists, or RuntimeError for
    other `gh` failures (e.g. `gh` not installed, no GitHub remote
    configured, not authenticated).

    >>> get_pr(1)
    """
    if number < 1:
        raise ValueError(
            f"PR number must be a positive integer, got {number!r}."
        )
    result = run_subprocess(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,body,state,author,headRefName,files,url",
        ]
    )
    if result["returncode"] != 0:
        stderr = result["stderr"]
        if any(marker in stderr.lower() for marker in _NOT_FOUND_MARKERS):
            raise NotFoundError(f"No PR #{number} found: {stderr}")
        raise RuntimeError(f"gh pr view {number} failed: {stderr}")
    return json.loads(result["stdout"])
