"""validate_repo_glob: reject globs that would walk outside REPO_ROOT
before the walker starts. Absolute paths and `..` are rejected, and a
concrete first component that is a symlink (or path) resolving outside
the repo raises rather than letting the walk touch the target tree."""

from __future__ import annotations

from pathlib import Path

from smile.repo_tools.errors import PathEscapesRepoError
from smile.repo_tools.repo_root import REPO_ROOT
from smile.repo_tools.resolve_repo_path import resolve_repo_path

_GLOB_METACHARS = "*?["


def validate_repo_glob(pattern: str) -> None:
    """Raise PathEscapesRepoError if `pattern` is absolute, contains
    `..`, or its first concrete path component resolves outside the
    repository."""
    candidate = Path(pattern)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise PathEscapesRepoError(
            f"{pattern!r} is not a repo-relative glob (absolute paths and "
            f"'..' segments are not allowed)."
        )
    if not candidate.parts:
        return
    first = candidate.parts[0]
    if any(char in first for char in _GLOB_METACHARS):
        return
    prefix = REPO_ROOT / first
    if prefix.exists() or prefix.is_symlink():
        resolve_repo_path(first)
