"""IGNORED_DIR_NAMES: directory names skipped by every filesystem-walking
capability (list_files, grep) -- VCS internals, caches, and dependency
trees that are never useful to search or list. No functions/methods here
-- exempt from the one-def-per-file rule."""

from __future__ import annotations

IGNORED_DIR_NAMES = {".git", "__pycache__", ".venv", "node_modules"}
