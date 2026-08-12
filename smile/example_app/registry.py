"""The shared CapabilityRegistry instance that every example_app
capability registers against. Not a function/method -- just the shared
object, analogous to `data.py`."""

from __future__ import annotations

from smile.capabilities import CapabilityRegistry

registry = CapabilityRegistry()
