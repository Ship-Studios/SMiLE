"""list_files capability."""

from __future__ import annotations

from smile.repo_tools.registry import registry
from smile.repo_tools.walk_repo_glob import walk_repo_glob


@registry.register
def list_files(pattern: str = "**/*.py") -> list[str]:
    """List repo-relative file paths matching a glob pattern, rooted at
    the repository root. Skips .git, __pycache__, .venv, and
    node_modules directories before descending. Raises
    PathEscapesRepoError if `pattern` is absolute, contains `..`, or
    its first concrete component resolves outside the repository
    (including a symlink to an outside tree).

    >>> list_files("smile/capabilities/*.py")
    """
    return walk_repo_glob(pattern)
