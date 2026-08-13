"""The shared ServerSettings instance every server tool reads from.
Resolved once at import time via load_settings() -- not a function/method,
just the shared object, analogous to registry_instance.py."""

from __future__ import annotations

from smile.server.load_settings import load_settings

settings = load_settings()
