"""read_file capability."""

from __future__ import annotations

from smile.repo_tools.registry import registry
from smile.repo_tools.resolve_repo_path import resolve_repo_path


@registry.register
def read_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Read a text file by repo-relative path, optionally restricted to
    a 1-indexed inclusive line range. Raises PathEscapesRepoError if the
    path resolves outside the repository, IsADirectoryError if `path`
    is a directory, and ValueError if `end_line` is less than 1.

    >>> read_file("pyproject.toml")
    """
    resolved = resolve_repo_path(path)
    if not resolved.is_file():
        raise IsADirectoryError(f"{path!r} is not a file.")
    if end_line is not None and end_line < 1:
        raise ValueError(f"end_line must be at least 1 (got {end_line!r}).")
    lines = resolved.read_text().splitlines(keepends=True)

    start_index = max(start_line - 1, 0)
    end_index = end_line if end_line is not None else len(lines)
    return "".join(lines[start_index:end_index])
