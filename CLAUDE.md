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

# Build/serve the API reference docs site (mkdocs + mkdocstrings, autodoc from docstrings)
uv sync --extra docs
uv run mkdocs serve          # live-reloading dev server at http://127.0.0.1:8000
uv run mkdocs build --strict # CI-style build; fails on broken links/cross-refs
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
   the structured catalog) and `execute_script(code, intent)` (runs `code` via `run_script` against
   `registry.namespace()`; `intent` is a required plain-English sentence describing the script's goal,
   logged alongside the capabilities the script actually called — see `smile/server/log_intent.py`).
   `execute_script`'s tool description is itself the API reference the agent
   reads before writing code — this is deliberate: MCP's native discovery (`tools/list`) is built for
   "one tool, one call," so the capability catalog is pushed into the tool description / a companion
   tool rather than expressed as separate MCP tools per capability. That description is **generated**
   from the served registry by `build_execute_script_description()` and passed to `@mcp.tool(description=...)`
   — not written as `execute_script`'s docstring. Since the served registry is configurable
   (`SMILE_CAPABILITIES`/`SMILE_CAPABILITY_SPEC`), a hardcoded docstring could only ever describe the
   bundled demo app, and would hand every other consumer a worked example calling functions that don't
   exist for them.

   A script that defines exactly one top-level typed function and assigns `__save__ = True` (or
   `__save__ = "name"`) is published as `scripts.<name>` for later `execute_script` calls in this
   process — and across restarts if `SMILE_SCRIPTS_DIR` is set. `__unpublish__ = "name"` removes one.
   Saved scripts are **not** operator capabilities: they live in `ScriptStore` (`smile/server/script_store.py`),
   are hydrated inside the sandbox child from picklable `SavedScriptRecord`s (closures built in the parent
   would fail `spawn`'s pickle), and show up in `list_capabilities()` with `source="saved_script"`.
   `extract_called_capabilities` walks saved bodies transitively so the intent log names the inner
   operator capabilities, not just `scripts.foo`. The reserved `scripts` namespace is refused if the
   operator registry already owns it.

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

### Output budgets: the return path is context-bounded

SMiLE's premise is "one script, one result" — but the *result* still lands verbatim in the agent's
context, so an unbounded result is a context-exhaustion bug. Measured on realistic CRM rows, 10k rows is
~1.3M characters (~334k tokens), which overflows any current window outright; a stray `print` in a loop
cost 47k tokens. Two layers address this:

1. **Truncation** (`smile/sandbox/truncate_value.py`, `truncate_stream.py`). `run_script` caps
   `return_value` at `result_budget` characters and each stream at `stream_budget` (both defaults in
   `constants.py`; pass `0` to disable, which library callers not feeding an LLM should do). Defaults
   are sized against a **100k-token context window** — the conservative planning assumption, not the
   largest window available, since a budget tuned to a big window misbehaves silently on a smaller one.
   Consumers override them per-deployment via env vars in `.mcp.json` (`SMILE_RESULT_BUDGET`,
   `SMILE_STREAM_BUDGET`, `SMILE_TIMEOUT_S`, `SMILE_MAX_STORED_RESULTS`, `SMILE_MAX_SAVED_SCRIPTS`,
   `SMILE_SCRIPTS_DIR`) — resolved once at import time
   by `load_settings()` into a frozen `ServerSettings` (`settings_instance.py`), the same shape
   `load_registry()`/`registry_instance.py` already use. Malformed values raise at **startup** rather
   than falling back to a default: a silently ignored budget produces results truncated at a size the
   consumer never chose, with nothing anywhere saying so. `.mcp.json.example` is the shipped reference
   and is covered by a test asserting it parses and boots.
   Because `execute_script` is called repeatedly in a loop, the number that matters is calls-per-window,
   not one call: worst case is ~5,000 tokens (~5% of 100k, so ~20 calls before real pressure). If you
   change these, re-derive them the same way rather than picking round numbers. An
   oversized result is replaced by a **note**, not a silent slice: original shape, item counts, an
   explicit `truncated: True`, and guidance to aggregate. This is load-bearing — an agent handed 20 of
   10,000 rows with no marker will report "20" to the user, which is worse than an error. Streams keep
   head *and* tail, because the interesting output (a failure, a summary) is usually at the end.
2. **`ResourceLink`** (`smile/server/full_result_resource.py`, `result_store.py`). The full value is
   kept server-side in a small bounded `ResultStore` and exposed at `smile://results/{result_id}`, so
   the agent can fetch the rows deliberately instead of being force-fed them or losing them.

**Ordering constraint:** truncation happens in the **parent** (`build_script_result.py`), not the child.
The child must send the complete value across the queue so the parent can store it for the resource
link — truncating in `build_payload` would destroy the data before anything could stash it. This is safe
only because the parent now drains the queue while the child writes; see the constraint below.

`ResultStore.get` returns a `RESULT_MISSING` sentinel rather than `None` for unknown/evicted ids, since
`None` is a perfectly valid script result and conflating them would report an evicted result as a
successful null.

### Non-obvious constraint: never `join()` the sandbox child before draining its queue

`multiprocessing.Queue` is backed by a pipe with a bounded OS buffer (~64KB). `Queue.put()` hands the
payload to a **background feeder thread** in the child and returns immediately; that thread blocks once
the buffer fills, and the child cannot exit until the parent reads. Two consequences, both of which were
live bugs:

- **`proc.join(timeout)` before reading the queue deadlocks** on any script whose payload exceeds the
  buffer — the child waits for the parent to read, the parent waits for the child to exit. The symptom is
  a *spurious timeout* that discards a correctly-computed result. `await_payload()` (`smile/sandbox/`)
  polls the queue in short slices instead, which keeps the pipe draining. Join only *after* the payload
  is in hand.
- **`try`/`except` around `put()` cannot catch a `PicklingError`**, because the pickling happens on that
  feeder thread, not at the call site. An unpicklable `__result__` silently dropped the whole payload.
  `build_payload()` pickles the value up front and substitutes its `repr` on failure, so the fallback is
  actually reachable.

A crashed child (segfault, OOM, `os._exit`) does **not** raise `EOFError` in the parent's reader — the
queue just stays empty — so "timed out" and "died without reporting" are only distinguishable by checking
`proc.is_alive()` between polls. Don't collapse those two branches.

### Namespace prefixes are real attribute access, not string keys

A capability registered with `prefix="stripe."` (e.g. `"stripe.charge_card"`) is exposed inside the
sandbox as a `_Namespace` object at global name `stripe`, with `charge_card` as a bound attribute — so
`stripe.charge_card(...)` is ordinary Python attribute access, not a string-keyed dispatch hack. Because
of this, `Capability.stub_signature()` renders namespaced capabilities in call-style form
(`stripe.charge_card(amount_cents: int) -> dict`) rather than as a `def` statement — `def
stripe.charge_card(...): ...` isn't valid Python syntax.

Because the flattened namespace binds `stripe` to a `_Namespace` object, a *flat* capability named
`stripe` and a prefixed one named `stripe.charge_card` cannot coexist — one silently shadows the other,
and `registry_add`'s exact-key duplicate check never sees it (they're different dict keys). That's what
`validate_no_namespace_shadowing()` catches at registration time. Ordinary siblings sharing a prefix
(`crm.a` + `crm.b`) are fine and must keep working — only the bare namespace head collides.

### `smile/repo_tools/`

The default capability set served by `smile/server/` when no `SMILE_CAPABILITIES`/`SMILE_CAPABILITY_SPEC`
is configured — capabilities for working inside the SMiLE repository itself rather than a demo app:

- **Introspection**: `list_files(pattern)`, `read_file(path, start_line, end_line)`, `grep(pattern,
  path_glob)` — `grep` walks the filesystem directly (not `git grep`) so untracked/unstaged files are
  searched too, which matters for an agent actively writing new files.
- **Git**: `git_status()`, `git_diff(staged)`, `git_log(max_count)`, `git_show(ref)`.
- **GitHub** (via the `gh` CLI): `list_prs(state)`, `get_pr(number)`, `list_issues(state)` —
  `list_prs` / `list_issues` return `[]` only when the `gh` binary is not installed; any other
  non-zero `gh` exit (no remote, not authenticated, bad `--state`) raises `RuntimeError`.
  `get_pr` never returns `[]` — missing `gh`, a missing PR (`NotFoundError`), and other
  operational failures all raise. A consumer without `gh` can still use every other
  capability; a script that only calls the list helpers sees an empty list rather than
  an exception.
- **Dev loop**: `run_tests()`, running `tests/test_capabilities.py` in a subprocess with
  its own timeout (capped at `SMILE_TIMEOUT_S`, default 30s — sized to fit the suite)
  and output truncation (reusing `smile/sandbox/truncate_stream.py`).

Every path-accepting capability resolves through `resolve_repo_path.py` (or
`validate_repo_glob.py` / `walk_repo_glob.py` for glob walkers), which confines it
to the repository root (`repo_root.py`) and raises `PathEscapesRepoError` on anything
that would escape (symlinks included, since `Path.resolve()` follows them before the
containment check). Glob walkers prune `.git` / `__pycache__` / `.venv` / `node_modules`
*before* descending, using in-repo path parts only (so a checkout living under a
directory of those names is not treated as empty), and do not walk symlink directories
that resolve outside the repo. An explicitly named glob prefix that resolves outside
raises rather than walking the target and filtering results. These functions execute
inside the sandbox child — they are pickled into the capability namespace — with the
host process's filesystem permissions, unlike the rest of the sandboxed script, which
has none.

Every git/gh/test capability shells out through the shared `run_subprocess.py`
helper with a fixed argv list (never `shell=True`, never a caller-built command
string). User-supplied tokens that could be parsed as options (e.g. `git show`
refs) are rejected if they start with `-` and passed after
`--end-of-options` so they cannot become git switches. `--` is the
path-separator, not an option terminator, for `git show`. Subprocesses start in their own
process group and are killed as a group on timeout or when the sandbox worker
is terminated; their timeout is capped at `SMILE_TIMEOUT_S` so they cannot
outlive the script budget.

Every capability here uses bare `@registry.register` with no explicit `description=`/`example=` —
consistent with the project's own intended common case (description/example inferred from the
docstring).

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
