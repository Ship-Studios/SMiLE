"""is_ignored_repo_path: ignored-directory check that only looks at
segments *inside* the repo, so a checkout living under a directory
named node_modules / .venv / .git is not treated as entirely empty."""

from __future__ import annotations

from pathlib import Path

from smile.repo_tools.ignored_dir_names import IGNORED_DIR_NAMES


def is_ignored_repo_path(path: Path, root: Path) -> bool:
    """True if `path` is under `root` and any in-repo segment is in
    IGNORED_DIR_NAMES. Paths that are not under `root` are treated as
    ignored (the walker should never yield them)."""
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES for part in rel_parts)
