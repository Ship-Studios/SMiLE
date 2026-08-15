"""grep capability."""

from __future__ import annotations

import re

from smile.repo_tools.registry import registry
from smile.repo_tools.repo_root import REPO_ROOT
from smile.repo_tools.walk_repo_glob import walk_repo_glob


@registry.register
def grep(pattern: str, path_glob: str = "**/*") -> list[str]:
    """Search files matching path_glob (relative to the repo root) for a
    regex pattern. Returns matching lines as "path:line_number:text".
    Walks the filesystem directly (not `git grep`), so untracked and
    unstaged files are searched too -- skips .git/__pycache__/.venv/
    node_modules before descending. Binary files that can't be decoded
    as UTF-8 are skipped rather than raising. Raises PathEscapesRepoError
    if `path_glob` is absolute, contains `..`, or its first concrete
    component resolves outside the repository.

    >>> grep("def execute_script", "smile/**/*.py")
    """
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"{pattern!r} is not a valid regex: {exc}") from None
    matches: list[str] = []

    for rel in walk_repo_glob(path_glob):
        path = REPO_ROOT / rel
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                matches.append(f"{rel}:{line_number}:{line}")

    return matches
