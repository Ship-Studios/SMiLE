"""The shared ResultStore instance that execute_script writes to and the
full-result resource reads from. Not a function/method -- just the shared
object, analogous to mcp_instance.py and registry_instance.py."""

from __future__ import annotations

from smile.server.result_store import ResultStore
from smile.server.settings_instance import settings

result_store = ResultStore(max_results=settings.max_stored_results)
