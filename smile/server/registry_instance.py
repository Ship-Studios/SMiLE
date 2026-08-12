"""The shared CapabilityRegistry instance that every server tool reads
from. Resolved once at import time via load_registry() -- not a
function/method, just the shared object, analogous to mcp_instance.py."""

from __future__ import annotations

from smile.server.load_registry import load_registry

registry = load_registry()
