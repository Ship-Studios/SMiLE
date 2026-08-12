# SMiLE

**SMiLE (Secure Message in Lambda Expressions)** is a prototype MCP server
that lets an LLM agent write a Python **script** against a curated set of
your application's functions, run it in a sandbox, and get back only the
final result — instead of one MCP tool-call round trip per action.

```text
Agent: "Email all enterprise customers their total paid amount"
  -> writes ONE Python script that loops over customers, sums orders,
     sends emails
  -> SMiLE runs it sandboxed, returns only the final summary
  -> Agent never sees the intermediate order records or email bodies
```

It exposes exactly two MCP tools, `list_capabilities` and `execute_script`,
backed by two independent pieces you can also use as a plain Python
library:

- **[`smile.capabilities`](reference/capability_registry.md)** — the
  `CapabilityRegistry` that turns your application's functions into
  agent-callable capabilities.
- **[`smile.sandbox`](reference/run_script.md)** — `run_script()`, the
  isolated-subprocess executor that runs agent-authored code against a
  capability namespace.

Neither depends on the MCP server layer — `from smile.capabilities import
CapabilityRegistry` and `from smile.sandbox import run_script` work with no
MCP involvement at all.

!!! warning "Prototype-grade isolation"
    The sandbox uses a subprocess boundary and a restricted builtins set.
    That stops accidental misuse and casual escapes — it is **not**
    adversarially secure against a determined attacker with code execution.
    See [`smile.sandbox`](reference/run_script.md) for what a production
    version would need instead.

## Where to start

- **[Defining capabilities](capabilities.md)** — the four ways to register
  a capability, with the picklability, async, and per-parameter-description
  details that matter once you go past the basic case.
- **API Reference** (sidebar) — generated from docstrings, one page per
  public class/function.

## Quickstart

```bash
uv sync --extra dev   # dev extra pulls in google-genai + pyyaml, for the e2e test
uv run python3 tests/test_capabilities.py   # unit tests for all registration paths
```

```python
from smile.capabilities import CapabilityRegistry
from smile.sandbox import run_script

registry = CapabilityRegistry()


@registry.register
def get_customer(customer_id: str) -> dict:
    """Look up a customer record by ID."""
    return {"id": customer_id, "name": "Ada Lovelace"}


result = run_script(
    "__result__ = get_customer('cust_1')",
    registry.namespace(),
)
print(result.return_value)  # {'id': 'cust_1', 'name': 'Ada Lovelace'}
```
