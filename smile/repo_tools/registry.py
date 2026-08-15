"""The shared CapabilityRegistry instance every repo_tools capability
registers against. Not a function/method -- just the shared object,
analogous to server/registry_instance.py."""

from __future__ import annotations

from smile.capabilities import CapabilityRegistry

registry = CapabilityRegistry()
