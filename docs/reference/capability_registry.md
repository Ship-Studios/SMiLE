# CapabilityRegistry

::: smile.capabilities.CapabilityRegistry
    options:
      show_bases: false
      members: false

`CapabilityRegistry` holds the set of capabilities available to sandboxed
scripts. Every method below is attached to the class after its body (see
[Defining capabilities](../capabilities.md) and the project's
one-function-per-file convention) — each is documented from its own module
here, and called the normal way: `registry.register(...)`, not
`registry_register(registry, ...)`. The `self` parameter shown in each
signature below is the `registry` instance the method is called on.

## `register`

::: smile.capabilities.registry_register.registry_register
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `register_module`

::: smile.capabilities.registry_register_module.registry_register_module
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `register_class`

::: smile.capabilities.registry_register_class.registry_register_class
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `register_spec`

::: smile.capabilities.registry_register_spec.registry_register_spec
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `load_specs`

::: smile.capabilities.registry_load_specs.registry_load_specs
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `collect`

::: smile.capabilities.registry_collect.registry_collect
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `namespace`

::: smile.capabilities.registry_namespace.registry_namespace
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `list_capabilities`

::: smile.capabilities.registry_list_capabilities.registry_list_capabilities
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3

## `stub_file`

::: smile.capabilities.registry_stub_file.registry_stub_file
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
