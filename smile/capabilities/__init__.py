"""
Capability registry: the user-defined abstraction layer.

A "capability" is a plain Python function that the sandboxed script is
allowed to call. This package holds the registry and the logic that turns
registered functions into:

  1. A namespace dict injected into the sandbox (name -> callable)
  2. Human/agent-readable type-stub signatures for `list_capabilities`

There are four ways to get a function into the registry, in increasing
order of leverage:

  1. `@registry.register` -- decorate one function. Description and
     example are inferred from the docstring/signature if not given
     explicitly.
  2. `registry.register_module(some_module)` -- auto-register every
     public function in an existing module.
  3. `registry.register_class(SomeClient(...))` -- auto-register every
     public method on an existing client/SDK instance, bound to that
     instance.
  4. `registry.register_spec(spec)` / `load_specs(path)` -- declarative
     JSON/YAML capability definitions that proxy to a Python target or an
     HTTP endpoint, for cases where hand-writing a Python wrapper isn't
     worth it.

A fifth, registry-free path exists for capabilities defined across many
files/modules with no registry in scope: mark a function with `@capability`
(no registration happens yet), then gather every marked function across one
or more modules in one call with `registry.collect(*modules)`.

`@registry.register` on an already-`@capability`-marked function also
works directly -- marker metadata (description/example) is used as a
fallback, below explicit kwargs and above docstring inference.

Every path above converges on the same `Capability` object and the same
registration-time validation, so the sandbox and the stub/documentation
generation don't need to know which path a capability came from.

This package follows the project's one-function/method-per-file rule
(see CLAUDE.md): every function and method -- including private helpers
and dataclass methods -- lives in its own module, wired back onto its
class via `Class.method = imported_function` after the class body
(field declarations only). This file reassembles the pre-restructure
public surface (`from smile.capabilities import CapabilityRegistry,
CapabilityDefinitionError, CapabilitySpec` keeps working exactly as
before).
"""

from __future__ import annotations

from smile.capabilities.capability import Capability
from smile.capabilities.capability_marker import capability_marker as capability
from smile.capabilities.capability_registry import CapabilityRegistry
from smile.capabilities.capability_spec import CapabilitySpec
from smile.capabilities.errors import CapabilityDefinitionError

__all__ = [
    "Capability",
    "CapabilityRegistry",
    "CapabilitySpec",
    "CapabilityDefinitionError",
    "capability",
]
