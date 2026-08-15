"""
repo_tools: capabilities for working inside the SMiLE repository itself
-- introspection (list/read/grep files), git history/diff, GitHub
PRs/issues (via `gh`), and running the test suite. This is the default
registry smile-mcp serves when no SMILE_CAPABILITIES/SMILE_CAPABILITY_SPEC
is configured (see load_registry.py).

Every path-accepting capability is confined to the repository root
(resolve_repo_path.py / validate_repo_glob.py). The functions execute
inside the sandbox child with the host process's filesystem
permissions. Every git/gh/test capability shells out via
run_subprocess.py with a fixed argv list, a process-group kill on
timeout, and a timeout capped at SMILE_TIMEOUT_S.

This package follows the project's one-function/method-per-file rule
(see CLAUDE.md): each capability lives in its own module. Importing them
here (for their `@registry.register` side effects) and re-exporting
`registry` keeps `from smile.repo_tools import registry` working the
same way it does for every other capability package.
"""

from __future__ import annotations

from smile.repo_tools.registry import registry

# Import each capability module for its registration side effect.
from smile.repo_tools import get_pr as _get_pr  # noqa: F401
from smile.repo_tools import git_diff as _git_diff  # noqa: F401
from smile.repo_tools import git_log as _git_log  # noqa: F401
from smile.repo_tools import git_show as _git_show  # noqa: F401
from smile.repo_tools import git_status as _git_status  # noqa: F401
from smile.repo_tools import grep as _grep  # noqa: F401
from smile.repo_tools import list_files as _list_files  # noqa: F401
from smile.repo_tools import list_issues as _list_issues  # noqa: F401
from smile.repo_tools import list_prs as _list_prs  # noqa: F401
from smile.repo_tools import read_file as _read_file  # noqa: F401
from smile.repo_tools import run_tests as _run_tests  # noqa: F401

__all__ = ["registry"]
