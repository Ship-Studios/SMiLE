# run_script

::: smile.sandbox.run_script.run_script

## What's available inside the script

The script executes with only two things as globals: the
`capability_namespace` dict you pass in, and a restricted builtins set. No
`import`, `open`, `exec`, `eval`, `compile`, `input`, or `breakpoint` — and
nothing that touches the filesystem or the host process.

Allowed builtins: `abs`, `all`, `any`, `ascii`, `bin`, `bool`, `bytearray`,
`bytes`, `callable`, `chr`, `complex`, `dict`, `divmod`, `enumerate`,
`filter`, `float`, `format`, `frozenset`, `getattr`, `hasattr`, `hash`,
`hex`, `id`, `int`, `isinstance`, `issubclass`, `iter`, `len`, `list`,
`map`, `max`, `min`, `next`, `oct`, `ord`, `pow`, `print`, `property`,
`range`, `repr`, `reversed`, `round`, `set`, `setattr`, `slice`, `sorted`,
`str`, `sum`, `tuple`, `type`, `zip`, plus `None`/`True`/`False`/
`NotImplemented` and the common built-in exception types (`Exception`,
`ValueError`, `TypeError`, `KeyError`, `IndexError`, `NameError`, and the
other names listed in `SAFE_BUILTIN_NAMES`).

Pass `saved_scripts=` (a sequence of `SavedScriptRecord` values) to bind
those functions as `scripts.<name>(...)` inside the child. `None` (the
default) does not bind `scripts` at all; an empty sequence binds an empty
`scripts` namespace. The MCP server hydrates this from the session
`ScriptStore` on every `execute_script` call.

The script hands back its result by assigning to a special `__result__`
variable — this mirrors how a real MCP tool result is a single structured
value, not stdout text:

```python
result = run_script(
    "__result__ = [c['name'] for c in list_customers() if c['plan'] == 'enterprise']",
    registry.namespace(),
)
result.return_value  # the list, if it's picklable
```

!!! warning "Prototype-grade isolation"
    This uses a subprocess boundary, a restricted `__builtins__` set, and no
    import machinery beyond what's injected. That stops accidental misuse
    and casual escapes — it is **not** adversarially secure against a
    determined attacker with code execution (e.g. via introspection tricks,
    or resource exhaustion beyond the coarse timeout set here). A
    production version should replace this isolation mechanism with
    something like Pyodide/WASM, gVisor/Firecracker microVMs, or a managed
    code-execution service — `run_script`'s signature is written so that
    swap stays contained to `smile.sandbox`.

## Picklability

`run_script` uses `multiprocessing`'s `spawn` context, which pickles the
entire `capability_namespace` dict (and `extra_names`) to hand them across
the process boundary. Every capability callable must therefore be
picklable — see
[Defining capabilities](../capabilities.md#1-decorate-a-function-youre-writing-fresh)
for what that means in practice and how `CapabilityRegistry` catches
violations at registration time, before you ever get here.
