# Capability

::: smile.capabilities.Capability
    options:
      show_bases: false
      members: false

A single callable exposed to sandboxed scripts. Every registration path
(`register`, `register_module`, `register_class`, `register_spec`,
`collect`) converges on this same dataclass — the sandbox and the
stub-rendering code don't need to know which path a capability came from.

## `name`

::: smile.capabilities.capability_name.capability_name
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `stub_signature`

::: smile.capabilities.capability_stub_signature.capability_stub_signature
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
