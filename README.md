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

## Large results don't blow up the context window

A script's result goes straight into the agent's context, so SMiLE caps how
much can come back. Returning 10,000 rows measures ~334k tokens — enough to
overflow any current context window on its own. Instead:

- **Results over the budget are truncated into a summary** naming the
  original shape, how many items were omitted, and a sample. The note is
  explicitly flagged, so an agent can't mistake a 20-row preview for a
  complete answer.
- **The full result stays fetchable.** It's stored server-side and exposed
  as an MCP resource at `smile://results/{id}`, returned alongside the
  summary as `full_result_uri` — so the data isn't lost, just not forced
  into context.
- **stdout/stderr are capped too**, keeping head and tail so a final
  summary or traceback survives.

In practice a 10,000-row result costs ~580 tokens inline instead of
~334,000, and the agent is told how to get the rest if it genuinely needs
it.

Defaults are sized conservatively against a **100k-token context window**,
on the assumption that `execute_script` gets called repeatedly in a loop —
so what matters is how many calls fit, not whether one does:

| | Tokens | Share of a 100k window |
|---|---|---|
| Typical call (aggregated result) | ~100–600 | <1% |
| Worst case (capped result + both streams) | ~5,000 | ~5% |

That leaves room for roughly 20 worst-case calls before context pressure
becomes real. The result cap is still generous in absolute terms — around
100 rows of typical CRM data passes through untouched, so shortlists and
summaries are never clipped; only accidental data dumps are.

Budgets are configurable per call via `run_script(..., result_budget=,
stream_budget=)`; pass `0` to disable them when calling SMiLE as a library
rather than behind an LLM. Running as an MCP server, set them in
`.mcp.json` — see Configuration below.

## Configuration

Everything a consumer needs to tune is an environment variable, set in your
MCP client's `.mcp.json`. Copy [`.mcp.json.example`](.mcp.json.example) as
a starting point — it boots as-is against the bundled repo_tools capability set.

```json
{
  "mcpServers": {
    "smile": {
      "command": "uv",
      "args": ["run", "smile-mcp"],
      "env": {
        "SMILE_CAPABILITIES": "myapp.integrations.registry:registry",
        "SMILE_RESULT_BUDGET": "12000",
        "SMILE_STREAM_BUDGET": "4000",
        "SMILE_TIMEOUT_S": "30",
        "SMILE_MAX_STORED_RESULTS": "32",
        "SMILE_MAX_SAVED_SCRIPTS": "32",
        "SMILE_INTENT_LOG": "smile_intent.log"
      }
    }
  }
}
```

| Variable | Default | What it does |
|---|---|---|
| `SMILE_CAPABILITIES` | — | `module.path:attr` reference to your own `CapabilityRegistry`. |
| `SMILE_CAPABILITY_SPEC` | — | Path to a JSON/YAML capability spec file instead. |
| `SMILE_RESULT_BUDGET` | `12000` | Max characters of `return_value` returned inline; `0` disables. |
| `SMILE_STREAM_BUDGET` | `4000` | Max characters of stdout and of stderr each; `0` disables. |
| `SMILE_TIMEOUT_S` | `30` | Seconds a script may run before termination. |
| `SMILE_MAX_STORED_RESULTS` | `32` | Full results retained for `smile://results/{id}` fetches. |
| `SMILE_MAX_SAVED_SCRIPTS` | `32` | Agent-saved functions (`__save__`) the session library may hold. |
| `SMILE_SCRIPTS_DIR` | — | Directory of `{name}.json` files so saved scripts survive a restart. Unset = memory only. |
| `SMILE_INTENT_LOG` | `smile_intent.log` | File each `execute_script` call's intent and called capabilities are appended to. |

Set `SMILE_CAPABILITIES` **or** `SMILE_CAPABILITY_SPEC`, not both; with
neither, the bundled repo_tools capability set is served. Budgets are in characters
(~4 chars/token) — raise them if your model has a window larger than the
100k the defaults assume.

Values are validated at startup, so a typo (`SMILE_RESULT_BUDGET=100k`)
stops the server with a message naming the variable, rather than silently
falling back to a default you didn't choose.

The better fix is usually to aggregate in the script — `__result__ =
len(orders)` rather than `__result__ = orders` — which is what
`execute_script`'s tool description now tells the agent to do.

## Reusable scripts

An agent can publish a typed function from inside `execute_script` and
call it from later scripts as `scripts.<name>(...)` — no extra MCP tool,
and no `import` (the sandbox has none).

```python
def doubled(n: int) -> int:
    """Double a number."""
    return n * 2

__save__ = True
__result__ = doubled(3)
```

Later:

```python
__result__ = scripts.doubled(4)
```

`__save__ = "name"` publishes under a different name; `__unpublish__ =
"name"` removes one. The function needs type hints and a docstring — the
same bar as an operator-registered capability. `list_capabilities()` is
the live catalog (`source="saved_script"`); `execute_script`'s tool
description is built at startup and will not list functions saved later.

By default the library is process-memory only. Set `SMILE_SCRIPTS_DIR` to
keep `{name}.json` files across restarts.

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
