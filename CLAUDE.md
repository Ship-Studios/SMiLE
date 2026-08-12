# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SMiLE (Secure Message in Lambda Expressions) is a prototype MCP server that lets an LLM agent write a
Python **script** against a curated set of application functions ("capabilities"), run it in a sandbox,
and get back only the final result — instead of one MCP tool-call round trip per action. It exposes
exactly two MCP tools: `list_capabilities` and `execute_script`.

## Commands

```bash
# Install deps (dev extra pulls in google-genai + pyyaml, needed for tests)
uv sync --extra dev

# Run the capability-registration unit tests (plain assert-based, no pytest)
uv run python3 tests/test_capabilities.py

# Run the live end-to-end test — makes real calls to the Gemini API
GEMINI_API_KEY=... uv run python3 tests/e2e_gemini.py

# Run the MCP server directly (stdio transport)
uv run python3 -m smile.server

# Launch the MCP Inspector for manual/interactive tool testing
uv run mcp dev smile/server/__init__.py

# Quick manual check of the tool schemas / server health
uv run python3 -c "
from smile.server import mcp
import asyncio
asyncio.run(mcp.list_tools())
"
```

There is no test framework dependency (no pytest) — `tests/test_capabilities.py` is a self-contained
runner: each `test_*` function in the module is executed in turn, failures are collected into a list,
and the script exits non-zero if any failed. To run a single check, either comment out the others in
`__main__` or import and call the specific `test_*` function directly via `python3 -c`.

`tests/e2e_gemini.py` costs real API quota — it drives `gemini-2.5-flash-lite` as an actual tool-calling
agent against a live server subprocess, not a scripted stand-in. Don't run it reflexively; confirm with
the user first the way the transcript that built this repo did.

## Architecture

### The core mechanism: capabilities → sandbox → MCP

Three layers, each independent enough to reason about alone:

1. **`smile/capabilities/`** — the `CapabilityRegistry`. A "capability" is a plain Python function
   that sandboxed scripts are allowed to call. Every capability, regardless of how it was registered,
   converges on one `Capability` dataclass — the sandbox and the stub-generation code never need to know
   which registration path produced it.

2. **`smile/sandbox/`** — `run_script(code, capability_namespace)` executes agent-written Python in a
   **separate subprocess** (`multiprocessing`, `spawn` context) with a restricted `__builtins__` set (no
   `import`, `open`, `exec`, `eval`) and only the capability namespace injected as globals. A script
   returns its result by assigning to a special `__result__` variable — this is the sandbox's equivalent
   of a return statement for the whole script. **This isolation is explicitly prototype-grade, not
   adversarially secure** — see `smile/sandbox/__init__.py`'s docstring for what a production version
   would need instead (Pyodide/WASM, gVisor, Firecracker).

3. **`smile/server/`** — the MCP server (`mcp.server.mcpserver.MCPServer`, not the older `FastMCP` —
   the installed `mcp` package renamed it in this major version). Exposes `list_capabilities()` (returns
   the structured catalog) and `execute_script(code)` (runs it via `run_script` against
   `registry.namespace()`). `execute_script`'s tool description is itself the API reference the agent
   reads before writing code — this is deliberate: MCP's native discovery (`tools/list`) is built for
   "one tool, one call," so the capability catalog is pushed into the tool description / a companion
   tool rather than expressed as separate MCP tools per capability.

### Four ways to register a capability (increasing leverage)

All four live in `smile/capabilities/` and all funnel through `CapabilityRegistry._add()`
(`registry_add.py`), which does registration-time validation (every parameter and the return value need
type hints; a description — explicit or inferred — is required) and raises `CapabilityDefinitionError`
immediately rather than producing a bad stub the agent discovers at call time.

1. `@registry.register` — decorate a function. Description/example are inferred from the docstring
   (summary paragraph → description; `>>> ` doctest line or `Example:` section → example; synthesized
   from the signature as a last resort) unless passed explicitly.
2. `registry.register_module(module, prefix=...)` — bulk-register every public, well-typed, top-level
   function in an existing module.
3. `registry.register_class(instance, prefix=...)` — bulk-register every public method on an
   already-constructed client/SDK instance, bound to that instance. This is the "wrap an existing
   integration with no rewrite" path.
4. `registry.register_spec(spec)` / `registry.load_specs(path)` — declarative JSON/YAML capability
   definitions with no Python wrapper required. Two `target.kind` values: `"python"` (dotted path to an
   existing callable) and `"http"` (templated URL + params, synthesizes a real annotated signature so it
   produces a proper stub instead of `**kwargs`).

Bulk registration (`register_module`/`register_class`) **skips rather than aborts** on functions/methods
that fail validation by default — wrapping existing code routinely hits things that were never meant to
be capabilities. Both return a `RegistrationReport` (`.registered`, `.skipped` with reasons,
`.summary()`); pass `strict=True` to raise on the first failure instead.

### Non-obvious constraint: everything injected into the sandbox must be picklable

`smile/sandbox/` uses `multiprocessing` with the `spawn` context, which pickles the entire capability
namespace to hand it across the process boundary. This ruled out the natural way to implement
HTTP-backed capabilities (a closure over `url_template`/`headers`/etc. built inside a factory function) —
closures over local variables aren't picklable (`AttributeError: Can't get local object
'...'.<locals>._call'`). The fix, `_HttpCapability` (`smile/capabilities/http_capability.py`), is a
module-level class with plain-data `__init__` state instead. If you add a new capability-construction
path that builds wrapper callables dynamically, this constraint applies again — and remember it also
covers the *module-level function targets* used to pickle `multiprocessing.Process(target=...)` itself
(see `smile/sandbox/worker.py`): the target must be reachable by a stable dotted import path, not a
closure or a method bound to a locally-constructed object.

### Namespace prefixes are real attribute access, not string keys

A capability registered with `prefix="stripe."` (e.g. `"stripe.charge_card"`) is exposed inside the
sandbox as a `_Namespace` object at global name `stripe`, with `charge_card` as a bound attribute — so
`stripe.charge_card(...)` is ordinary Python attribute access, not a string-keyed dispatch hack. Because
of this, `Capability.stub_signature()` renders namespaced capabilities in call-style form
(`stripe.charge_card(amount_cents: int) -> dict`) rather than as a `def` statement — `def
stripe.charge_card(...): ...` isn't valid Python syntax.

### `smile/example_app/`

A fake in-memory CRM (customers/orders/email, all in module-level dicts in `data.py`, reset on server
restart) used as the live capability set for `smile/server/` and as the target of `tests/e2e_gemini.py`.
Every capability here uses bare `@registry.register` with no explicit `description=`/`example=` — it's
meant to double as a working example of what capability authors should write.

## STRICT GUIDELINE: one method per file

**Every function and method — including private helpers, dataclass methods, and module-level functions —
lives in its own file.** No file may define more than one `def` (bare dataclass field declarations don't
count — a `@dataclass` with only fields and no methods is exempt). This is enforced across the entire
`smile/` package; a file audit finding more than one `def` per file (excluding `__init__.py`/`__main__.py`
reassembly/entry-point files, which contain only imports and wiring) is a rule violation to fix.

The pattern used throughout, and the one to follow for new code:

- **Standalone functions** just live in their own module (e.g. `smile/capabilities/infer_description.py`
  holds only `infer_description`).
- **Dataclass/class methods** are defined as plain functions taking `self` as an explicit first
  parameter, in their own file (e.g. `smile/capabilities/capability_stub_signature.py` defines
  `capability_stub_signature(self, ...)`), then attached to the class after its body via
  `ClassName.method_name = imported_function` (see the bottom of `smile/capabilities/capability.py` or
  `smile/capabilities/capability_registry.py`). The class body itself declares only dataclass fields.
  Self-referencing type hints on these standalone method-functions use a `if typing.TYPE_CHECKING: from
  ... import ClassName` guard plus a string annotation (`self: "ClassName"`) to avoid a circular import
  between the class module and its method modules.
- **Nested closures inside a method** (e.g. a decorator's inner wrapper, a generator used only by one
  caller) are extracted the same way — as their own top-level function in their own file, taking
  whatever the closure used to capture as explicit parameters instead. Where a closure exists purely to
  satisfy a decorator's dual call-signature (`@register` vs `@register(...)`), prefer `functools.partial`
  over writing a second nested `def` (see `smile/capabilities/registry_register.py`).
- **Classes with no methods** (plain dataclass field blocks, plain `Exception` subclasses with only a
  docstring) don't need splitting — they define zero `def`s, so they're already compliant on their own.
- **Package `__init__.py` files reassemble the public surface**: they import every function/method module
  (for registration side effects like `@registry.register`, or simply to re-export), so callers outside
  the package don't need to know about the one-file-per-function layout underneath (e.g. `from
  smile.capabilities import CapabilityRegistry` still works exactly as when it was a single file).
- **`multiprocessing.Process(target=...)` picklability still applies** even after this split — a method
  now defined in its own file and attached post-hoc via `ClassName.method = func` is still picklable as
  long as `ClassName` itself is importable from its module path (pickle only needs the class, not the
  method-attachment mechanism). See `smile/sandbox/worker.py` for the one function that's actually
  handed to `multiprocessing.Process` as a target and must stay a plain top-level function for that
  reason specifically.

## MCP SDK version note

The installed `mcp` package is a newer major version than a lot of published examples assume. Notable
API differences hit while building this: the high-level server class is `mcp.server.mcpserver.MCPServer`
(not `mcp.server.fastmcp.FastMCP`), and `Tool.input_schema` is snake_case (not `Tool.inputSchema`). If
something from an MCP example doesn't import, check `smile/server/mcp_instance.py` and
`smile/server/__init__.py` for the actual working shape before assuming the example is right.
