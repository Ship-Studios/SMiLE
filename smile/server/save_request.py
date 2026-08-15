"""SaveRequest: a parsed, validated `__save__` request extracted from
agent-authored source. Field declarations only -- exempt from the
one-def-per-file rule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaveRequest:
    """Everything needed to publish one function as `scripts.<name>`."""

    name: str
    func_name: str
    source: str
    description: str
    signature: str
    example: str
