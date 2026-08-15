"""git_show capability."""

from __future__ import annotations

from smile.repo_tools.errors import NotFoundError
from smile.repo_tools.registry import registry
from smile.repo_tools.run_subprocess import run_subprocess

# Substrings `git` emits on stderr specifically when `ref` doesn't
# resolve to anything, as opposed to other failures.
_NOT_FOUND_MARKERS = ("bad revision", "unknown revision", "ambiguous argument")


@registry.register
def git_show(ref: str) -> str:
    """Return the commit message and diff for a single commit ref
    (hash, branch name, or "HEAD"-style relative ref). Raises
    ValueError if `ref` looks like a git option, NotFoundError if it
    doesn't resolve to a commit, or RuntimeError for other `git show`
    failures.

    >>> git_show("HEAD")
    """
    if ref.startswith("-"):
        raise ValueError(
            f"ref {ref!r} looks like a git option; pass a commit hash, "
            f"branch name, or HEAD-style relative ref."
        )
    # `git show` has no real options-terminator for the revision argument
    # (`--` there separates pathspecs, not options -- see CLAUDE.md); the
    # startswith("-") check above is the actual, only defense against
    # `ref` being parsed as a git switch.
    result = run_subprocess(["git", "show", ref])
    if result["returncode"] != 0:
        stderr = result["stderr"]
        if any(marker in stderr.lower() for marker in _NOT_FOUND_MARKERS):
            raise NotFoundError(f"No commit found for ref {ref!r}: {stderr}")
        raise RuntimeError(f"git show {ref!r} failed: {stderr}")
    return result["stdout"]
