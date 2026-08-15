# Defining capabilities

A **capability** is any Python function you register with a
[`CapabilityRegistry`](reference/capability_registry.md). Once registered,
it's callable by name inside every sandboxed script, and its signature +
description show up in `list_capabilities()` and in `execute_script`'s tool
description so the agent knows what's available before it writes code.

There are five ways to get a function into the registry, in increasing order
of leverage.

## 1. Decorate a function you're writing fresh

The common case. Write a normal, type-hinted, module-level Python function
with a docstring; [`registry.register`](reference/capability_registry.md#register)
infers everything else.

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
inferred) is required. Missing either raises
[`CapabilityDefinitionError`](reference/errors.md) immediately, at
registration time — not as a confusing bad stub the agent has to guess
around at call time.

**Picklability is checked too.** The sandbox runs scripts in a spawned
subprocess, which pickles every registered capability to hand it across the
process boundary. A closure, lambda, or a bound method on a locally-defined
class isn't picklable — registering one raises `CapabilityDefinitionError`
immediately, naming the specific problem, instead of failing later deep
inside the sandbox with a raw pickle traceback:

```python
def make_capability():
    def get_widget(widget_id: str) -> dict:
        """This will fail to register -- it's a closure."""
        return {"id": widget_id}
    return get_widget

registry.register(make_capability())
# CapabilityDefinitionError: Capability 'get_widget' (decorator) can't be
# registered: it is a closure or nested function (qualname
# '...make_capability.<locals>.get_widget'). ... define it as a plain
# module-level function, or (for stateful wrappers) an instance of a
# module-level class with plain-data __init__ state, not a closure.
```

The fix is always the same: define the capability at module level, or (for
stateful wrappers) as an instance of a module-level class — see
[`_HttpCapability`](reference/capability_spec.md) for the pattern this
project itself uses for HTTP-backed capabilities.

**`async def` capabilities work directly.** Register an `async def`
function exactly like a sync one; it's wrapped once at registration time
into a picklable callable that runs it to completion via `asyncio.run()`
inside the sandbox. The agent-authored script never needs to know it's
calling something async — the stub signature and calling convention are
identical to a sync capability:

```python
@registry.register
async def get_customer(customer_id: str) -> dict:
    """Look up a customer record by ID."""
    return await db.customers.find_one(customer_id)
```

## 2. Wrap an existing module

If you already have a module full of well-typed, well-documented functions —
not written with SMiLE in mind at all — point the registry at it with
[`register_module`](reference/capability_registry.md#register_module):

```python
import myapp.crm as crm
registry.register_module(crm, prefix="crm.")
```

Every public, top-level, well-typed function in `crm` becomes a capability
(`crm.get_customer`, `crm.list_orders`, ...). Functions missing type hints
are **skipped, not fatal** — bulk-wrapping existing code routinely hits
functions that were never meant to be capabilities. Check the returned
[`RegistrationReport`](reference/registration_report.md):

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

## 3. Wrap an existing client/SDK instance

The highest-leverage path: point SMiLE at an **already-constructed** client
object — already holding its API key, base URL, connection, etc. — and every
public method becomes a capability, bound to that instance, via
[`register_class`](reference/capability_registry.md#register_class).
No rewriting your integration.

```python
stripe_client = StripeClient(api_key=os.environ["STRIPE_KEY"])
registry.register_class(stripe_client, prefix="stripe.")
```

Same skip-with-reason behavior as `register_module`. Properties, private
methods, and non-callable attributes are never considered (not treated as
validation failures — they're just not method candidates).

Namespaced capabilities (anything registered with a `prefix=`) are callable
inside the sandbox exactly as the prefix suggests — `stripe.charge_card(500)`
— and their stub signatures render in that same call-style form, since `def
stripe.charge_card(...): ...` isn't valid Python syntax.

## 4. Declarative specs (JSON/YAML) — no Python wrapper at all

For cases where writing a Python function isn't worth it — a single REST
endpoint, or a function that already exists somewhere importable by dotted
path — use [`register_spec`](reference/capability_registry.md#register_spec)
or [`load_specs`](reference/capability_registry.md#load_specs)
with a [`CapabilitySpec`](reference/capability_spec.md):

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

- **`python`** — a dotted path to an existing callable. Registered exactly
  like any other capability (same validation).
- **`http`** — a templated HTTP call. `{placeholders}` in `url_template` are
  filled from named parameters; any parameter not consumed by the template
  goes into the query string (GET/DELETE) or JSON body (POST/PUT/PATCH). A
  real, annotated function signature is synthesized from the `parameters`
  block, so it produces a proper stub (`def get_weather(city: str) -> dict:
  ...`) instead of a bare `**kwargs`.

`load_specs()` accepts a single spec object or a list (optionally under a
top-level `capabilities` key), in `.json`, `.yaml`, or `.yml` files.

## 5. Registry-free: `@capability` marker + `collect()`

For capabilities defined across many files/modules with no
`CapabilityRegistry` in scope at definition time, mark a function with
`@capability` and gather every marked function later in one call with
[`registry.collect(*modules)`](reference/capability_registry.md#collect):

```python
# myapp/orders.py
from smile.capabilities import capability

@capability
def get_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return db.orders.find_one(order_id)

@capability(description="Refund an order in full.")
def refund_order(order_id: str) -> dict:
    """This docstring is ignored -- explicit description above wins."""
    ...
```

```python
# elsewhere, with no import of orders.py's individual functions
import myapp.orders
registry = CapabilityRegistry()
report = registry.collect(myapp.orders)
```

`@capability` alone never registers anything — it only attaches metadata.
Unmarked functions in a collected module are ignored, even if they're
otherwise well-typed and documented (use `register_module` for "everything
public" instead). `collect()` returns the same `RegistrationReport` as
`register_module`/`register_class`, with the same `prefix=`/`include=`/
`exclude=`/`strict=` options.

Marker metadata also works as a fallback if you register the function
directly instead of via `collect()`: `@registry.register` on an
already-`@capability`-marked function uses the marker's `description`/
`example` below explicit kwargs and above docstring inference.

## Per-parameter descriptions

Any parameter typed with `Annotated[SomeType, "a description"]` gets an
extra trailing comment line in the generated stub, so the agent sees
per-argument documentation instead of just a whole-function description:

```python
from typing import Annotated

@registry.register
def charge_card(
    amount_cents: Annotated[int, "amount to charge, in the smallest currency unit"],
    currency: Annotated[str, "ISO 4217 currency code, e.g. \"usd\""] = "usd",
) -> dict:
    """Charge a card for the given amount."""
    ...
```

renders as:

```text
def charge_card(amount_cents: int, currency: str = 'usd') -> dict: ...
#   amount_cents: amount to charge, in the smallest currency unit
#   currency: ISO 4217 currency code, e.g. "usd"
```

Capabilities with no `Annotated` parameters render exactly as before — this
is purely additive.

## Design notes worth knowing if you extend this

- **Everything converges on one [`Capability`](reference/capability.md)
  object.** Whichever path you use, the sandbox and the stub/documentation
  generator don't know or care where a capability came from — `source` is
  tracked only for error messages and the catalog.
- **Anything injected into the sandbox namespace must be picklable,
  including anything it closes over.** `smile.sandbox` runs scripts in a
  `multiprocessing.spawn` subprocess, which pickles every capability
  callable to hand it across the process boundary. A closure over local
  variables isn't picklable — this is what the registration-time
  picklability check (above) exists to catch early. `_HttpCapability` and
  the async-capability wrapper are both module-level classes with
  plain-data `__init__` state for exactly this reason, not closures.
- **Namespace prefixes are real attribute access, not string keys.** A
  capability registered as `"stripe.charge_card"` is exposed to the sandbox
  as a namespace object at global name `stripe` with `charge_card` as a
  bound attribute — so `stripe.charge_card(...)` works as ordinary Python,
  not as some string-keyed dispatch hack.
- **One function/method per file.** `smile/` is restructured so every
  function and method — including private helpers and dataclass methods —
  lives in its own module. Classes declare only fields; methods are
  standalone functions taking `self` explicitly, attached via
  `ClassName.method = imported_function` after the class body. Package
  `__init__.py` files reassemble the pre-restructure public surface, so
  imports like `from smile.capabilities import CapabilityRegistry` are
  unaffected.

## Agent-saved scripts

Operator capabilities are curated at startup. An agent can also **publish
a function from inside `execute_script`** and call it later as
`scripts.<name>(...)`:

```python
def doubled(n: int) -> int:
    """Double a number."""
    return n * 2

__save__ = True
__result__ = doubled(3)
```

That is not a sixth registration path on `CapabilityRegistry`. Saved
scripts live in a separate `ScriptStore`, stay under the reserved
`scripts` prefix so they cannot shadow `grep` / `get_customer`, and
appear in `list_capabilities()` with `source="saved_script"`. They must
meet the same type-hint and docstring bar as a capability — the catalog
stub is generated from the AST, not from executing the agent’s code in
the parent process.

`__save__ = "name"` publishes under a different name. `__unpublish__ =
"name"` removes one. Overwriting a name replaces the function. The store
refuses a new name once `SMILE_MAX_SAVED_SCRIPTS` is reached (default 32)
rather than evicting — a later script still calling `scripts.foo()` would
otherwise become an `AttributeError` with no marker.

By default the library dies with the MCP process. Set `SMILE_SCRIPTS_DIR`
to persist each function as `{name}.json` and reload on the next boot.
