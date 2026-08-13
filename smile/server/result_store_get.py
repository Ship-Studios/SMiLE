"""ResultStore.get implementation. Attached to the ResultStore class in
result_store.py."""

from __future__ import annotations

import typing
from typing import Any

from smile.server.constants import RESULT_MISSING

if typing.TYPE_CHECKING:
    from smile.server.result_store import ResultStore


def result_store_get(self: "ResultStore", result_id: str) -> Any:
    """Return the stored result for `result_id`, or the RESULT_MISSING
    sentinel if it was never stored or has since been evicted.

    A sentinel rather than None, because None is a perfectly valid thing
    for a script to have returned -- conflating the two would report an
    evicted result as a successful null.
    """
    return self._results.get(result_id, RESULT_MISSING)
