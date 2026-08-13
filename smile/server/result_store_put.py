"""ResultStore.put implementation. Attached to the ResultStore class in
result_store.py."""

from __future__ import annotations

import typing
import uuid
from typing import Any

if typing.TYPE_CHECKING:
    from smile.server.result_store import ResultStore


def result_store_put(self: "ResultStore", value: Any) -> str:
    """Store `value` and return the opaque id it can be fetched by.

    The id is a random uuid4 hex rather than a sequential counter: result
    ids appear in URIs handed to a model, and a guessable id would let one
    conversation's agent read another's results if the server is ever
    shared between sessions.
    """
    result_id = uuid.uuid4().hex
    self._results[result_id] = value

    while len(self._results) > self.max_results:
        self._results.popitem(last=False)  # evict oldest

    return result_id
