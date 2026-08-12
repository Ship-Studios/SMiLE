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

## Quickstart

```bash
uv sync --extra dev   # dev extra pulls in google-genai + pyyaml, for the e2e test
uv run python3 tests/test_capabilities.py   # unit tests for all registration paths
uv run python3 -m examples.order_support.run   # full end-to-end example app, no API key needed
GEMINI_API_KEY=... uv run python3 tests/e2e_gemini.py   # live agent test
```

```python
from smile.capabilities import CapabilityRegistry
from smile.sandbox import run_script

registry = CapabilityRegistry()


@registry.register
def get_customer(customer_id: str) -> dict:
    """Look up a customer record by ID."""
    return db.customers.find_one(customer_id)


result = run_script("__result__ = get_customer('cust_1')", registry.namespace())
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

There are five ways to register one, depending on how much of your app
already exists:

1. **`@registry.register`** -- decorate a function you're writing fresh;
   description/example are inferred from its docstring.
2. **`registry.register_module(module)`** -- bulk-wrap every public,
   well-typed function in an existing module.
3. **`registry.register_class(instance)`** -- bulk-wrap every public
   method on an already-constructed client/SDK instance.
4. **`registry.register_spec(spec)` / `load_specs(path)`** -- declarative
   JSON/YAML capability definitions, no Python wrapper required.
5. **`@capability` + `registry.collect(*modules)`** -- registry-free
   marker for capabilities defined across many files, gathered centrally
   later.

`async def` functions register directly via any of the above. Registration
validates eagerly: missing type hints, a missing description, and
unpicklable callables (closures, lambdas) all raise immediately, with a
message telling you how to fix it, instead of failing later inside the
sandbox.

**Full guide, with examples for every path:** see the
[Defining capabilities](docs/capabilities.md) docs page, or build the docs
site locally:

```bash
uv sync --extra docs
uv run mkdocs serve   # http://127.0.0.1:8000, live-reloading
```

The docs site includes a generated **API Reference** (via mkdocstrings) for
every public class and function in `smile.capabilities` and
`smile.sandbox`, built straight from their docstrings.
