"""walk_repo_glob: repo-confined glob that prunes ignored directories
before descending and never walks a symlink tree that resolves outside
REPO_ROOT. Replaces Path.glob, which follows an explicitly named
symlink prefix (and walks `.git` / `.venv` before any post-filter)."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from smile.repo_tools.collect_unignored_files import collect_unignored_files
from smile.repo_tools.errors import PathEscapesRepoError
from smile.repo_tools.is_ignored_repo_path import is_ignored_repo_path
from smile.repo_tools.repo_root import REPO_ROOT
from smile.repo_tools.resolve_repo_path import resolve_repo_path
from smile.repo_tools.validate_repo_glob import validate_repo_glob


def walk_repo_glob(pattern: str) -> list[str]:
    """Return sorted repo-relative posix paths of files matching
    `pattern`. Raises PathEscapesRepoError if the pattern is absolute,
    contains `..`, or its first concrete component resolves outside
    the repository."""
    validate_repo_glob(pattern)
    parts = Path(pattern).parts
    if not parts:
        return []

    matches: set[str] = set()
    stack: list[tuple[Path, int, frozenset[Path]]] = [
        (REPO_ROOT, 0, frozenset({REPO_ROOT.resolve()}))
    ]
    while stack:
        directory, index, seen = stack.pop()
        part = parts[index]
        is_last = index == len(parts) - 1

        if part == "**":
            if is_last:
                for path in collect_unignored_files(directory):
                    matches.add(path.relative_to(REPO_ROOT).as_posix())
            else:
                stack.append((directory, index + 1, seen))
                try:
                    entries = list(os.scandir(directory))
                except OSError:
                    continue
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    child = Path(entry.path)
                    if is_ignored_repo_path(child, REPO_ROOT):
                        continue
                    child_real = child.resolve()
                    if child_real in seen:
                        continue
                    stack.append((child, index, seen | {child_real}))
            continue

        try:
            entries = list(os.scandir(directory))
        except OSError:
            continue
        for entry in entries:
            if not fnmatch.fnmatch(entry.name, part):
                continue
            child = Path(entry.path)
            if is_ignored_repo_path(child, REPO_ROOT):
                continue
            try:
                rel = child.relative_to(REPO_ROOT)
            except ValueError:
                continue
            if entry.is_symlink():
                try:
                    resolve_repo_path(rel.as_posix())
                except PathEscapesRepoError:
                    continue
            if is_last:
                if entry.is_file(follow_symlinks=True):
                    matches.add(rel.as_posix())
                continue
            if not entry.is_dir(follow_symlinks=True):
                continue
            child_real = child.resolve()
            if child_real in seen:
                continue
            stack.append((child, index + 1, seen | {child_real}))

    return sorted(matches)
