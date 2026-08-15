"""list_prs capability."""

from __future__ import annotations

import json

from smile.repo_tools.registry import registry
from smile.repo_tools.run_subprocess import run_subprocess


@registry.register
def list_prs(state: str = "open") -> list[dict]:
    """List pull requests on the repo's GitHub remote, filtered by
    state ('open', 'closed', 'merged', 'all'). Requires the `gh` CLI to
    be authenticated. Returns [] if `gh` itself is not installed --
    a repo_tools consumer without GitHub access should still be able
    to use every other capability. Raises RuntimeError for other `gh`
    failures (no remote configured, not authenticated) so a genuine
    "zero PRs" result can't be confused with "couldn't check".

    >>> list_prs(state="open")
    """
    result = run_subprocess(
        [
            "gh",
            "pr",
            "list",
            "--state",
            state,
            "--json",
            "number,title,author,headRefName,url",
        ]
    )
    if result["returncode"] is None and not result["timed_out"]:
        return []
    if result["returncode"] != 0:
        raise RuntimeError(f"gh pr list failed: {result['stderr']}")
    return json.loads(result["stdout"])
