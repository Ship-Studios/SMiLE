"""collect_unignored_files: recursive file listing for a trailing `**`
glob segment. Does not follow symlink directories (pathlib `**` does
not either, and following them loops on cycles). Escaping symlink
files are dropped; ignored directory names are pruned before descent."""

from __future__ import annotations

import os
from pathlib import Path

from smile.repo_tools.errors import PathEscapesRepoError
from smile.repo_tools.is_ignored_repo_path import is_ignored_repo_path
from smile.repo_tools.repo_root import REPO_ROOT
from smile.repo_tools.resolve_repo_path import resolve_repo_path


def collect_unignored_files(directory: Path) -> list[Path]:
    found: list[Path] = []
    stack = [directory]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            child = Path(entry.path)
            if is_ignored_repo_path(child, REPO_ROOT):
                continue
            if entry.is_dir(follow_symlinks=False):
                stack.append(child)
                continue
            if not entry.is_file(follow_symlinks=True):
                continue
            if entry.is_symlink():
                try:
                    resolve_repo_path(child.relative_to(REPO_ROOT).as_posix())
                except (PathEscapesRepoError, ValueError):
                    continue
            found.append(child)
    return found
