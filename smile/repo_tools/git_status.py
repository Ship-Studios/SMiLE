"""git_status capability."""

from __future__ import annotations

from smile.repo_tools.registry import registry
from smile.repo_tools.require_subprocess_success import require_subprocess_success
from smile.repo_tools.run_subprocess import run_subprocess


@registry.register
def git_status() -> str:
    """Return `git status --short --branch` output for the repository.
    Raises RuntimeError if `git status` times out, exits non-zero, or
    cannot be started, so a failure can never be mistaken for a clean
    working tree.

    >>> git_status()
    """
    result = run_subprocess(["git", "status", "--short", "--branch"])
    require_subprocess_success(result, "git status")
    return result["stdout"]
