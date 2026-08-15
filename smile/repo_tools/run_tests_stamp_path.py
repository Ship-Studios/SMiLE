"""run_tests_stamp_path: per-repo lock file for the run_tests interval.

Module-level state cannot work: capabilities execute inside a spawn
child that re-imports this package on every execute_script, so an
in-memory timestamp resets each call. The file lives in the system
temp dir (keyed by repo path) so every child shares it.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from smile.repo_tools.repo_root import REPO_ROOT


def run_tests_stamp_path() -> Path:
    digest = hashlib.sha256(str(REPO_ROOT.resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"smile-run-tests-{digest}"
