"""ResultStore: holds full script results server-side so an oversized
result can be offered to the agent as a fetchable resource instead of
being forced into its context window.

Field declarations only -- its methods live in their own files and are
attached below, per the project's one-def-per-file rule.

Bounded on purpose. This is a cache, not a database: entries are evicted
oldest-first past MAX_STORED_RESULTS so a long-running server can't grow
without limit. A caller that needs a result to outlive that window should
persist it through a capability of its own rather than relying on this.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from smile.server.constants import MAX_STORED_RESULTS
from smile.server.result_store_get import result_store_get
from smile.server.result_store_put import result_store_put


@dataclass
class ResultStore:
    """An in-memory, bounded, insertion-ordered store of full script
    results, keyed by an opaque result id."""

    max_results: int = MAX_STORED_RESULTS
    """How many results to retain before evicting the oldest. A field
    rather than a module constant so the server can size it from
    SMILE_MAX_STORED_RESULTS and tests can use a small store without
    monkeypatching."""

    _results: "OrderedDict[str, Any]" = field(default_factory=OrderedDict)


ResultStore.put = result_store_put
ResultStore.get = result_store_get
