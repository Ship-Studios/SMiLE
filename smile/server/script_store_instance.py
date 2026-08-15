"""The shared ScriptStore instance that execute_script writes to and
list_capabilities reads from. Not a function/method -- just the shared
object, analogous to result_store_instance.py.
"""

from __future__ import annotations

from smile.server.load_script_store import load_script_store
from smile.server.settings_instance import settings

script_store = load_script_store(settings)
