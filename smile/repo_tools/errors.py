"""Errors raised by repo_tools capabilities. Available inside the
sandbox since it's part of the traceback a failed capability call
raises."""

from __future__ import annotations


class PathEscapesRepoError(Exception):
    """Raised when a requested path resolves outside REPO_ROOT."""


class NotFoundError(Exception):
    """Raised when a requested PR, issue, or commit ref doesn't exist --
    distinct from RuntimeError, which covers other gh/git failures (auth,
    rate limits, network) so a caller can catch "not found" specifically
    without also swallowing an operational problem."""
