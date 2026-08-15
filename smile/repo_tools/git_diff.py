"""git_diff capability."""

from __future__ import annotations

from smile.repo_tools.registry import registry
from smile.repo_tools.require_subprocess_success import require_subprocess_success
from smile.repo_tools.run_subprocess import run_subprocess


@registry.register
def git_diff(staged: bool = False) -> str:
    """Return the working-tree diff, or the staged diff if staged=True.
    Raises RuntimeError if `git diff` times out, exits non-zero, or
    cannot be started, so a failure can never be mistaken for "no
    changes".

    >>> git_diff()
    """
    argv = ["git", "diff"]
    if staged:
        argv.append("--staged")
    result = run_subprocess(argv)
    require_subprocess_success(result, "git diff")
    return result["stdout"]
