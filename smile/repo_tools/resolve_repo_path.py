"""resolve_repo_path: resolves a user-supplied relative path against
REPO_ROOT and refuses to hand back anything outside it.

Shared by every path-accepting capability (read_file, list_files) so the
containment check lives in exactly one place. Symlinks are resolved
before the containment check (Path.resolve() follows them), so a
symlink inside the repo pointing outside it is still caught.

`path` must be rejected up front if it's absolute: `Path.__truediv__`
discards the left operand entirely when the right one is absolute
(`REPO_ROOT / "/etc/passwd" == Path("/etc/passwd")`), so joining first
and checking containment after would let an absolute path escape the
repo outright rather than merely resolving into it unexpectedly.
"""

from __future__ import annotations

from pathlib import Path

from smile.repo_tools.errors import PathEscapesRepoError
from smile.repo_tools.repo_root import REPO_ROOT


def resolve_repo_path(path: str) -> Path:
    if Path(path).is_absolute():
        raise PathEscapesRepoError(
            f"{path!r} is not a repo-relative path (absolute paths are not "
            f"allowed)."
        )
    candidate = (REPO_ROOT / path).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError:
        raise PathEscapesRepoError(
            f"{path!r} resolves outside the repository root ({REPO_ROOT})."
        ) from None
    return candidate
