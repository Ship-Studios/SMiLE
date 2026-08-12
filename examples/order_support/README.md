# Example: order support agent

A standalone, runnable app showing how to wire SMiLE onto code that
wasn't written with SMiLE in mind, using every registration path
together:

| File | Registration path | What it shows |
|---|---|---|
| `orders.py` | `registry.register_module(orders)` | Bulk-wrap a plain existing module. `_internal_audit_dump` is skipped automatically (leading underscore). |
| `payment_client.py` | `registry.register_class(client, prefix="payments.")` | Wrap an already-constructed client instance (API key and all) with zero changes to the client itself. |
| `notifications.py` — `send_refund_email` | `registry.register(send_refund_email)` | A fresh `async def` capability, registered directly — SMiLE runs it to completion transparently, no `asyncio` awareness needed in the agent's script. |
| `notifications.py` — `log_support_action` | `@capability` + `registry.collect(notifications)` | Registry-free marking: `notifications.py` never imports or references a `CapabilityRegistry` at all. |
| `app.py` | — | Assembles all four into one `CapabilityRegistry`. |
| `run.py` | — | The walkthrough: prints the capability catalog an agent would see, then runs one multi-step agent-authored script through `run_script()` and prints the result. |

## Run it

```bash
uv run python3 -m examples.order_support.run
```

## What it demonstrates

The script in `run.py` resolves "refund every paid order over $1000 for
this customer, email them, and log it" in a **single** sandboxed round
trip — one `run_script()` call, regardless of how many orders match.
Without SMiLE, the same task is 1 call to list orders plus 3 more calls
(refund, email, log) *per matching order*, each paying a full context
round trip. With SMiLE, only the final summary dict crosses back out of
the sandbox; the agent never sees the intermediate order records.

This is also a template for wiring a real registry outside the MCP
server entirely — `run.py` calls `smile.sandbox.run_script()` directly,
the same function `smile/server/execute_script.py` calls inside the MCP
tool. Use this shape if you want SMiLE's script-execution model in your
own app without going through MCP at all.
