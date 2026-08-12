# SMiLE (Secure Message in Lambda Expressions)

A prototype MCP server that lets an LLM agent write a Python **script**
against a curated set of your application's functions, run it in a
sandbox, and get back only the final result -- instead of one MCP
tool-call round trip per action.

```
Agent: "Email all enterprise customers their total paid amount"
  -> writes ONE Python script that loops over customers, sums orders,
     sends emails
  -> SMiLE runs it sandboxed, returns only the final summary
  -> Agent never sees the intermediate order records or email bodies
```

See `smile/server/` for the two MCP tools this exposes
(`list_capabilities`, `execute_script`) and `smile/sandbox/` for the
isolation mechanism (subprocess + restricted builtins -- **prototype-grade,
not adversarially secure**; see the warning at the top of `smile/sandbox/__init__.py`).

This document covers the part that determines whether SMiLE is actually
usable: how you define the functions ("capabilities") an agent's script
is allowed to call.

## Quickstart

```bash
uv sync --extra dev   # dev extra pulls in google-genai + pyyaml, for the e2e test
uv run python3 tests/test_capabilities.py   # unit tests for all registration paths
uv run python3 -m examples.order_support.run   # full end-to-end example app, no API key needed
GEMINI_API_KEY=... uv run python3 tests/e2e_gemini.py   # live agent test
```

See `examples/order_support/` for a standalone app that wires SMiLE onto
plain application code using every registration path together, then runs
a realistic multi-step task through the sandbox in one round trip.

## Defining capabilities

A **capability** is any Python function you register with a
`CapabilityRegistry` (`smile/capabilities/`). Once registered, it's
callable by name inside every sandboxed script, and its signature +
description show up in `list_capabilities()` and in `execute_script`'s
tool description so the agent knows what's available before it writes
code.

There are four ways to register one, depending on how much of your app
already exists.

### 1. Decorate a function you're writing fresh

The common case. Write a normal, type-hinted Python function with a
docstring; `@registry.register` infers everything else.

```python
from smile.capabilities import CapabilityRegistry

registry = CapabilityRegistry()

@registry.register
def get_customer(customer_id: str) -> dict:
    """Look up a customer record by ID.

    >>> get_customer("cust_1")
    """
    return db.customers.find_one(customer_id)
```

What gets inferred, and from where:

| Field | Source |
|---|---|
| `description` | First paragraph of the docstring |
| `example` | A `>>> ` doctest line, or an `Example:` section, in the docstring |
| (fallback) example | Synthesized from the signature if neither is present, e.g. `get_customer(customer_id=...)` |

Explicit overrides still work exactly as before, for cases where the
docstring shouldn't double as agent-facing documentation:

```python
@registry.register(description="...", example="...")
def get_customer(customer_id: str) -> dict: ...
```

**Registration-time validation.** Every parameter (except `*args`/`**kwargs`)
and the return value need a type hint, and a description (explicit or
inferred) is required. Missing either raises `CapabilityDefinitionError`
immediately, at registration time -- not as a confusing bad stub the
agent has to guess around at call time.

### 2. Wrap an existing module

If you already have a module full of well-typed, well-documented
functions -- not written with SMiLE in mind at all -- point the registry
at it:

```python
import myapp.crm as crm
registry.register_module(crm, prefix="crm.")
```

Every public, top-level, well-typed function in `crm` becomes a
capability (`crm.get_customer`, `crm.list_orders`, ...). Functions
missing type hints are **skipped, not fatal** -- bulk-wrapping existing
code routinely hits functions that were never meant to be capabilities.
Check the returned `RegistrationReport`:

```python
report = registry.register_module(crm, prefix="crm.")
print(report.summary())
# Registered 12 capabilities: ['crm.get_customer', 'crm.list_orders', ...]
# Skipped 2:
#   - crm._legacy_migrate: missing type hints on parameter(s) ['data']
#   - crm.internal_debug_dump: missing a return type hint
```

Pass `strict=True` to raise on the first bad function instead, or
`include=[...]`/`exclude=[...]` to filter by name.

### 3. Wrap an existing client/SDK instance

The highest-leverage path: point SMiLE at an **already-constructed**
client object -- already holding its API key, base URL, connection, etc.
-- and every public method becomes a capability, bound to that instance.
No rewriting your integration.

```python
stripe_client = StripeClient(api_key=os.environ["STRIPE_KEY"])
registry.register_class(stripe_client, prefix="stripe.")
```

Same skip-with-reason behavior as `register_module`. Properties, private
methods, and non-callable attributes are never considered (not treated
as validation failures -- they're just not method candidates).

Namespaced capabilities (anything registered with a `prefix=`) are
callable inside the sandbox exactly as the prefix suggests --
`stripe.charge_card(500)` -- and their stub signatures render in that
same call-style form, since `def stripe.charge_card(...): ...` isn't
valid Python syntax.

### 4. Declarative specs (JSON/YAML) -- no Python wrapper at all

For cases where writing a Python function isn't worth it -- a single REST
endpoint, or a function that already exists somewhere importable by
dotted path:

```yaml
# capabilities.yaml
capabilities:
  - name: get_weather
    description: Get current weather for a city.
    target:
      kind: http
      method: GET
      url_template: "https://api.example.com/weather/{city}"
    parameters:
      city: {type: str, required: true}
    returns: dict

  - name: get_product
    description: Look up a product by SKU.
    target:
      kind: python
      path: myapp.catalog.lookup_product
```

```python
registry.load_specs("capabilities.yaml")  # or a .json file
```

Two target kinds:

- **`python`** -- a dotted path to an existing callable. Registered
  exactly like any other capability (same validation).
- **`http`** -- a templated HTTP call. `{placeholders}` in `url_template`
  are filled from named parameters; any parameter not consumed by the
  template goes into the query string (GET/DELETE) or JSON body
  (POST/PUT/PATCH). A real, annotated function signature is synthesized
  from the `parameters` block, so it produces a proper stub
  (`def get_weather(city: str) -> dict: ...`) instead of a bare
  `**kwargs`.

`load_specs()` accepts a single spec object or a list (optionally under
a top-level `capabilities` key), in `.json`, `.yaml`, or `.yml` files.

## Design notes worth knowing if you extend this

- **Everything converges on one `Capability` object.** Whichever of the
  four paths you use, the sandbox and the stub/documentation generator
  don't know or care where a capability came from -- `source` is tracked
  only for error messages and the catalog.
- **HTTP-target capabilities are a picklable class instance, not a
  closure.** `smile/sandbox/` runs scripts in a `multiprocessing.spawn`
  subprocess, which pickles every capability callable to hand it across
  the process boundary. A closure over local variables (the "obvious"
  way to build an HTTP wrapper) isn't picklable --
  `AttributeError: Can't get local object '...'.<locals>._call'` -- so
  `_HttpCapability` (`smile/capabilities/http_capability.py`) is a
  module-level class with plain-data `__init__` state instead. If you
  add a fifth registration path that builds its own wrapper callables,
  keep this in mind: **anything injected into the sandbox namespace must
  be picklable, including anything it closes over.**
- **Namespace prefixes are real attribute access, not string keys.** A
  capability registered as `"stripe.charge_card"` is exposed to the
  sandbox as a `_Namespace` object at global name `stripe` with
  `charge_card` as a bound attribute -- so `stripe.charge_card(...)`
  works as ordinary Python, not as some string-keyed dispatch hack.
- **One function/method per file (see `CLAUDE.md`).** `smile/` is
  restructured so every function and method -- including private
  helpers and dataclass methods -- lives in its own module. Classes
  declare only fields; methods are standalone functions taking `self`
  explicitly, attached via `ClassName.method = imported_function` after
  the class body. Package `__init__.py` files reassemble the
  pre-restructure public surface, so imports like `from
  smile.capabilities import CapabilityRegistry` are unaffected.
