"""REPO_ROOT: the repository these capabilities operate on.

Resolved once from this file's location (smile/repo_tools/repo_root.py
-> repo root is two parents up) rather than os.getcwd(), so behavior
doesn't depend on where smile-mcp happens to be launched from. Every
path-accepting capability resolves against this and refuses to leave
it -- see resolve_repo_path.py. The functions execute inside the
sandbox child (pickled into the capability namespace) with the host
process's filesystem permissions.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
