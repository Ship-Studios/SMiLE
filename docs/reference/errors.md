# CapabilityDefinitionError

::: smile.capabilities.CapabilityDefinitionError
    options:
      show_bases: true
      heading_level: 2

Raised at registration time whenever a capability can't be safely exposed
to the sandbox: missing type hints, no description available (explicit or
inferred), a name collision, or a callable that isn't picklable (a closure,
lambda, or bound method on a locally-defined class). Always raised
immediately at the `register*`/`collect`/`load_specs` call site — the
alternative is the agent silently getting a bad or empty stub at call time,
which is a much worse failure to debug.
